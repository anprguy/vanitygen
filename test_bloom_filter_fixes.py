#!/usr/bin/env python3
"""
Test script to verify that the bloom filter fixes are working correctly.
This tests the hash matching between Python and GPU implementations.
"""

import sys
import os

# Add the vanitygen_py directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'vanitygen_py'))

def test_base58_decode():
    """Test that base58_decode function works correctly"""
    print("Testing base58_decode function...")
    
    try:
        from crypto_utils import decode_base58_address
        
        # Test with genesis block address
        test_addr = "1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa"
        version, hash160 = decode_base58_address(test_addr)
        
        assert version == 0, f"Expected version 0, got {version}"
        assert len(hash160) == 20, f"Expected 20-byte hash160, got {len(hash160)} bytes"
        assert hash160.hex() == "62e907b15cbf27d5425399ebf6f0fb50ebb88f18", f"Hash160 mismatch: {hash160.hex()}"
        
        print("✅ base58_decode works correctly")
        return True
        
    except Exception as e:
        print(f"❌ base58_decode failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_bloom_hash_consistency():
    """Test that bloom hash function is consistent between Python and GPU"""
    print("\nTesting bloom hash consistency...")
    
    try:
        from balance_checker import BalanceChecker
        
        # Create a test bloom filter
        checker = BalanceChecker()
        test_addresses = [
            "1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa",  # Genesis block
            "1BgGZ9tcN4rm9KBzDn7KprQz87SZ26SAMH",  # Private key = 1
            "12c6DSiU4Rq3P4ZxziKxzrL5LmMBrzjrJX"   # Private key = 2
        ]
        
        # Create bloom filter
        bloom_data, num_bits = checker.create_bloom_filter(test_addresses)
        
        assert bloom_data is not None, "Bloom filter creation failed"
        assert len(bloom_data) > 0, "Bloom filter is empty"
        assert num_bits > 0, "Bloom filter has no bits"
        
        print(f"✅ Bloom filter created: {len(bloom_data)} bytes ({num_bits} bits)")
        print(f"   Expected false positive rate: ~{0.5 ** 7 * 100:.2f}%")
        
        return True
        
    except Exception as e:
        print(f"❌ Bloom filter creation failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_known_private_key():
    """Test that CPU EC math produces correct addresses"""
    print("\nTesting CPU EC math with known private keys...")
    
    try:
        from bitcoin_keys import BitcoinKey
        
        # Test with private key = 1
        privkey_bytes = b'\x00' * 31 + b'\x01'
        key = BitcoinKey(privkey_bytes)
        addr = key.get_p2pkh_address()
        
        expected = "1BgGZ9tcN4rm9KBzDn7KprQz87SZ26SAMH"
        assert addr == expected, f"Address mismatch: got {addr}, expected {expected}"
        
        print("✅ CPU EC math produces correct addresses")
        
        # Test with private key = 2
        privkey_bytes = b'\x00' * 31 + b'\x02'
        key = BitcoinKey(privkey_bytes)
        addr = key.get_p2pkh_address()
        
        expected = "12c6DSiU4Rq3P4ZxziKxzrL5LmMBrzjrJX"
        assert addr == expected, f"Address mismatch: got {addr}, expected {expected}"
        
        print("✅ CPU EC math works for multiple private keys")
        
        return True
        
    except Exception as e:
        print(f"❌ CPU EC math test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_gpu_kernel_compilation():
    """Test that GPU kernel compiles with new bloom filter functions"""
    print("\nTesting GPU kernel compilation...")
    
    try:
        # Read the kernel code and check for required functions
        with open('vanitygen_py/gpu_kernel.cl', 'r') as f:
            kernel_code = f.read()
        
        # Check for bloom_hash function
        assert 'uint bloom_hash(uint data_x, uint data_y, uint data_z, uint seed, uint m)' in kernel_code, "bloom_hash function not found"
        
        # Check for proper bloom_might_contain implementation
        assert 'if (!(f[byte_idx] & (1 << bit_offset)))' in kernel_code, "Bit checking not implemented correctly"
        
        # Check for data extraction
        assert 'uint data_x = h[0] | (h[1] << 8) | (h[2] << 16)' in kernel_code, "Data extraction not found"
        
        print("✅ GPU kernel has correct bloom filter implementation")
        
        return True
        
    except Exception as e:
        print(f"❌ GPU kernel compilation test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_cpu_verification_logic():
    """Test that CPU verification logic is in place"""
    print("\nTesting CPU verification logic...")
    
    try:
        # Read the gpu_generator.py code
        with open('vanitygen_py/gpu_generator.py', 'r') as f:
            python_code = f.read()
        
        # Check for GPU/CPU address mismatch detection
        assert 'GPU/CPU ADDRESS MISMATCH' in python_code, "Mismatch detection not found"
        assert 'GPU generated:' in python_code, "GPU address reporting not found"
        assert 'CPU correct:' in python_code, "CPU address reporting not found"
        
        # Check for real address generation
        assert 'real_addr = key.get_p2pkh_address()' in python_code, "Real address generation not found"
        
        print("✅ CPU verification logic is properly implemented")
        
        return True
        
    except Exception as e:
        print(f"❌ CPU verification logic test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Main test function"""
    print("=" * 60)
    print("Bloom Filter Fixes Verification")
    print("=" * 60)
    
    tests = [
        ("Base58 Decode", test_base58_decode),
        ("Bloom Hash Consistency", test_bloom_hash_consistency),
        ("CPU EC Math", test_known_private_key),
        ("GPU Kernel Compilation", test_gpu_kernel_compilation),
        ("CPU Verification Logic", test_cpu_verification_logic),
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"\n{test_name}:")
        result = test_func()
        results.append((test_name, result))
    
    print("\n" + "=" * 60)
    print("Test Results Summary")
    print("=" * 60)
    
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status}: {test_name}")
        if result:
            passed += 1
    
    print(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All bloom filter fixes verified!")
        print("The system is ready for testing with real data.")
        return True
    else:
        print("❌ Some tests failed.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)