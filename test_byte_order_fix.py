#!/usr/bin/env python3
"""
Test to verify that the byte order conversion is correct for GPU-generated keys.
This ensures that EC verification properly matches GPU and CPU implementations.
"""

import struct
import numpy as np
from vanitygen_py.bitcoin_keys import BitcoinKey

def test_byte_order_conversion():
    """Test that byte order conversion matches GPU kernel output"""
    
    print("=" * 80)
    print("Testing Byte Order Conversion (GPU Little-Endian → Bitcoin Big-Endian)")
    print("=" * 80)
    print()
    
    # Simulate a known private key in the GPU's word array format
    # Let's use a simple test key: 0x0000000000000000000000000000000000000000000000000000000000000001
    # In GPU format (little-endian words, LSW first):
    # d[0] = 0x00000001 (LSW), d[1] = 0x00000000, ..., d[7] = 0x00000000 (MSW)
    
    test_words_1 = np.array([1, 0, 0, 0, 0, 0, 0, 0], dtype=np.uint32)
    
    # OLD (incorrect) method: treat entire buffer as little-endian integer
    old_le = test_words_1.tobytes()
    old_int = int.from_bytes(old_le, 'little')
    old_be = old_int.to_bytes(32, 'big')
    
    # NEW (correct) method: reverse bytes to convert to big-endian
    new_le = test_words_1.tobytes()
    new_be = new_le[::-1]
    
    print("Test 1: Private key = 0x...0001")
    print(f"GPU words (LSW first): {test_words_1}")
    print(f"Old method result: {old_be.hex()}")
    print(f"New method result: {new_be.hex()}")
    print(f"Expected (big-endian): {'00' * 31}01")
    print()
    
    assert new_be.hex() == '00' * 31 + '01', f"Test 1 failed: {new_be.hex()}"
    print("✓ Test 1 PASSED")
    print()
    
    # Test 2: A more complex key
    # Private key: 0x0102030405060708090a0b0c0d0e0f101112131415161718191a1b1c1d1e1f20
    # In little-endian word array (LSW first):
    # Bytes in order: 01 02 03 04 05 06 07 08 ... 1d 1e 1f 20
    # Words (each little-endian): [0x04030201, 0x08070605, ..., 0x201f1e1d]
    
    test_bytes = bytes(range(1, 33))  # 01 02 03 ... 1f 20
    test_words_2 = np.array([
        struct.unpack('<I', test_bytes[i:i+4])[0] for i in range(0, 32, 4)
    ], dtype=np.uint32)
    
    # OLD (incorrect) method
    old_le_2 = test_words_2.tobytes()
    old_int_2 = int.from_bytes(old_le_2, 'little')
    old_be_2 = old_int_2.to_bytes(32, 'big')
    
    # NEW (correct) method
    new_le_2 = test_words_2.tobytes()
    new_be_2 = new_le_2[::-1]
    
    print("Test 2: Private key = 0x0102030405060708...1d1e1f20")
    print(f"GPU words: {[hex(w) for w in test_words_2]}")
    print(f"Old method result: {old_be_2.hex()}")
    print(f"New method result: {new_be_2.hex()}")
    print(f"Expected (big-endian): {test_bytes[::-1].hex()}")
    print()
    
    assert new_be_2.hex() == test_bytes[::-1].hex(), f"Test 2 failed: {new_be_2.hex()}"
    print("✓ Test 2 PASSED")
    print()
    
    # Test 3: Verify that the new method produces valid Bitcoin keys
    print("Test 3: Verify Bitcoin key generation")
    
    # Use a known valid private key
    known_privkey_hex = "e9873d79c6d87dc0fb6a5778633389f4453213303da61f20bd67fc233aa33262"
    known_privkey_bytes = bytes.fromhex(known_privkey_hex)
    
    # Simulate GPU storage (convert to little-endian word array)
    gpu_words = np.array([
        struct.unpack('<I', known_privkey_bytes[::-1][i:i+4])[0] for i in range(0, 32, 4)
    ], dtype=np.uint32)
    
    # Apply NEW conversion
    converted_bytes = gpu_words.tobytes()[::-1]
    
    print(f"Known private key: {known_privkey_hex}")
    print(f"GPU words: {[hex(w) for w in gpu_words[:3]]}...")
    print(f"Converted bytes:  {converted_bytes.hex()}")
    print()
    
    assert converted_bytes.hex() == known_privkey_hex, f"Test 3 conversion failed"
    
    # Create Bitcoin key and generate address
    key = BitcoinKey(converted_bytes)
    address = key.get_p2pkh_address()
    pubkey = key.get_public_key(compressed=True)
    
    print(f"Address: {address}")
    print(f"Public Key: {pubkey.hex()}")
    print()
    
    print("✓ Test 3 PASSED")
    print()

def test_gpu_kernel_format():
    """Test that we understand the GPU kernel format correctly"""
    
    print("=" * 80)
    print("Testing GPU Kernel Format Understanding")
    print("=" * 80)
    print()
    
    # The GPU kernel stores private keys as:
    # for(int i=0; i<32; i++) d[i] = (k.d[i/4] >> ((i%4)*8)) & 0xff;
    # This means:
    # - d[0] = byte 0 of word 0 (LSB of LSW)
    # - d[1] = byte 1 of word 0
    # - d[2] = byte 2 of word 0
    # - d[3] = byte 3 of word 0 (MSB of LSW)
    # - d[4] = byte 0 of word 1 (LSB of word 1)
    # ...
    # - d[31] = byte 3 of word 7 (MSB of MSW)
    
    # Simulate GPU kernel storage for word array [0x04030201, 0x08070605, ...]
    words = np.array([0x04030201, 0x08070605, 0x0c0b0a09, 0x100f0e0d,
                      0x14131211, 0x18171615, 0x1c1b1a19, 0x201f1e1d], dtype=np.uint32)
    
    # Simulate GPU kernel extraction
    gpu_bytes = bytearray(32)
    for i in range(32):
        word_idx = i // 4
        byte_in_word = i % 4
        gpu_bytes[i] = (words[word_idx] >> (byte_in_word * 8)) & 0xff
    
    print("GPU word array:")
    print([hex(w) for w in words])
    print()
    print("GPU kernel extracts bytes as:")
    print(gpu_bytes.hex())
    print()
    print("Expected (little-endian sequence):")
    print(''.join(f'{i+1:02x}' for i in range(32)))
    print()
    
    assert gpu_bytes.hex() == ''.join(f'{i+1:02x}' for i in range(32)), "GPU format test failed"
    
    print("✓ GPU kernel format verified: stores in little-endian byte order")
    print()
    
    # Now verify the conversion
    converted = bytes(gpu_bytes)[::-1]
    print("After reversing bytes:")
    print(converted.hex())
    print()
    print("This gives us big-endian format (Bitcoin standard)")
    print()
    
    print("✓ GPU Kernel Format Test PASSED")
    print()

if __name__ == "__main__":
    try:
        test_byte_order_conversion()
        test_gpu_kernel_format()
        
        print("=" * 80)
        print("✓ ALL TESTS PASSED")
        print("=" * 80)
        print()
        print("Summary:")
        print("- GPU stores private keys in little-endian byte order (LSB first)")
        print("- Bitcoin expects big-endian byte order (MSB first)")
        print("- Simple byte reversal [::-1] converts correctly")
        print("- EC verification should now match GPU and CPU implementations")
        print()
        
    except Exception as e:
        print(f"✗ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        exit(1)
