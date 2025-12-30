#!/usr/bin/env python3
"""
Test to verify that hash160 calculations match expected values.
This ensures that EC verification uses hash160 correctly.
"""

from vanitygen_py.bitcoin_keys import BitcoinKey
from vanitygen_py.crypto_utils import hash160, base58_decode

def test_hash160_from_private_key():
    """Test hash160 calculation from a known private key"""
    # Test with the private key from the user's example
    # KzQnKhjVZs79QbY5iqPKmo8Nj1dK7iEwnuDBmXXkRriFVDJnjNxt
    # Expected address: 1E7rcojs1o5TvdF8AT3JfaBeXWAnukt41f
    # Expected hash160: 8fe58ca786d7c81740624fb281cec58b8de819c2
    
    # WIF private key from user's example
    wif = "KzQnKhjVZs79QbY5iqPKmo8Nj1dK7iEwnuDBmXXkRriFVDJnjNxt"
    
    # Decode WIF to get private key bytes
    # WIF format: version(1) + privkey(32) + [compressed_flag(1)] + checksum(4)
    import base58
    decoded = base58.b58decode(wif)
    # For compressed WIF (starts with K or L), format is: 0x80 + privkey(32) + 0x01 + checksum(4) = 38 bytes
    privkey_bytes = decoded[1:33]  # Skip version byte, get 32-byte private key
    
    # Create key object
    key = BitcoinKey(privkey_bytes)
    
    # Get public key and hash160
    pubkey = key.get_public_key(compressed=True)
    hash160_value = key.get_hash160(compressed=True)
    
    # Get address
    address = key.get_p2pkh_address(compressed=True)
    
    print("Test 1: Known private key from user example")
    print(f"WIF: {wif}")
    print(f"Address: {address}")
    print(f"Expected Address: 1E7rcojs1o5TvdF8AT3JfaBeXWAnukt41f")
    print(f"Public Key: {pubkey.hex()}")
    print(f"Hash160: {hash160_value.hex()}")
    print(f"Expected Hash160: 8fe58ca786d7c81740624fb281cec58b8de819c2")
    print()
    
    # Verify address matches
    assert address == "1E7rcojs1o5TvdF8AT3JfaBeXWAnukt41f", f"Address mismatch: {address}"
    
    # Verify hash160 matches
    expected_hash160 = "8fe58ca786d7c81740624fb281cec58b8de819c2"
    assert hash160_value.hex() == expected_hash160, f"Hash160 mismatch: {hash160_value.hex()}"
    
    print("✓ Test 1 PASSED: Hash160 matches expected value")
    print()

def test_hash160_from_second_example():
    """Test hash160 from second user example"""
    # Address: 1uvbg5oMK43ckB1CU5h9RqZ7Bt99HppAJ
    # Private Key: KxoJmKxj974fEkP2a82JuAwPkdS2GcYgKqkjWSVEmn4w8Erbm1AY
    # Public Key: 022ce763bac3c7011f5856361623a2c815631640f762dde4b2043c41f47916dd0f
    
    wif = "KxoJmKxj974fEkP2a82JuAwPkdS2GcYgKqkjWSVEmn4w8Erbm1AY"
    
    # Decode WIF
    import base58
    decoded = base58.b58decode(wif)
    privkey_bytes = decoded[1:33]  # Skip version, get 32-byte private key
    
    # Create key
    key = BitcoinKey(privkey_bytes)
    
    # Get values
    pubkey = key.get_public_key(compressed=True)
    hash160_value = key.get_hash160(compressed=True)
    address = key.get_p2pkh_address(compressed=True)
    
    print("Test 2: Second example from user")
    print(f"WIF: {wif}")
    print(f"Address: {address}")
    print(f"Expected Address: 1uvbg5oMK43ckB1CU5h9RqZ7Bt99HppAJ")
    print(f"Public Key: {pubkey.hex()}")
    print(f"Expected Public Key: 022ce763bac3c7011f5856361623a2c815631640f762dde4b2043c41f47916dd0f")
    print(f"Hash160: {hash160_value.hex()}")
    print()
    
    # Verify values
    assert address == "1uvbg5oMK43ckB1CU5h9RqZ7Bt99HppAJ", f"Address mismatch: {address}"
    assert pubkey.hex() == "022ce763bac3c7011f5856361623a2c815631640f762dde4b2043c41f47916dd0f", f"Public key mismatch: {pubkey.hex()}"
    
    print("✓ Test 2 PASSED: Public key and address match expected values")
    print()

def test_address_to_hash160_extraction():
    """Test extracting hash160 from an address"""
    address = "1E7rcojs1o5TvdF8AT3JfaBeXWAnukt41f"
    expected_hash160 = "8fe58ca786d7c81740624fb281cec58b8de819c2"
    
    # Decode the address to extract hash160
    decoded = base58_decode(address)
    # Skip version byte (1 byte), take hash160 (20 bytes), ignore checksum (4 bytes)
    extracted_hash160 = decoded[1:21]
    
    print("Test 3: Extract hash160 from address")
    print(f"Address: {address}")
    print(f"Extracted Hash160: {extracted_hash160.hex()}")
    print(f"Expected Hash160: {expected_hash160}")
    print()
    
    assert extracted_hash160.hex() == expected_hash160, f"Hash160 mismatch: {extracted_hash160.hex()}"
    
    print("✓ Test 3 PASSED: Hash160 correctly extracted from address")
    print()

if __name__ == "__main__":
    print("=" * 80)
    print("Testing Hash160 Verification")
    print("=" * 80)
    print()
    
    try:
        test_hash160_from_private_key()
        test_hash160_from_second_example()
        test_address_to_hash160_extraction()
        
        print("=" * 80)
        print("✓ ALL TESTS PASSED")
        print("=" * 80)
        print()
        print("Summary:")
        print("- Hash160 calculations are correct")
        print("- Public keys are correctly derived")
        print("- Addresses are correctly generated")
        print("- EC verification should use hash160 (20 bytes) instead of full public key (33/65 bytes)")
        print()
        
    except Exception as e:
        print(f"✗ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        exit(1)
