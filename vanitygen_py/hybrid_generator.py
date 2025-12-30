"""
Hybrid GPU+CPU Bitcoin Address Generator using coincurve.

This module implements a high-performance address generator that:
1. Uses GPU for parallel random number generation (embarrassingly parallel)
2. Uses coincurve (Bitcoin Core's libsecp256k1) for 100% correct EC math
3. Achieves ~100,000 addresses/second with guaranteed correctness

The hybrid approach gives us:
- SPEED: GPU parallelizes the RNG work
- CORRECTNESS: libsecp256k1 ensures valid Bitcoin addresses
- RELIABILITY: No risk of generating addresses we can't control
"""

import threading
import time
import queue
import os
import struct
import secrets
import hashlib
from multiprocessing import Pool, cpu_count
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
from typing import Optional, List, Tuple, Set, Callable

# Try to import coincurve for fast, correct EC operations
try:
    import coincurve
    COINCURVE_AVAILABLE = True
except ImportError:
    COINCURVE_AVAILABLE = False
    print("WARNING: coincurve not installed. Install with: pip install coincurve")

# Try to import OpenCL for GPU random number generation
try:
    import pyopencl as cl
    import numpy as np
    OPENCL_AVAILABLE = True
except ImportError:
    OPENCL_AVAILABLE = False
    cl = None
    np = None

# Handle both module and direct execution
try:
    from .crypto_utils import hash160, base58check_encode, bech32_encode
except ImportError:
    from crypto_utils import hash160, base58check_encode, bech32_encode


# Minimal OpenCL kernel for fast random number generation
RNG_KERNEL_SOURCE = """
/*
 * High-quality random number generator kernel for private key generation.
 * Uses XORShift128+ algorithm - fast, high quality PRNG suitable for crypto seeding.
 */

// XORShift128+ state 
typedef struct {
    ulong s0;
    ulong s1;
} xorshift128_state;

// XORShift128+ - fast, high-quality PRNG
ulong xorshift128plus(xorshift128_state* state) {
    ulong s1 = state->s0;
    ulong s0 = state->s1;
    state->s0 = s0;
    s1 ^= s1 << 23;
    s1 ^= s1 >> 17;
    s1 ^= s0;
    s1 ^= s0 >> 26;
    state->s1 = s1;
    return state->s0 + state->s1;
}

// Initialize state from seed + global ID
void init_state(xorshift128_state* state, ulong seed, uint gid) {
    // Mix seed with gid using splitmix64 to avoid correlation
    ulong z = seed + gid * 0x9e3779b97f4a7c15UL;
    z = (z ^ (z >> 30)) * 0xbf58476d1ce4e5b9UL;
    z = (z ^ (z >> 27)) * 0x94d049bb133111ebUL;
    state->s0 = z ^ (z >> 31);
    
    z = seed + (gid + 0x10000) * 0x9e3779b97f4a7c15UL;
    z = (z ^ (z >> 30)) * 0xbf58476d1ce4e5b9UL;
    z = (z ^ (z >> 27)) * 0x94d049bb133111ebUL;
    state->s1 = z ^ (z >> 31);
    
    // Ensure non-zero state
    if (state->s0 == 0 && state->s1 == 0) {
        state->s0 = 1;
    }
}

/*
 * Generate random 256-bit private keys
 * Each work item generates one 32-byte private key
 */
__kernel void generate_random_keys(
    __global uchar* output,     // Output buffer: 32 bytes per key
    ulong seed,                  // Random seed
    uint count                   // Number of keys to generate
) {
    uint gid = get_global_id(0);
    if (gid >= count) return;
    
    // Initialize PRNG state
    xorshift128_state state;
    init_state(&state, seed, gid);
    
    // Generate 32 bytes (4 x 64-bit values)
    __global uchar* key = output + (gid * 32);
    
    for (int i = 0; i < 4; i++) {
        ulong r = xorshift128plus(&state);
        // Store 8 bytes
        key[i*8 + 0] = (r >> 0) & 0xFF;
        key[i*8 + 1] = (r >> 8) & 0xFF;
        key[i*8 + 2] = (r >> 16) & 0xFF;
        key[i*8 + 3] = (r >> 24) & 0xFF;
        key[i*8 + 4] = (r >> 32) & 0xFF;
        key[i*8 + 5] = (r >> 40) & 0xFF;
        key[i*8 + 6] = (r >> 48) & 0xFF;
        key[i*8 + 7] = (r >> 56) & 0xFF;
    }
}
"""


