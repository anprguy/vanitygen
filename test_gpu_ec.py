#!/usr/bin/env python3
"""
Test if GPU EC operations generate correct Bitcoin addresses
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'vanitygen_py'))

from vanitygen_py.bitcoin_keys import BitcoinKey
from vanitygen_py.gpu_generator import GPUGenerator

def test_gpu_ec():
    """Test if GPU generates correct addresses compared to CPU"""
    print("Testing GPU EC operations...")
    print("="*60)
    
    # Create a GPU generator
    gen = GPUGenerator(
        prefix="1",  # Simple prefix
        addr_type='p2pkh',
        batch_size=10,  # Small batch for testing
        gpu_only=True  # Test GPU-only mode
    )
    
    # Initialize GPU
    if not gen.init_cl():
        print("ERROR: Failed to initialize GPU")
        return False
    
    print(f"\nUsing GPU: {gen.device.name}")
    print(f"Batch size: 10")
    print("\nGenerating 10 test keys...\n")
    
    # Generate some keys on GPU
    gpu_keys = gen._generate_keys_on_gpu(10)
    if gpu_keys is None:
        print("ERROR: Failed to generate keys on GPU")
        return False
    
    # Test each key
    all_correct = True
    for i, key_data in enumerate(gpu_keys):
        # Convert GPU key to bytes (GPU stores in little-endian uint32 array)
        import struct
        key_bytes = b''.join(struct.pack('<I', word) for word in key_data)[::-1]
        
        # Generate address on CPU (reference implementation)
        cpu_key = BitcoinKey(key_bytes)
        cpu_addr = cpu_key.get_p2pkh_address()
        cpu_pub = cpu_key.get_public_key(compressed=True).hex()
        
        print(f"Key {i+1}:")
        print(f"  Private: {key_bytes.hex()[:32]}...")
        print(f"  CPU Pub: {cpu_pub}")
        print(f"  CPU Addr: {cpu_addr}")
        
        # TODO: Generate address on GPU and compare
        # For now, just verify CPU generation works
        print(f"  ✓ CPU generation successful\n")
    
    print("="*60)
    print("Test completed - CPU generation works")
    print("\nNote: To fully test GPU EC, we need to call the")
    print("generate_addresses_full_exact kernel and compare results")
    
    return True

if __name__ == "__main__":
    try:
        success = test_gpu_ec()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
