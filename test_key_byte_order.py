#!/usr/bin/env python3
"""
Test to verify the byte ordering fix for GPU key generation
"""

import struct

def test_byte_extraction():
    """
    Test that the byte extraction pattern used in the fixed kernel
    produces the correct byte order for ECDSA keys.
    """
    
    print("=" * 80)
    print("Testing Byte Extraction Logic")
    print("=" * 80)
    
    # Sample bignum (8 uint32 words) representing a private key
    # Using a simple pattern to verify byte ordering
    k_words = [
        0x01020304,  # k.d[0]
        0x05060708,  # k.d[1]
        0x090A0B0C,  # k.d[2]
        0x0D0E0F10,  # k.d[3]
        0x11121314,  # k.d[4]
        0x15161718,  # k.d[5]
        0x191A1B1C,  # k.d[6]
        0x1D1E1F20,  # k.d[7]
    ]
    
    print("\n1. Input bignum (8 uint32 words):")
    for i, word in enumerate(k_words):
        print(f"   k.d[{i}] = 0x{word:08X}")
    
    # Method 1: OLD BROKEN METHOD (direct uint32 copy)
    print("\n2. OLD METHOD (broken) - Direct uint32 copy:")
    old_bytes = b''.join(struct.pack('<I', word) for word in k_words)
    print(f"   Bytes: {old_bytes.hex()}")
    
    # Method 2: NEW FIXED METHOD (byte extraction pattern)
    print("\n3. NEW METHOD (fixed) - Byte extraction pattern:")
    # Simulate: for(int i=0; i<32; i++) kd[i] = (k.d[i/4] >> ((i%4)*8)) & 0xff;
    new_bytes = bytearray(32)
    for i in range(32):
        word_idx = i // 4  # Which uint32 word
        byte_shift = (i % 4) * 8  # How many bits to shift
        byte_val = (k_words[word_idx] >> byte_shift) & 0xff
        new_bytes[i] = byte_val
    
    new_bytes = bytes(new_bytes)
    print(f"   Bytes: {new_bytes.hex()}")
    
    # Expected output (little-endian uint32 words, extracted byte by byte)
    # k.d[0] = 0x01020304 -> bytes: 04 03 02 01
    # k.d[1] = 0x05060708 -> bytes: 08 07 06 05
    # etc.
    expected = bytes([
        0x04, 0x03, 0x02, 0x01,  # k.d[0]
        0x08, 0x07, 0x06, 0x05,  # k.d[1]
        0x0C, 0x0B, 0x0A, 0x09,  # k.d[2]
        0x10, 0x0F, 0x0E, 0x0D,  # k.d[3]
        0x14, 0x13, 0x12, 0x11,  # k.d[4]
        0x18, 0x17, 0x16, 0x15,  # k.d[5]
        0x1C, 0x1B, 0x1A, 0x19,  # k.d[6]
        0x20, 0x1F, 0x1E, 0x1D,  # k.d[7]
    ])
    
    print(f"\n4. Expected bytes:")
    print(f"   Bytes: {expected.hex()}")
    
    # Verify
    print("\n5. Verification:")
    if new_bytes == expected:
        print("   ✓ NEW METHOD produces CORRECT byte order")
    else:
        print("   ✗ NEW METHOD byte order mismatch!")
        return False
    
    if old_bytes == expected:
        print("   ✗ OLD METHOD produces CORRECT byte order (unexpected!)")
        return False
    else:
        print("   ✓ OLD METHOD produces INCORRECT byte order (as expected)")
    
    # Test with ECDSA library
    print("\n6. Testing with ECDSA library:")
    try:
        import ecdsa
        
        # Try to create signing key with old method (should fail for some keys)
        print("   Testing OLD method bytes...")
        try:
            key_old = ecdsa.SigningKey.from_string(old_bytes, curve=ecdsa.SECP256k1)
            print("   ⚠ OLD method: Key created (might work for some patterns)")
        except Exception as e:
            print(f"   ✓ OLD method: Failed as expected ({e.__class__.__name__})")
        
        # Try to create signing key with new method
        print("   Testing NEW method bytes...")
        try:
            key_new = ecdsa.SigningKey.from_string(new_bytes, curve=ecdsa.SECP256k1)
            print("   ✓ NEW method: Key created successfully")
            
            # Verify the key is valid
            pubkey = key_new.get_verifying_key()
            print(f"   ✓ Public key: {pubkey.to_string().hex()[:32]}...")
            
        except Exception as e:
            print(f"   ✗ NEW method: Failed ({e})")
            return False
            
    except ImportError:
        print("   ⚠ ecdsa library not available, skipping ECDSA test")
    
    print("\n" + "=" * 80)
    print("✓ ALL TESTS PASSED - Byte extraction fix is correct!")
    print("=" * 80)
    
    return True

if __name__ == "__main__":
    import sys
    try:
        success = test_byte_extraction()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\nERROR: Test failed with exception: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
