#!/usr/bin/env python3
"""
Demonstration of the network address encoding issue and fix.

This script shows how the same scriptPubKey can produce different addresses
depending on the Bitcoin network (mainnet, testnet, regtest, signet).
"""

from vanitygen_py.balance_checker import BalanceChecker, NETWORKS, detect_network_from_path

def demonstrate_network_encoding():
    """Demonstrate address encoding for different networks."""
    
    print("=" * 80)
    print("BITCOIN CHAINSTATE ADDRESS DERIVATION - NETWORK ENCODING DEMONSTRATION")
    print("=" * 80)
    print()
    
    # Create a checker instance
    checker = BalanceChecker()
    
    # Example P2PKH script
    print("P2PKH Address Encoding Example")
    print("-" * 80)
    pubkey_hash = b'\x00\x01\x02\x03\x04\x05\x06\x07\x08\x09\x0a\x0b\x0c\x0d\x0e\x0f\x10\x11\x12\x13'
    p2pkh_script = b'\x76\xa9\x14' + pubkey_hash + b'\x88\xac'
    
    print(f"ScriptPubKey (P2PKH): {p2pkh_script.hex()}")
    print(f"Pubkey hash: {pubkey_hash.hex()}")
    print()
    
    for network in ['mainnet', 'testnet', 'regtest', 'signet']:
        addr = checker._extract_address_from_script(p2pkh_script, network=network)
        config = NETWORKS[network]
        print(f"  {network:10s}: {addr:35s} (version: 0x{config['p2pkh_version']:02x})")
    
    print()
    
    # Example P2SH script
    print("P2SH Address Encoding Example")
    print("-" * 80)
    script_hash = b'\x00\x01\x02\x03\x04\x05\x06\x07\x08\x09\x0a\x0b\x0c\x0d\x0e\x0f\x10\x11\x12\x13'
    p2sh_script = b'\xa9\x14' + script_hash + b'\x87'
    
    print(f"ScriptPubKey (P2SH): {p2sh_script.hex()}")
    print(f"Script hash: {script_hash.hex()}")
    print()
    
    for network in ['mainnet', 'testnet', 'regtest', 'signet']:
        addr = checker._extract_address_from_script(p2sh_script, network=network)
        config = NETWORKS[network]
        print(f"  {network:10s}: {addr:35s} (version: 0x{config['p2sh_version']:02x})")
    
    print()
    
    # Example witness script
    print("Witness Address Encoding Example (P2WPKH)")
    print("-" * 80)
    witness_program = b'\x00\x01\x02\x03\x04\x05\x06\x07\x08\x09\x0a\x0b\x0c\x0d\x0e\x0f\x10\x11\x12\x13'
    p2wpkh_script = b'\x00\x14' + witness_program
    
    print(f"ScriptPubKey (P2WPKH): {p2wpkh_script.hex()}")
    print(f"Witness program: {witness_program.hex()}")
    print()
    
    for network in ['mainnet', 'testnet', 'regtest', 'signet']:
        addr = checker._extract_address_from_script(p2wpkh_script, network=network)
        config = NETWORKS[network]
        addr_display = addr if addr else "ERROR: None"
        print(f"  {network:10s}: {addr_display:50s} (hrp: {config['bech32_hrp']})")
    
    print()
    
    # Demonstrate network detection
    print("Network Detection from Chainstate Paths")
    print("-" * 80)
    
    test_paths = [
        '/home/user/.bitcoin/chainstate',
        '/home/user/.bitcoin/testnet3/chainstate',
        '/home/user/.bitcoin/regtest/chainstate',
        '/home/user/.bitcoin/signet/chainstate',
        '/var/snap/bitcoin-core/common/.bitcoin/testnet3/chainstate',
    ]
    
    for path in test_paths:
        network = detect_network_from_path(path)
        print(f"  {path:65s} -> {network}")
    
    print()
    
    # Explain the issue
    print("THE ISSUE AND THE FIX")
    print("=" * 80)
    print()
    print("ISSUE:")
    print("  - The chainstate database contains scriptPubKeys, NOT addresses")
    print("  - Addresses are DERIVED from scriptPubKeys by encoding with network-specific")
    print("    parameters (version bytes for legacy, HRP for witness addresses)")
    print("  - The old code ALWAYS used mainnet parameters (0x00, 0x05, 'bc')")
    print("  - This meant testnet addresses would be incorrectly encoded as mainnet")
    print("    addresses, causing balance checks to fail!")
    print()
    print("FIX:")
    print("  - Added network detection from chainstate path")
    print("  - Added network parameter to _extract_address_from_script()")
    print("  - Support for all Bitcoin networks: mainnet, testnet, regtest, signet")
    print("  - Correct version bytes and HRP for each network")
    print()
    print("RESULT:")
    print("  - Same scriptPubKey now correctly encodes to different addresses")
    print("  - based on the network being used")
    print("  - Balance checking will work correctly for all networks!")
    print()
    print("=" * 80)

if __name__ == '__main__':
    demonstrate_network_encoding()
