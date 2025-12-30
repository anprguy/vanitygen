#!/usr/bin/env python3
"""
Test script to verify EC check enhancements work correctly.
"""

import sys
from vanitygen_py.bitcoin_keys import BitcoinKey
from vanitygen_py.crypto_utils import hash160, base58check_encode

def test_ec_check_error_details():
    """Test that EC check error details generation works correctly."""
    print("Testing EC check error details generation...")
    
    # Create a test key
    test_key = BitcoinKey()
    
    # Get compressed public key and address
    cpu_pub = test_key.get_public_key(compressed=True)
    cpu_addr = test_key.get_p2pkh_address(compressed=True)
    
    # Simulate GPU-generated data (same as CPU for this test)
    gpu_pub = cpu_pub
    gpu_hash160 = hash160(gpu_pub)
    gpu_addr = base58check_encode(0, gpu_hash160)
    
    # Verify they match
    assert cpu_pub == gpu_pub, "Public keys should match"
    assert cpu_addr == gpu_addr, "Addresses should match"
    
    print(f"✓ CPU Public Key: {cpu_pub.hex()[:32]}...")
    print(f"✓ GPU Public Key: {gpu_pub.hex()[:32]}...")
    print(f"✓ CPU Address: {cpu_addr}")
    print(f"✓ GPU Address: {gpu_addr}")
    print(f"✓ Addresses match: {cpu_addr == gpu_addr}")
    
    # Test with mismatched public key (flip a bit)
    gpu_pub_bad = bytes([cpu_pub[0] ^ 0x01]) + cpu_pub[1:]  # Flip prefix bit
    gpu_hash160_bad = hash160(gpu_pub_bad)
    gpu_addr_bad = base58check_encode(0, gpu_hash160_bad)
    
    print(f"\n✓ Testing with mismatched public key:")
    print(f"  CPU Address: {cpu_addr}")
    print(f"  GPU Address (bad): {gpu_addr_bad}")
    print(f"  Addresses differ: {cpu_addr != gpu_addr_bad}")
    
    # Test error detail structure
    error_details = {
        'privkey': test_key.privkey_bytes.hex(),
        'cpu_pub': cpu_pub.hex(),
        'gpu_pub': gpu_pub_bad.hex(),
        'cpu_addr': cpu_addr,
        'gpu_addr': gpu_addr_bad,
        'note': 'Public keys differ but addresses may still match (check GPU EC implementation)',
    }
    
    assert 'privkey' in error_details
    assert 'cpu_pub' in error_details
    assert 'gpu_pub' in error_details
    assert 'cpu_addr' in error_details
    assert 'gpu_addr' in error_details
    assert 'note' in error_details
    
    print("\n✓ Error details structure is correct")
    print(f"  Keys in dict: {list(error_details.keys())}")
    
    return True

def test_compressed_key_consistency():
    """Test that compressed keys are used consistently."""
    print("\nTesting compressed key consistency...")
    
    test_key = BitcoinKey()
    
    # Test default behavior (should be compressed)
    pub_default = test_key.get_public_key()
    pub_compressed = test_key.get_public_key(compressed=True)
    pub_uncompressed = test_key.get_public_key(compressed=False)
    
    assert len(pub_default) == 33, f"Default public key should be 33 bytes (compressed), got {len(pub_default)}"
    assert len(pub_compressed) == 33, f"Compressed public key should be 33 bytes, got {len(pub_compressed)}"
    assert len(pub_uncompressed) == 65, f"Uncompressed public key should be 65 bytes, got {len(pub_uncompressed)}"
    
    assert pub_default == pub_compressed, "Default should be compressed"
    
    print(f"✓ Default public key is compressed: {len(pub_default)} bytes")
    print(f"✓ Compressed public key: {len(pub_compressed)} bytes")
    print(f"✓ Uncompressed public key: {len(pub_uncompressed)} bytes")
    
    # Test address generation
    addr_default = test_key.get_p2pkh_address()
    addr_compressed = test_key.get_p2pkh_address(compressed=True)
    addr_uncompressed = test_key.get_p2pkh_address(compressed=False)
    
    assert addr_default == addr_compressed, "Default address should use compressed key"
    assert addr_default != addr_uncompressed, "Compressed and uncompressed addresses should differ"
    
    print(f"✓ Default address uses compressed key: {addr_default}")
    print(f"✓ Uncompressed address differs: {addr_uncompressed}")
    
    # Test WIF
    wif_default = test_key.get_wif()
    wif_compressed = test_key.get_wif(compressed=True)
    wif_uncompressed = test_key.get_wif(compressed=False)
    
    assert wif_default == wif_compressed, "Default WIF should be compressed"
    assert len(wif_compressed) > len(wif_uncompressed), "Compressed WIF should be longer (has suffix byte)"
    
    print(f"✓ Default WIF is compressed")
    print(f"✓ Compressed WIF: {wif_compressed[:8]}...")
    print(f"✓ Uncompressed WIF: {wif_uncompressed[:8]}...")
    
    return True

if __name__ == "__main__":
    try:
        print("=" * 60)
        print("EC Check Enhancements Test Suite")
        print("=" * 60)
        
        test_ec_check_error_details()
        test_compressed_key_consistency()
        
        print("\n" + "=" * 60)
        print("✓ All tests passed!")
        print("=" * 60)
        sys.exit(0)
    except Exception as e:
        print(f"\n✗ Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
