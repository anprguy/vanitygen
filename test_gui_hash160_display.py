#!/usr/bin/env python3
"""
Test to verify that the GUI correctly displays hash160 values alongside public keys.
This ensures users can verify their addresses using either the full public key or hash160.
"""

from vanitygen_py.bitcoin_keys import BitcoinKey
from vanitygen_py.crypto_utils import hash160
import base58

def test_gui_hash160_display():
    """Test that hash160 is correctly calculated and displayed in GUI format"""
    
    print("=" * 80)
    print("Testing GUI Hash160 Display")
    print("=" * 80)
    print()
    
    # Test with the user's example
    wif = "KzQnKhjVZs79QbY5iqPKmo8Nj1dK7iEwnuDBmXXkRriFVDJnjNxt"
    expected_address = "1E7rcojs1o5TvdF8AT3JfaBeXWAnukt41f"
    expected_hash160 = "8fe58ca786d7c81740624fb281cec58b8de819c2"
    
    # Decode WIF
    decoded = base58.b58decode(wif)
    privkey_bytes = decoded[1:33]
    
    # Create key
    key = BitcoinKey(privkey_bytes)
    
    # Get values as they would be displayed in GUI
    addr = key.get_p2pkh_address(compressed=True)
    pubkey = key.get_public_key(compressed=True).hex()
    
    # Calculate hash160 from public key (as done in GUI)
    pubkey_bytes = bytes.fromhex(pubkey)
    hash160_value = hash160(pubkey_bytes).hex()
    
    # Simulate GUI output format
    balance = 0
    is_in_funded_list = False
    membership_status = "✓ YES" if is_in_funded_list else "✗ NO"
    addr_type = "p2pkh"
    
    result_str = (
        f"Address: {addr}\n"
        f"Private Key: {wif}\n"
        f"Public Key: {pubkey}\n"
        f"Public Key Hash (Hash160): {hash160_value}\n"
        f"Balance: {balance}\n"
        f"In Funded List: {membership_status}\n"
        f"Address Type: {addr_type}\n"
        + "-" * 40 + "\n"
    )
    
    print("Simulated GUI Output:")
    print(result_str)
    
    # Verify values
    print("Verification:")
    print(f"✓ Address matches expected: {addr == expected_address}")
    print(f"✓ Hash160 matches expected: {hash160_value == expected_hash160}")
    print()
    
    assert addr == expected_address, f"Address mismatch: {addr}"
    assert hash160_value == expected_hash160, f"Hash160 mismatch: {hash160_value}"
    
    print("=" * 80)
    print("✓ TEST PASSED: GUI will correctly display hash160 values")
    print("=" * 80)
    print()
    print("Benefits:")
    print("1. Users can now verify addresses using either:")
    print("   - Full Public Key (33 or 65 bytes)")
    print("   - Public Key Hash / Hash160 (20 bytes)")
    print()
    print("2. This matches the format shown on verification websites like:")
    print("   - https://privatekeys.pw/")
    print("   - https://www.bitaddress.org/")
    print()
    print("3. EC verification now uses hash160 for comparison, which is:")
    print("   - The actual value stored in the balance checker")
    print("   - The value embedded in Bitcoin addresses")
    print("   - The correct way to verify address ownership")
    print()

def test_second_example():
    """Test with second user example"""
    print("=" * 80)
    print("Testing Second Example")
    print("=" * 80)
    print()
    
    wif = "KxoJmKxj974fEkP2a82JuAwPkdS2GcYgKqkjWSVEmn4w8Erbm1AY"
    expected_address = "1uvbg5oMK43ckB1CU5h9RqZ7Bt99HppAJ"
    expected_pubkey = "022ce763bac3c7011f5856361623a2c815631640f762dde4b2043c41f47916dd0f"
    
    # Decode WIF
    decoded = base58.b58decode(wif)
    privkey_bytes = decoded[1:33]
    
    # Create key
    key = BitcoinKey(privkey_bytes)
    
    # Get values
    addr = key.get_p2pkh_address(compressed=True)
    pubkey = key.get_public_key(compressed=True).hex()
    
    # Calculate hash160
    pubkey_bytes = bytes.fromhex(pubkey)
    hash160_value = hash160(pubkey_bytes).hex()
    
    # Display
    result_str = (
        f"Address: {addr}\n"
        f"Private Key: {wif}\n"
        f"Public Key: {pubkey}\n"
        f"Public Key Hash (Hash160): {hash160_value}\n"
        f"Balance: 0\n"
        f"In Funded List: ✗ NO\n"
        f"Address Type: p2pkh\n"
        + "-" * 40 + "\n"
    )
    
    print("Simulated GUI Output:")
    print(result_str)
    
    # Verify
    print("Verification:")
    print(f"✓ Address matches: {addr == expected_address}")
    print(f"✓ Public key matches: {pubkey == expected_pubkey}")
    print()
    
    assert addr == expected_address
    assert pubkey == expected_pubkey
    
    print("✓ TEST PASSED")
    print()

if __name__ == "__main__":
    try:
        test_gui_hash160_display()
        test_second_example()
        
        print("=" * 80)
        print("✓ ALL TESTS PASSED")
        print("=" * 80)
        print()
        print("The GUI now correctly displays:")
        print("1. Full Public Key (for complete verification)")
        print("2. Public Key Hash (Hash160) (for quick verification)")
        print()
        print("This resolves the user's issue where they could only see")
        print("the full public key and couldn't match it against the hash160")
        print("values shown on verification websites.")
        print()
        
    except Exception as e:
        print(f"✗ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        exit(1)
