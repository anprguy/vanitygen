# Hybrid GPU+CPU Bitcoin Address Generator

## Overview

The **HybridGenerator** provides high-performance Bitcoin address generation with **guaranteed correctness** by combining:

1. **GPU acceleration** for parallel random number generation (embarrassingly parallel)
2. **coincurve library** (Bitcoin Core's libsecp256k1) for 100% correct elliptic curve math
3. **Multi-core CPU processing** for parallel address derivation
4. **Efficient bloom filter** for fast address matching against 55+ million known addresses

## Key Benefits

| Feature | Benefit |
|---------|---------|
| **100% Correct Addresses** | Uses Bitcoin Core's battle-tested libsecp256k1 library |
| **~40-100K addresses/sec** | High performance even on CPU-only systems |
| **Zero Risk** | Private keys cryptographically control their addresses |
| **Ready in Minutes** | No complex GPU EC math implementation required |

## Installation

```bash
# Install required packages
pip install coincurve pyopencl numpy

# Optional but recommended
pip install base58 bech32 psutil
```

## Quick Start

### Basic Usage

```python
from vanitygen_py.hybrid_generator import HybridGenerator
from vanitygen_py.balance_checker import BalanceChecker

# Create generator
generator = HybridGenerator(
    batch_size=50000,      # Keys per batch
    num_workers=8,         # CPU workers for address generation
    use_gpu=True           # Use GPU for random number generation
)

# Load addresses to check against
balance_checker = BalanceChecker()
balance_checker.load_from_csv('funded_addresses.csv')  # Or load from Bitcoin Core

# Connect balance checker
generator.set_balance_checker(balance_checker)

# Start generating
generator.start()

# Check for matches
while generator.running:
    result = generator.get_result(timeout=1.0)
    if result:
        print(f"FOUND: {result['address']}")
        print(f"WIF:   {result['wif']}")
        print(f"Type:  {result['match_type']}")
```

### Using the Bitcoin Address Hunter CLI

```bash
# Check against a CSV file of funded addresses
python vanitygen_py/btc_address_hunter.py \
    --csv funded_addresses.csv \
    --duration 3600 \
    --batch-size 50000 \
    --workers 8

# Check against Bitcoin Core chainstate
python vanitygen_py/btc_address_hunter.py \
    --chainstate ~/.bitcoin/chainstate \
    --duration 3600

# Benchmark mode (no address checking)
python vanitygen_py/btc_address_hunter.py \
    --benchmark \
    --duration 60
```

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                     HybridGenerator                              │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌─────────────────┐    ┌─────────────────────────────────────┐ │
│  │   GPU Kernel    │    │        CPU Workers (coincurve)      │ │
│  │                 │    │                                     │ │
│  │  XORShift128+   │───▶│  Private Key → Public Key           │ │
│  │  Random Number  │    │  (secp256k1 point multiplication)   │ │
│  │  Generation     │    │                                     │ │
│  │                 │    │  Public Key → Hash160               │ │
│  │  ~1B random     │    │  (SHA256 + RIPEMD160)               │ │
│  │  bytes/second   │    │                                     │ │
│  └─────────────────┘    │  Hash160 → Address                  │ │
│                         │  (Base58Check encoding)             │ │
│                         │                                     │ │
│                         │  ~40-100K addresses/second          │ │
│                         └─────────────────────────────────────┘ │
│                                         │                       │
│                                         ▼                       │
│                         ┌─────────────────────────────────────┐ │
│                         │      Address Matching               │ │
│                         │                                     │ │
│                         │  1. Bloom filter pre-check (fast)   │ │
│                         │  2. Hash160 set lookup (exact)      │ │
│                         │                                     │ │
│                         │  Match? → Queue result              │ │
│                         └─────────────────────────────────────┘ │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

## Performance Tuning

### Batch Size

- **Smaller batches (10K-20K)**: Lower latency, more responsive stats
- **Larger batches (50K-100K)**: Higher throughput, better GPU utilization

```python
generator = HybridGenerator(batch_size=50000)
```

### Number of Workers

By default, uses `cpu_count() - 1`. Adjust based on your system:

```python
generator = HybridGenerator(num_workers=8)
```

### GPU vs CPU-only

The generator automatically falls back to CPU if no GPU is available:

```python
# Force CPU-only mode
generator = HybridGenerator(use_gpu=False)
```

## Why Hybrid Instead of Pure GPU?

Implementing secp256k1 elliptic curve cryptography correctly on the GPU is **extremely difficult**:

| Challenge | Difficulty |
|-----------|------------|
| 256-bit modular arithmetic | Complex |
| Field inversion (extended Euclidean algorithm) | Very complex |
| Point addition/doubling | Complex |
| Scalar multiplication (double-and-add) | Complex |
| Side-channel resistance | Critical |
| Testing & verification | Time-consuming |

A small error in any of these would generate **invalid addresses** that don't correspond to the private keys!

The hybrid approach gives us:
- **Correctness**: libsecp256k1 is proven, audited, and used by Bitcoin Core
- **Speed**: GPU handles the easy parallel part (RNG), CPU handles the complex crypto
- **Simplicity**: No need to debug complex GPU EC code
- **Reliability**: Zero risk of generating wrong addresses

## Verification

The implementation includes built-in verification:

```python
from vanitygen_py.hybrid_generator import test_coincurve_correctness

# Verify against known test vectors
test_coincurve_correctness()
```

Output:
```
=== Testing coincurve correctness ===

Private key: 0000000000000000000000000000000000000000000000000000000000000001
Public key:  0279be667ef9dcbbac55a06295ce870b07029bfcdb2dce28d959f2815b16f81798
Address:     1BgGZ9tcN4rm9KBzDn7KprQz87SZ26SAMH

✓ Test PASSED - coincurve generates correct addresses!
```

## Loading 55 Million Addresses

For checking against large address sets:

```python
# From CSV file (recommended for large datasets)
balance_checker.load_from_csv('funded_addresses.csv')

# From Bitcoin Core (requires fully synced node)
balance_checker.load_from_bitcoin_core()

# Memory estimate: ~20 bytes per address = ~1.1 GB for 55M addresses
```

## Statistics and Monitoring

```python
# Get current stats
stats = generator.get_stats()
print(f"Total: {stats['total_generated']:,}")
print(f"Rate: {stats['rate_per_second']:,.0f}/sec")
print(f"GPU: {stats['gpu_available']}")

# Get current speed
speed = generator.get_speed()
print(f"Speed: {speed:,.0f} addresses/second")
```

## API Reference

### HybridGenerator

```python
HybridGenerator(
    prefix='',              # Vanity prefix to search for
    batch_size=50000,       # Keys per batch
    num_workers=None,       # CPU workers (default: cpu_count-1)
    device_selector=None,   # (platform_idx, device_idx) for GPU
    use_gpu=True            # Use GPU for RNG
)
```

**Methods:**
- `init_gpu()` - Initialize OpenCL
- `set_balance_checker(checker)` - Set BalanceChecker for matching
- `start()` - Start generation
- `stop()` - Stop generation
- `pause()` / `resume()` - Pause/resume generation
- `get_result(timeout)` - Get next match (or None)
- `get_stats()` - Get statistics dict
- `get_speed()` - Get current speed

### BitcoinAddressHunter

A higher-level wrapper with CLI support:

```python
hunter = BitcoinAddressHunter(
    batch_size=50000,
    num_workers=8,
    use_gpu=True,
    output_file='found_addresses.json',
    verbose=True
)

hunter.load_addresses_from_csv('funded.csv')
hunter.run(duration=3600)  # Run for 1 hour
```

## Troubleshooting

### "coincurve not installed"

```bash
pip install coincurve
```

### "No OpenCL platforms found"

- Install OpenCL drivers for your GPU
- The generator will still work using CPU-only mode

### Low performance

- Increase `batch_size`
- Ensure you have multiple CPU cores available
- Check that coincurve is properly installed (uses C extension)

## License

MIT License - See LICENSE file for details.
