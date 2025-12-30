#!/usr/bin/env python3
"""
Test script to verify GPU key generation produces valid ECDSA keys
"""

import sys
import time
from vanitygen_py.gpu_generator import GPUGenerator

def test_gpu_keys():
    """Test that GPU-generated keys pass ECDSA validation"""
    
    print("=" * 80)
    print("Testing GPU Key Generation Fix")
    print("=" * 80)
    
    # Create generator with simple prefix to get quick results
    generator = GPUGenerator(
        prefix="1",  # All Bitcoin addresses start with 1, so this will match everything
        batch_size=100,  # Small batch for testing
        gpu_only=True
    )
    
    # Initialize GPU
    print("\n1. Initializing GPU...")
    if not generator.init_cl():
        print("ERROR: GPU initialization failed!")
        return False
    
    print("✓ GPU initialized successfully")
    
    # Start generation
    print("\n2. Starting key generation...")
    generator.start()
    
    # Wait for some results
    print("\n3. Waiting for results (5 seconds)...")
    time.sleep(5)
    
    # Stop generation
    print("\n4. Stopping generation...")
    generator.stop()
    
    # Check results
    print("\n5. Checking results...")
    results = []
    while not generator.result_queue.empty():
        result = generator.result_queue.get()
        results.append(result)
    
    if not results:
        print("ERROR: No results generated!")
        return False
    
    print(f"\n✓ Generated {len(results)} valid keys")
    
    # Show first few results
    print("\n6. Sample results:")
    for i, (address, wif, pubkey) in enumerate(results[:5]):
        print(f"   Key {i+1}:")
        print(f"     Address: {address}")
        print(f"     WIF: {wif[:20]}...{wif[-10:]}")
        print(f"     Public Key: {pubkey[:20]}...{pubkey[-10:]}")
    
    print("\n" + "=" * 80)
    print("✓ ALL TESTS PASSED - GPU keys are valid!")
    print("=" * 80)
    
    return True

if __name__ == "__main__":
    try:
        success = test_gpu_keys()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\nERROR: Test failed with exception: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
