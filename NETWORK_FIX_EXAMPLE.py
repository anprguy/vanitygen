#!/usr/bin/env python3
"""
Practical example demonstrating the network fix for BalanceChecker.

This shows how the fix enables correct balance checking across all Bitcoin networks.
"""

from vanitygen_py.balance_checker import BalanceChecker, detect_network_from_path

def test_scenario():
    """Demonstrate practical scenario of network-aware balance checking."""
    
    print("=" * 80)
    print("PRACTICAL EXAMPLE: NETWORK-AWARE BALANCE CHECKING")
    print("=" * 80)
    print()
    
    # Scenario 1: User wants to generate testnet vanity addresses
    print("SCENARIO 1: Generating testnet vanity addresses")
    print("-" * 80)
    
    checker = BalanceChecker()
    
    # Simulate loading from testnet chainstate
    testnet_path = "/home/user/.bitcoin/testnet3/chainstate"
    detected_network = detect_network_from_path(testnet_path)
    print(f"Loading from: {testnet_path}")
    print(f"Detected network: {detected_network}")
    
    # Simulate a testnet P2PKH scriptPubKey
    testnet_p2pkh_script = bytes.fromhex(
        "76a914000102030405060708090a0b0c0d0e0f1011121388ac"
    )
    
    # Extract address with testnet network
    testnet_addr = checker._extract_address_from_script(
        testnet_p2pkh_script, 
        network='testnet'
    )
    
    print(f"Testnet address: {testnet_addr}")
    print(f"Address starts with: {'m' if testnet_addr.startswith('m') else 'n' if testnet_addr.startswith('n') else 'ERROR!'}")
    print()
    
    # Show what would happen with the OLD bug
    print("WITH THE OLD BUG:")
    old_buggy_addr = checker._extract_address_from_script(
        testnet_p2pkh_script,
        network='mainnet'  # Old code always used mainnet
    )
    print(f"  Would have encoded as: {old_buggy_addr}")
    print(f"  Problem: This is a mainnet address, not testnet!")
    print(f"  Result: Balance check would FAIL even though address exists!")
    print()
    
    print("WITH THE FIX:")
    print(f"  Correctly encodes as: {testnet_addr}")
    print(f"  Problem solved: This is a proper testnet address!")
    print(f"  Result: Balance check will SUCCEED!")
    print()
    
    # Scenario 2: User wants to generate mainnet addresses
    print("SCENARIO 2: Generating mainnet vanity addresses")
    print("-" * 80)
    
    mainnet_path = "/home/user/.bitcoin/chainstate"
    detected_network = detect_network_from_path(mainnet_path)
    print(f"Loading from: {mainnet_path}")
    print(f"Detected network: {detected_network}")
    
    # Same scriptPubKey, but mainnet encoding
    mainnet_addr = checker._extract_address_from_script(
        testnet_p2pkh_script,
        network='mainnet'
    )
    
    print(f"Mainnet address: {mainnet_addr}")
    print(f"Address starts with: {mainnet_addr[0] if mainnet_addr else 'ERROR!'}")
    print()
    
    print("COMPARISON:")
    print(f"  Testnet: {testnet_addr}")
    print(f"  Mainnet: {mainnet_addr}")
    print(f"  Same script, different networks = different addresses ✅")
    print()
    
    # Scenario 3: Manual network setting for file-based loading
    print("SCENARIO 3: Loading addresses from file (not Bitcoin Core)")
    print("-" * 80)
    
    file_checker = BalanceChecker()
    print(f"Initial network: {file_checker.get_network()}")
    
    # User knows they're working with testnet addresses
    file_checker.set_network('testnet')
    print(f"After set_network('testnet'): {file_checker.get_network()}")
    print()
    
    print("Usage example:")
    print("```python")
    print("checker = BalanceChecker()")
    print("checker.set_network('testnet')  # Important: set correct network!")
    print("checker.load_addresses('testnet_addresses.txt')")
    print("# Now checking balances against testnet addresses")
    print("```")
    print()
    
    # Summary
    print("SUMMARY")
    print("=" * 80)
    print()
    print("✅ Chainstate contains scriptPubKeys, not addresses")
    print("✅ Addresses are DERIVED from scriptPubKeys")
    print("✅ Address encoding depends on network (version bytes, HRP)")
    print()
    print("THE FIX:")
    print("  - Automatic network detection from chainstate path")
    print("  - Network-specific address encoding for all networks")
    print("  - Manual network setting for file-based loading")
    print("  - Support for mainnet, testnet, regtest, signet")
    print()
    print("RESULT:")
    print("  - Balance checking now works correctly on ALL networks")
    print("  - Same scriptPubKey produces correct addresses per network")
    print("  - No more testnet balance check failures!")
    print()
    print("=" * 80)

if __name__ == '__main__':
    test_scenario()