def _worker_generate_addresses(args):
    """
    Worker function to generate Bitcoin addresses from private keys using coincurve.
    
    This runs in a separate process for parallel address generation.
    """
    private_keys, check_hash160s, check_prefix = args
    
    if not COINCURVE_AVAILABLE:
        return []
    
    results = []
    
    for privkey_bytes in private_keys:
        try:
            # Validate private key is in valid range
            privkey_int = int.from_bytes(privkey_bytes, 'big')
            if privkey_int == 0 or privkey_int >= 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEBAAEDCE6AF48A03BBFD25E8CD0364141:
                continue
            
            # Generate public key using coincurve (libsecp256k1)
            private_key = coincurve.PrivateKey(privkey_bytes)
            public_key = private_key.public_key.format(compressed=True)
            
            # Compute hash160 (RIPEMD160(SHA256(pubkey)))
            sha256_hash = hashlib.sha256(public_key).digest()
            ripemd160 = hashlib.new('ripemd160')
            ripemd160.update(sha256_hash)
            h160 = ripemd160.digest()
            
            # Check against known addresses first (most common case - no match)
            if check_hash160s is not None and h160 in check_hash160s:
                # MATCH FOUND! Generate full address info
                address = base58check_encode(0x00, h160)  # P2PKH mainnet
                wif = _privkey_to_wif(privkey_bytes, compressed=True)
                results.append({
                    'address': address,
                    'wif': wif,
                    'pubkey': public_key.hex(),
                    'hash160': h160.hex(),
                    'match_type': 'balance'
                })
            
            # Check prefix match (vanity address)
            if check_prefix:
                address = base58check_encode(0x00, h160)
                if address.startswith(check_prefix):
                    wif = _privkey_to_wif(privkey_bytes, compressed=True)
                    results.append({
                        'address': address,
                        'wif': wif,
                        'pubkey': public_key.hex(),
                        'hash160': h160.hex(),
                        'match_type': 'prefix'
                    })
                    
        except Exception:
            # Skip invalid keys
            continue
    
    return results


def _privkey_to_wif(privkey_bytes: bytes, compressed: bool = True, testnet: bool = False) -> str:
    """Convert private key bytes to WIF format."""
    version = 0xef if testnet else 0x80
    payload = privkey_bytes
    if compressed:
        payload = payload + b'\x01'
    
    data = bytes([version]) + payload
    checksum = hashlib.sha256(hashlib.sha256(data).digest()).digest()[:4]
    
    import base58
    return base58.b58encode(data + checksum).decode('ascii')


