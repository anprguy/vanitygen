#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
COMPREHENSIVE GPU EC CORRECTNESS TEST

This test verifies that the GPU generates correct Bitcoin addresses
by comparing GPU-generated addresses with CPU-generated addresses
for the same private keys.

This is the CRITICAL test to verify GPU EC operations are correct.

Compatible with Python 2.7 and Python 3.x
"""
from __future__ import print_function
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'vanitygen_py'))

import struct
import numpy as np

try:
    import pyopencl as cl
except ImportError:
    print("ERROR: pyopencl not installed")
    print("Install with: pip install pyopencl")
    sys.exit(1)

from vanitygen_py.bitcoin_keys import BitcoinKey


def test_gpu_ec_correctness():
    """
    Test if GPU EC operations generate correct Bitcoin addresses.
    
    Steps:
    1. Generate random private keys
    2. Compute addresses on GPU (using full GPU kernel)
    3. Compute addresses on CPU (using proven BitcoinKey)
    4. Compare - ALL addresses must match exactly
    5. Report any mismatches with details
    """
    print("="*80)
    print("GPU EC CORRECTNESS TEST")
    print("="*80)
    print()
    print("This test verifies GPU generates correct Bitcoin addresses")
    print("by comparing GPU vs CPU output for the same private keys.")
    print()
    
    # Initialize OpenCL
    print("[1] Initializing OpenCL...")
    try:
        platforms = cl.get_platforms()
        if not platforms:
            print("ERROR: No OpenCL platforms found")
            return False
        
        # Try to find a GPU
        device = None
        for platform in platforms:
            try:
                gpus = platform.get_devices(device_type=cl.device_type.GPU)
                if gpus:
                    device = gpus[0]
                    break
            except:
                pass
        
        if device is None:
            # Fall back to first device
            device = platforms[0].get_devices()[0]
        
        print("    Using device: {}".format(device.name))
        ctx = cl.Context([device])
        queue = cl.CommandQueue(ctx)
        
    except Exception as e:
        print("ERROR: Failed to initialize OpenCL: {}".format(e))
        return False
    
    # Load and compile GPU kernel
    print("[2] Loading GPU kernel...")
    kernel_path = os.path.join(os.path.dirname(__file__), 'vanitygen_py', 'gpu_kernel.cl')
    if not os.path.exists(kernel_path):
        print("ERROR: Kernel not found at {}".format(kernel_path))
        return False
    
    try:
        with open(kernel_path, 'r') as f:
            kernel_source = f.read()
        program = cl.Program(ctx, kernel_source).build()
        print("    ✓ Kernel compiled successfully")
    except Exception as e:
        print("ERROR: Failed to compile kernel: {}".format(e))
        return False
    
    # Test parameters
    num_tests = 100  # Test 100 addresses
    print("\n[3] Testing {} random private keys...".format(num_tests))
    print()
    
    # Generate test seed
    seed = struct.unpack('<Q', os.urandom(8))[0]
    
    # Allocate buffers for GPU kernel
    mf = cl.mem_flags
    results_buffer = np.zeros(num_tests * 128, dtype=np.uint8)
    found_count = np.zeros(1, dtype=np.int32)
    
    # Empty prefix (match all addresses)
    prefix_buffer = np.zeros(64, dtype=np.uint8)
    prefix_len = 0
    
    # No balance checking (just generate addresses)
    dummy_bloom = np.zeros(1, dtype=np.uint8)
    
    # Create GPU buffers
    results_buf = cl.Buffer(ctx, mf.WRITE_ONLY, results_buffer.nbytes)
    found_count_buf = cl.Buffer(ctx, mf.READ_WRITE, 4)
    prefix_buf = cl.Buffer(ctx, mf.READ_ONLY | mf.COPY_HOST_PTR, hostbuf=prefix_buffer)
    bloom_buf = cl.Buffer(ctx, mf.READ_ONLY | mf.COPY_HOST_PTR, hostbuf=dummy_bloom)
    
    # Execute GPU kernel
    print("    [GPU] Generating addresses...")
    try:
        # Use generate_addresses_full kernel
        kernel = program.generate_addresses_full
        
        # Reset found count
        found_count[0] = 0
        cl.enqueue_copy(queue, found_count_buf, found_count)
        
        # Execute kernel
        kernel(
            queue, (num_tests,), None,
            results_buf,                # found_addresses
            found_count_buf,            # found_count  
            np.uint64(seed),            # seed
            np.uint32(num_tests),       # batch_size
            prefix_buf,                 # prefix
            np.int32(prefix_len),       # prefix_len
            np.uint32(num_tests),       # max_addresses
            bloom_buf,                  # bloom_filter (dummy)
            np.uint32(0),               # filter_size (0 = disabled)
            np.uint32(0)                # check_balance (0 = disabled)
        )
        
        # Read results
        cl.enqueue_copy(queue, results_buffer, results_buf)
        cl.enqueue_copy(queue, found_count, found_count_buf)
        queue.finish()
        
        num_found = found_count[0]
        print("    ✓ GPU generated {} addresses".format(num_found))
        
    except Exception as e:
        print("ERROR: GPU kernel failed: {}".format(e))
        import traceback
        traceback.print_exc()
        return False
    
    # Now verify each address on CPU
    print("    [CPU] Verifying addresses...")
    print()
    
    mismatches = []
    matches = 0
    
    for i in range(min(num_found, num_tests)):
        offset = i * 128
        
        # Extract private key (first 32 bytes, little-endian from GPU)
        # GPU stores key as little-endian bytes, need to reverse for Bitcoin
        gpu_key_bytes = results_buffer[offset:offset+32].tobytes()[::-1]
        
        # Extract GPU-generated address (next 64 bytes, null-terminated)
        addr_start = offset + 32
        addr_end = offset + 96
        gpu_addr = ''
        for k in range(addr_start, addr_end):
            if results_buffer[k] == 0:
                break
            gpu_addr += chr(results_buffer[k])
        
        # Generate address on CPU using same private key
        try:
            cpu_key = BitcoinKey(gpu_key_bytes)
            cpu_addr = cpu_key.get_p2pkh_address()
            cpu_pub_bytes = cpu_key.get_public_key(compressed=True)
            # Convert to hex string (Python 2/3 compatible)
            try:
                cpu_pub = cpu_pub_bytes.hex()
            except AttributeError:
                cpu_pub = cpu_pub_bytes.encode('hex')
            
            # Compare
            if gpu_addr == cpu_addr:
                matches += 1
                if i < 5:  # Show first 5 matches
                    print("    ✓ Match #{}:".format(i+1))
                    print("       Address: {}".format(gpu_addr))
                    print("       (GPU and CPU both generated same address)")
                    print()
            else:
                # Convert private key to hex (Python 2/3 compatible)
                try:
                    priv_hex = gpu_key_bytes.hex()
                except AttributeError:
                    priv_hex = gpu_key_bytes.encode('hex')
                    
                mismatches.append({
                    'index': i,
                    'private_key': priv_hex,
                    'gpu_addr': gpu_addr,
                    'cpu_addr': cpu_addr,
                    'cpu_pub': cpu_pub
                })
                
        except Exception as e:
            # Convert private key to hex (Python 2/3 compatible)
            try:
                priv_hex = gpu_key_bytes.hex()
            except AttributeError:
                priv_hex = gpu_key_bytes.encode('hex')
                
            mismatches.append({
                'index': i,
                'private_key': priv_hex,
                'error': str(e)
            })
    
    # Report results
    print()
    print("="*80)
    print("TEST RESULTS")
    print("="*80)
    print()
    print("Total addresses tested: {}".format(num_found))
    print("Matches (GPU == CPU):   {}".format(matches))
    print("Mismatches:             {}".format(len(mismatches)))
    print()
    
    if len(mismatches) == 0:
        print("✓✓✓ SUCCESS! ALL ADDRESSES MATCH ✓✓✓")
        print()
        print("GPU EC operations are CORRECT!")
        print("GPU-generated addresses match CPU-generated addresses.")
        print()
        return True
    else:
        print("✗✗✗ FAILURE! GPU EC OPERATIONS ARE INCORRECT ✗✗✗")
        print()
        print("GPU-generated addresses do NOT match CPU-generated addresses.")
        print()
        print("MISMATCH DETAILS:")
        print("-" * 80)
        
        for m in mismatches[:10]:  # Show first 10 mismatches
            print("\nMismatch #{}:".format(m['index']+1))
            print("  Private Key: {}...".format(m.get('private_key', 'N/A')[:32]))
            
            if 'error' in m:
                print("  ERROR: {}".format(m['error']))
            else:
                print("  GPU Address: {}".format(m.get('gpu_addr', 'N/A')))
                print("  CPU Address: {}".format(m.get('cpu_addr', 'N/A')))
                print("  CPU Pubkey:  {}...".format(m.get('cpu_pub', 'N/A')[:32]))
                
                if m.get('gpu_addr') and m.get('cpu_addr'):
                    # Analyze difference
                    if m['gpu_addr'][0] != m['cpu_addr'][0]:
                        print("  → First character differs (version byte issue?)")
                    else:
                        print("  → Same version, different hash (EC or hash issue)")
        
        print()
        print("POSSIBLE CAUSES:")
        print("1. EC scalar multiplication implementation is incorrect")
        print("2. Montgomery domain conversions are wrong")
        print("3. Modular inverse implementation has bugs")
        print("4. Point normalization (Jacobian → affine) is incorrect")
        print("5. Endianness issues (byte order)")
        print("6. Hash160 implementation (SHA256 or RIPEMD160)")
        print("7. Base58 encoding errors")
        print()
        print("RECOMMENDATION:")
        print("Use Hybrid Mode instead (GPU RNG + coincurve EC)")
        print("This guarantees correct addresses using Bitcoin Core's libsecp256k1")
        print()
        
        return False


if __name__ == "__main__":
    try:
        success = test_gpu_ec_correctness()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\nTest interrupted by user")
        sys.exit(1)
    except Exception as e:
        print("\nFATAL ERROR: {}".format(e))
        import traceback
        traceback.print_exc()
        sys.exit(1)