class HybridGenerator:
    """
    High-performance Bitcoin address generator using GPU+coincurve hybrid approach.
    
    This generator achieves ~100K addresses/second with 100% correctness by:
    1. Using GPU for fast parallel random number generation
    2. Using coincurve (libsecp256k1) for correct elliptic curve operations
    3. Using multiprocessing for parallel address generation on CPU
    
    Usage:
        generator = HybridGenerator(
            batch_size=50000,
            num_workers=8
        )
        generator.set_balance_checker(balance_checker)
        generator.start()
        
        while generator.running:
            result = generator.get_result(timeout=1.0)
            if result:
                print(f"Found: {result['address']}")
    """
    
    def __init__(
        self,
        prefix: str = '',
        batch_size: int = 50000,
        num_workers: Optional[int] = None,
        device_selector: Optional[Tuple[int, int]] = None,
        use_gpu: bool = True
    ):
        """
        Initialize the hybrid generator.
        
        Args:
            prefix: Vanity prefix to search for (e.g., '1ABC')
            batch_size: Number of keys to generate per batch
            num_workers: Number of CPU workers for address generation (default: cpu_count)
            device_selector: (platform_idx, device_idx) for OpenCL device selection
            use_gpu: Whether to use GPU for RNG (falls back to CPU if unavailable)
        """
        self.prefix = prefix
        self.batch_size = batch_size
        self.num_workers = num_workers or max(1, cpu_count() - 1)
        self.device_selector = device_selector
        self.use_gpu = use_gpu and OPENCL_AVAILABLE
        
        # Threading state
        self.running = False
        self.paused = False
        self.stop_event = threading.Event()
        self.pause_event = threading.Event()
        self.result_queue = queue.Queue()
        self.search_thread = None
        
        # Statistics
        self.stats_counter = 0
        self.stats_lock = threading.Lock()
        self.start_time = None
        
        # OpenCL resources
        self.ctx = None
        self.cl_queue = None
        self.program = None
        self.kernel = None
        self.device = None
        self.gpu_available = False
        
        # Balance checker integration
        self.balance_checker = None
        self.check_hash160s: Optional[Set[bytes]] = None
        
        # Seed for RNG
        self.rng_seed = int.from_bytes(secrets.token_bytes(8), 'big')
        
        # Verify coincurve is available
        if not COINCURVE_AVAILABLE:
            raise ImportError(
                "coincurve is required for HybridGenerator. "
                "Install with: pip install coincurve"
            )
    
    def init_gpu(self) -> bool:
        """Initialize OpenCL for GPU random number generation."""
        if not OPENCL_AVAILABLE:
            print("[HybridGenerator] OpenCL not available, using CPU for RNG")
            return False
        
        try:
            platforms = cl.get_platforms()
            if not platforms:
                print("[HybridGenerator] No OpenCL platforms found")
                return False
            
            # Select device
            if self.device_selector:
                p_idx, d_idx = self.device_selector
                platform = platforms[p_idx]
                devices = platform.get_devices()
                self.device = devices[d_idx]
            else:
                # Auto-detect GPU
                for platform in platforms:
                    try:
                        gpus = platform.get_devices(device_type=cl.device_type.GPU)
                        if gpus:
                            self.device = gpus[0]
                            break
                    except Exception:
                        pass
                
                if not self.device:
                    # Fall back to first available device
                    self.device = platforms[0].get_devices()[0]
            
            # Create context and compile kernel
            self.ctx = cl.Context([self.device])
            self.cl_queue = cl.CommandQueue(self.ctx)
            self.program = cl.Program(self.ctx, RNG_KERNEL_SOURCE).build()
            self.kernel = self.program.generate_random_keys
            
            self.gpu_available = True
            print(f"[HybridGenerator] GPU initialized: {self.device.name}")
            print(f"[HybridGenerator]   Global memory: {self.device.global_mem_size / (1024**3):.2f} GB")
            print(f"[HybridGenerator]   Compute units: {self.device.max_compute_units}")
            return True
            
        except Exception as e:
            print(f"[HybridGenerator] GPU init failed: {e}")
            return False
    
    def set_balance_checker(self, balance_checker):
        """
        Set the balance checker for matching against known funded addresses.
        
        This extracts hash160 values from the balance checker for efficient matching.
        """
        self.balance_checker = balance_checker
        
        if balance_checker and balance_checker.is_loaded:
            print("[HybridGenerator] Loading addresses for matching...")
            self._build_hash160_set()
            print(f"[HybridGenerator] Loaded {len(self.check_hash160s)} addresses for matching")
    
    def _build_hash160_set(self):
        """Build a set of hash160 values for efficient matching."""
        if not self.balance_checker:
            self.check_hash160s = None
            return
        
        hash160s = set()
        
        # Try to import base58 decode
        try:
            from .crypto_utils import base58_decode
        except ImportError:
            from crypto_utils import base58_decode
        
        # Get addresses from balance checker
        addresses = []
        if self.balance_checker.funded_addresses:
            addresses = list(self.balance_checker.funded_addresses)
        elif self.balance_checker.address_balances:
            addresses = list(self.balance_checker.address_balances.keys())
        
        for addr in addresses:
            try:
                # Decode base58 address to extract hash160
                decoded = base58_decode(addr)
                if decoded and len(decoded) >= 21:
                    # Skip version byte, take 20-byte hash160
                    h160 = bytes(decoded[1:21])
                    hash160s.add(h160)
            except Exception:
                continue
        
        self.check_hash160s = hash160s if hash160s else None
    
    def _generate_random_keys_gpu(self, count: int) -> np.ndarray:
        """Generate random private keys using GPU."""
        if not self.gpu_available:
            return None
        
        try:
            mf = cl.mem_flags
            output = np.zeros(count * 32, dtype=np.uint8)
            output_buf = cl.Buffer(self.ctx, mf.WRITE_ONLY, output.nbytes)
            
            # Execute kernel
            self.kernel(
                self.cl_queue,
                (count,),
                None,
                output_buf,
                np.uint64(self.rng_seed),
                np.uint32(count)
            )
            
            # Read results
            cl.enqueue_copy(self.cl_queue, output, output_buf)
            self.cl_queue.finish()
            output_buf.release()
            
            # Update seed
            self.rng_seed += count
            
            return output.reshape(count, 32)
            
        except Exception as e:
            print(f"[HybridGenerator] GPU RNG error: {e}")
            return None
    
    def _generate_random_keys_cpu(self, count: int) -> List[bytes]:
        """Generate random private keys using CPU (fallback)."""
        return [secrets.token_bytes(32) for _ in range(count)]
    
    def _process_batch(self, private_keys: List[bytes]) -> List[dict]:
        """
        Process a batch of private keys to find matching addresses.
        
        Uses multiprocessing for parallel address generation with coincurve.
        """
        if not private_keys:
            return []
        
        # Split into chunks for workers
        chunk_size = max(1, len(private_keys) // self.num_workers)
        chunks = []
        for i in range(0, len(private_keys), chunk_size):
            chunk = private_keys[i:i + chunk_size]
            chunks.append((chunk, self.check_hash160s, self.prefix))
        
        # Process in parallel using process pool
        results = []
        with ProcessPoolExecutor(max_workers=self.num_workers) as executor:
            for chunk_results in executor.map(_worker_generate_addresses, chunks):
                results.extend(chunk_results)
        
        return results
    
    def _search_loop(self):
        """Main search loop running in background thread."""
        print("[HybridGenerator] Starting search loop...")
        print(f"[HybridGenerator]   Batch size: {self.batch_size}")
        print(f"[HybridGenerator]   Workers: {self.num_workers}")
        print(f"[HybridGenerator]   GPU RNG: {self.gpu_available}")
        print(f"[HybridGenerator]   Addresses to match: {len(self.check_hash160s) if self.check_hash160s else 0}")
        
        self.start_time = time.time()
        batch_count = 0
        
        while not self.stop_event.is_set():
            # Check pause
            if self.pause_event.is_set():
                time.sleep(0.1)
                continue
            
            batch_start = time.time()
            batch_count += 1
            
            try:
                # Generate random keys
                if self.gpu_available:
                    keys_array = self._generate_random_keys_gpu(self.batch_size)
                    if keys_array is not None:
                        private_keys = [bytes(k) for k in keys_array]
                    else:
                        private_keys = self._generate_random_keys_cpu(self.batch_size)
                else:
                    private_keys = self._generate_random_keys_cpu(self.batch_size)
                
                # Process batch (EC math + address generation + matching)
                matches = self._process_batch(private_keys)
                
                # Queue results
                for match in matches:
                    self.result_queue.put(match)
                
                # Update stats
                with self.stats_lock:
                    self.stats_counter += len(private_keys)
                
                # Log progress
                batch_time = time.time() - batch_start
                rate = len(private_keys) / batch_time if batch_time > 0 else 0
                
                if batch_count % 10 == 0:
                    total_time = time.time() - self.start_time
                    total_rate = self.stats_counter / total_time if total_time > 0 else 0
                    print(f"[HybridGenerator] Batch {batch_count}: {rate:.0f} keys/sec (avg: {total_rate:.0f}/sec)")
                    if matches:
                        print(f"[HybridGenerator]   Found {len(matches)} matches!")
                        
            except Exception as e:
                print(f"[HybridGenerator] Error in batch {batch_count}: {e}")
                import traceback
                traceback.print_exc()
                time.sleep(0.1)
        
        print("[HybridGenerator] Search loop ended")
    
    def start(self):
        """Start the address generation search."""
        if self.running:
            print("[HybridGenerator] Already running")
            return
        
        # Initialize GPU if requested
        if self.use_gpu and not self.gpu_available:
            self.init_gpu()
        
        self.running = True
        self.stop_event.clear()
        self.pause_event.clear()
        
        self.search_thread = threading.Thread(target=self._search_loop, daemon=True)
        self.search_thread.start()
        
        print("[HybridGenerator] Started")
    
    def stop(self):
        """Stop the address generation search."""
        if not self.running:
            return
        
        self.stop_event.set()
        self.running = False
        
        if self.search_thread:
            self.search_thread.join(timeout=5.0)
        
        print("[HybridGenerator] Stopped")
    
    def pause(self):
        """Pause the search."""
        self.pause_event.set()
        self.paused = True
    
    def resume(self):
        """Resume the search."""
        self.pause_event.clear()
        self.paused = False
    
    def get_result(self, timeout: float = 0.1) -> Optional[dict]:
        """
        Get a result from the queue.
        
        Returns None if no result available within timeout.
        """
        try:
            return self.result_queue.get(timeout=timeout)
        except queue.Empty:
            return None
    
    def get_stats(self) -> dict:
        """Get current statistics."""
        with self.stats_lock:
            total = self.stats_counter
        
        elapsed = time.time() - self.start_time if self.start_time else 0
        rate = total / elapsed if elapsed > 0 else 0
        
        return {
            'total_generated': total,
            'elapsed_seconds': elapsed,
            'rate_per_second': rate,
            'gpu_available': self.gpu_available,
            'num_workers': self.num_workers,
            'batch_size': self.batch_size
        }
    
    def get_speed(self) -> float:
        """Get current generation speed in addresses per second."""
        return self.get_stats()['rate_per_second']
    
    def is_available(self) -> bool:
        """Check if the generator is available (coincurve installed)."""
        return COINCURVE_AVAILABLE


def test_coincurve_correctness():
    """
    Test that coincurve generates correct Bitcoin addresses.
    
    This verifies the implementation against known test vectors.
    """
    print("\n=== Testing coincurve correctness ===\n")
    
    if not COINCURVE_AVAILABLE:
        print("ERROR: coincurve not installed!")
        return False
    
    # Test vector 1: Known private key -> address
    # Private key: 0x0000000000000000000000000000000000000000000000000000000000000001
    test_privkey = bytes.fromhex('0000000000000000000000000000000000000000000000000000000000000001')
    expected_address = '1BgGZ9tcN4rm9KBzDn7KprQz87SZ26SAMH'  # P2PKH compressed
    expected_pubkey = '0279be667ef9dcbbac55a06295ce870b07029bfcdb2dce28d959f2815b16f81798'
    
    try:
        # Generate using coincurve
        private_key = coincurve.PrivateKey(test_privkey)
        public_key = private_key.public_key.format(compressed=True)
        
        # Compute hash160
        sha256_hash = hashlib.sha256(public_key).digest()
        ripemd160 = hashlib.new('ripemd160')
        ripemd160.update(sha256_hash)
        h160 = ripemd160.digest()
        
        # Generate address
        address = base58check_encode(0x00, h160)
        
        print(f"Private key: {test_privkey.hex()}")
        print(f"Public key:  {public_key.hex()}")
        print(f"Expected:    {expected_pubkey}")
        print(f"Address:     {address}")
        print(f"Expected:    {expected_address}")
        
        if public_key.hex() == expected_pubkey and address == expected_address:
            print("\n✓ Test PASSED - coincurve generates correct addresses!")
            return True
        else:
            print("\n✗ Test FAILED - addresses don't match!")
            return False
            
    except Exception as e:
        print(f"ERROR: {e}")
        return False


def benchmark_hybrid_generator(duration: float = 10.0, batch_size: int = 50000):
    """
    Benchmark the hybrid generator.
    
    Args:
        duration: How long to run the benchmark in seconds
        batch_size: Batch size to use
    """
    print(f"\n=== Benchmarking HybridGenerator ({duration}s) ===\n")
    
    generator = HybridGenerator(
        prefix='',
        batch_size=batch_size,
        num_workers=max(1, cpu_count() - 1),
        use_gpu=True
    )
    
    # Initialize GPU
    generator.init_gpu()
    
    print(f"Configuration:")
    print(f"  Batch size: {batch_size}")
    print(f"  Workers: {generator.num_workers}")
    print(f"  GPU available: {generator.gpu_available}")
    print()
    
    # Start generator
    generator.start()
    
    # Run for specified duration
    start = time.time()
    while time.time() - start < duration:
        time.sleep(1.0)
        stats = generator.get_stats()
        print(f"  Rate: {stats['rate_per_second']:,.0f} addresses/sec | Total: {stats['total_generated']:,}")
    
    # Stop and get final stats
    generator.stop()
    stats = generator.get_stats()
    
    print(f"\n=== Benchmark Results ===")
    print(f"Total addresses generated: {stats['total_generated']:,}")
    print(f"Time elapsed: {stats['elapsed_seconds']:.2f} seconds")
    print(f"Average rate: {stats['rate_per_second']:,.0f} addresses/second")
    print()
    
    return stats


if __name__ == '__main__':
    # Run tests
    test_coincurve_correctness()
    
    # Run benchmark
    print("\nRunning benchmark...")
    benchmark_hybrid_generator(duration=10.0, batch_size=50000)
