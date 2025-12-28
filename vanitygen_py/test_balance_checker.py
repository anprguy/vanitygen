#!/usr/bin/env python3
"""
Unit tests for the BalanceChecker class and Bitcoin Core LevelDB integration.
"""

import sys
import os
import unittest
from unittest.mock import Mock, MagicMock, patch
import tempfile

# Handle both module and direct execution
try:
    from .balance_checker import BalanceChecker, NETWORKS, detect_network_from_path
    from .bitcoin_keys import BitcoinKey
except ImportError:
    from balance_checker import BalanceChecker, NETWORKS, detect_network_from_path
    from bitcoin_keys import BitcoinKey


class TestBalanceChecker(unittest.TestCase):
    """Test cases for BalanceChecker class"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.checker = BalanceChecker()
    
    def tearDown(self):
        """Clean up after tests"""
        self.checker.close()
    
    def test_init(self):
        """Test BalanceChecker initialization"""
        self.assertIsNotNone(self.checker)
        self.assertFalse(self.checker.is_loaded)
        self.assertEqual(len(self.checker.funded_addresses), 0)
        self.assertEqual(len(self.checker.address_balances), 0)
    
    def test_debug_mode(self):
        """Test debug mode enable/disable"""
        # Initially disabled
        self.assertFalse(self.checker.debug_mode)
        
        # Enable debug mode
        self.checker.enable_debug(True)
        self.assertTrue(self.checker.debug_mode)
        
        # Disable debug mode
        self.checker.enable_debug(False)
        self.assertFalse(self.checker.debug_mode)
    
    def test_load_addresses_from_file(self):
        """Test loading addresses from a text file"""
        # Create a temporary file with test addresses
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as f:
            test_addresses = [
                "1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa",
                "3J98t1WpEZ73CNmYviecrnyiWrnqRhWNLy",
                "bc1qw508d6qejxtdg4y5r3zarvary0c5xw7kv8f3t4",
                "1BvBMSEYstWetqTFn5Au4m4GFg7xJaNVN2",
            ]
            for addr in test_addresses:
                f.write(addr + '\n')
            temp_file = f.name
        
        try:
            # Load addresses
            result = self.checker.load_addresses(temp_file)
            
            # Verify
            self.assertTrue(result)
            self.assertTrue(self.checker.is_loaded)
            self.assertEqual(len(self.checker.funded_addresses), len(test_addresses))
            
            # Verify all addresses are loaded
            for addr in test_addresses:
                self.assertIn(addr, self.checker.funded_addresses)
        finally:
            os.unlink(temp_file)
    
    def test_load_addresses_nonexistent_file(self):
        """Test loading from a non-existent file"""
        result = self.checker.load_addresses("/nonexistent/path/file.txt")
        self.assertFalse(result)
        self.assertFalse(self.checker.is_loaded)
    
    def test_check_balance_with_loaded_file(self):
        """Test balance checking with loaded address file"""
        # Create a temporary file
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as f:
            test_addresses = ["1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa"]
            f.write(test_addresses[0] + '\n')
            temp_file = f.name
        
        try:
            # Load addresses
            self.checker.load_addresses(temp_file)
            
            # Test balance check
            balance = self.checker.check_balance(test_addresses[0])
            self.assertEqual(balance, 1)  # Returns 1 for funded addresses in file mode
            
            # Test non-funded address
            balance = self.checker.check_balance("1BvBMSEYstWetqTFn5Au4m4GFg7xJaNVN2")
            self.assertEqual(balance, 0)
        finally:
            os.unlink(temp_file)
    
    def test_check_balance_no_data_loaded(self):
        """Test balance checking when no data is loaded"""
        balance = self.checker.check_balance("1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa")
        self.assertEqual(balance, 0)
    
    def test_get_status_not_loaded(self):
        """Test status message when not loaded"""
        status = self.checker.get_status()
        self.assertEqual(status, "Balance checking not active")
    
    def test_get_status_with_file(self):
        """Test status message when file is loaded"""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as f:
            f.write("1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa\n")
            temp_file = f.name
        
        try:
            self.checker.load_addresses(temp_file)
            status = self.checker.get_status()
            self.assertIn("1 funded addresses from file", status)
        finally:
            os.unlink(temp_file)
    
    def test_parse_compact_size(self):
        """Test compact size parsing"""
        # Test single byte
        data = bytes([0x42])
        size, offset = self.checker._parse_compact_size(data, 0)
        self.assertEqual(size, 0x42)
        self.assertEqual(offset, 1)
        
        # Test 0xfd prefix (2 bytes)
        data = bytes([0xfd, 0x34, 0x12])
        size, offset = self.checker._parse_compact_size(data, 0)
        self.assertEqual(size, 0x1234)
        self.assertEqual(offset, 3)
        
        # Test 0xfe prefix (4 bytes)
        data = bytes([0xfe, 0x78, 0x56, 0x34, 0x12])
        size, offset = self.checker._parse_compact_size(data, 0)
        self.assertEqual(size, 0x12345678)
        self.assertEqual(offset, 5)
    
    def test_decode_varint_amount(self):
        """Test varint amount decoding"""
        # Test single byte
        data = bytes([0x42])
        amount, offset = self.checker._decode_varint_amount(data, 0)
        self.assertEqual(amount, 0x42)
        
        # Test 0xfd prefix (2 bytes)
        data = bytes([0xfd, 0x34, 0x12])
        amount, offset = self.checker._decode_varint_amount(data, 0)
        self.assertEqual(amount, 0x1234)
        
        # Test 0xfe prefix (4 bytes)
        data = bytes([0xfe, 0x78, 0x56, 0x34, 0x12])
        amount, offset = self.checker._decode_varint_amount(data, 0)
        self.assertEqual(amount, 0x12345678)
    
    def test_extract_address_from_p2pkh_script(self):
        """Test address extraction from P2PKH script"""
        # P2PKH script: OP_DUP OP_HASH160 <hash> OP_EQUALVERIFY OP_CHECKSIG
        # Example: 76 a9 14 <20 byte hash> 88 ac
        pubkey_hash = b'\x00' * 20  # Example hash
        script = b'\x76\xa9\x14' + pubkey_hash + b'\x88\xac'
        
        address = self.checker._extract_address_from_script(script)
        self.assertIsNotNone(address)
        self.assertTrue(address.startswith('1'))
        # Base58Check encoded addresses are typically 25-34 characters
        self.assertGreaterEqual(len(address), 25)
        self.assertLessEqual(len(address), 34)
    
    def test_extract_address_from_p2sh_script(self):
        """Test address extraction from P2SH script"""
        # P2SH script: OP_HASH160 <hash> OP_EQUAL
        # Example: a9 14 <20 byte hash> 87
        script_hash = b'\x00' * 20  # Example hash
        script = b'\xa9\x14' + script_hash + b'\x87'
        
        address = self.checker._extract_address_from_script(script)
        self.assertIsNotNone(address)
        self.assertTrue(address.startswith('3'))
        self.assertEqual(len(address), 34)  # Standard P2SH address length
    
    def test_extract_address_from_p2wpkh_script(self):
        """Test address extraction from P2WPKH script"""
        # P2WPKH script: OP_0 <20-byte witness program>
        # Example: 00 14 <20 bytes>
        witness_program = b'\x00' * 20
        script = b'\x00\x14' + witness_program
        
        address = self.checker._extract_address_from_script(script)
        self.assertIsNotNone(address)
        self.assertTrue(address.startswith('bc1q'))
    
    def test_extract_address_from_p2wsh_script(self):
        """Test address extraction from P2WSH script"""
        # P2WSH script: OP_0 <32-byte witness program>
        # Example: 00 20 <32 bytes>
        witness_program = b'\x00' * 32
        script = b'\x00\x20' + witness_program
        
        address = self.checker._extract_address_from_script(script)
        self.assertIsNotNone(address)
        self.assertTrue(address.startswith('bc1q'))
    
    def test_extract_address_from_p2tr_script(self):
        """Test address extraction from P2TR script"""
        # P2TR script: OP_1 <32-byte witness program>
        # Example: 51 20 <32 bytes>
        witness_program = b'\x00' * 32
        script = b'\x51\x20' + witness_program
        
        address = self.checker._extract_address_from_script(script)
        self.assertIsNotNone(address)
        self.assertTrue(address.startswith('bc1p'))
    
    def test_extract_address_from_invalid_script(self):
        """Test address extraction from invalid script"""
        invalid_scripts = [
            b'',  # Empty
            b'\x00',  # Too short
            b'\xff' * 10,  # Invalid opcodes
            b'\x76\xa9' + b'\x00' * 20,  # Incomplete P2PKH
        ]
        
        for script in invalid_scripts:
            address = self.checker._extract_address_from_script(script)
            self.assertIsNone(address, f"Should return None for script: {script.hex()}")

    def test_network_address_encoding(self):
        """Test that different networks encode the same script to different addresses"""
        # Same P2PKH script should produce different addresses for different networks
        pubkey_hash = b'\x00' * 20
        script = b'\x76\xa9\x14' + pubkey_hash + b'\x88\xac'
        
        # Test mainnet (default)
        mainnet_address = self.checker._extract_address_from_script(script, network='mainnet')
        self.assertIsNotNone(mainnet_address)
        self.assertTrue(mainnet_address.startswith('1'))
        
        # Test testnet
        testnet_address = self.checker._extract_address_from_script(script, network='testnet')
        self.assertIsNotNone(testnet_address)
        self.assertTrue(testnet_address.startswith(('m', 'n')))
        
        # Verify they're different
        self.assertNotEqual(mainnet_address, testnet_address)
        
    def test_p2pkh_script_to_testnet_address(self):
        """Test that P2PKH script can be encoded to testnet address"""
        pubkey_hash = b'\x00' * 20
        script = b'\x76\xa9\x14' + pubkey_hash + b'\x88\xac'
        
        # Testnet P2PKH should use version 0x6f (111), producing 'm' or 'n' addresses
        # Current implementation uses version 0, producing '1' addresses (mainnet)
        mainnet_addr = self.checker._extract_address_from_script(script)
        self.assertTrue(mainnet_addr.startswith('1'),
                       f"Expected mainnet address starting with '1', got {mainnet_addr}")
        
        # This test documents the issue: we need network parameter support
        # For testnet, we'd expect: base58check_encode(0x6f, pubkey_hash)
        # which would produce an address like 'm... or n...'
    
    def test_p2sh_script_to_testnet_address(self):
        """Test that P2SH script can be encoded to testnet address"""
        script_hash = b'\x00' * 20
        script = b'\xa9\x14' + script_hash + b'\x87'
        
        # Testnet P2SH should use version 0xc4 (196), producing '2' addresses
        # Current implementation uses version 5, producing '3' addresses (mainnet)
        mainnet_addr = self.checker._extract_address_from_script(script)
        self.assertTrue(mainnet_addr.startswith('3'),
                       f"Expected mainnet address starting with '3', got {mainnet_addr}")
        
        # This test documents the issue: we need network parameter support
        # For testnet, we'd expect: base58check_encode(0xc4, script_hash)
        # which would produce an address like '2...'
    
    def test_witness_script_to_testnet_address(self):
        """Test that witness scripts can be encoded to testnet addresses"""
        witness_program = b'\x00' * 20
        script = b'\x00\x14' + witness_program
        
        # Mainnet witness addresses should use 'bc' prefix
        mainnet_addr = self.checker._extract_address_from_script(script, network='mainnet')
        self.assertTrue(mainnet_addr.startswith('bc1q'),
                       f"Expected mainnet address starting with 'bc1q', got {mainnet_addr}")
        
        # Testnet witness addresses should use 'tb' prefix
        testnet_addr = self.checker._extract_address_from_script(script, network='testnet')
        self.assertTrue(testnet_addr.startswith('tb1q'),
                       f"Expected testnet address starting with 'tb1q', got {testnet_addr}")
        
        # Regtest witness addresses should use 'bcrt' prefix
        regtest_addr = self.checker._extract_address_from_script(script, network='regtest')
        self.assertTrue(regtest_addr.startswith('bcrt1q'),
                       f"Expected regtest address starting with 'bcrt1q', got {regtest_addr}")
    
    def test_detect_network_from_path(self):
        """Test network detection from chainstate paths"""
        # Test mainnet paths (default)
        self.assertEqual(detect_network_from_path('/home/user/.bitcoin/chainstate'), 'mainnet')
        self.assertEqual(detect_network_from_path('/var/lib/bitcoin/chainstate'), 'mainnet')
        
        # Test testnet paths
        self.assertEqual(detect_network_from_path('/home/user/.bitcoin/testnet3/chainstate'), 'testnet')
        self.assertEqual(detect_network_from_path('/home/user/.bitcoin/testnet/chainstate'), 'testnet')
        self.assertEqual(detect_network_from_path('/var/snap/bitcoin-core/common/.bitcoin/testnet3/chainstate'), 'testnet')
        
        # Test regtest paths
        self.assertEqual(detect_network_from_path('/home/user/.bitcoin/regtest/chainstate'), 'regtest')
        
        # Test signet paths
        self.assertEqual(detect_network_from_path('/home/user/.bitcoin/signet/chainstate'), 'signet')
    
    def test_all_networks_p2sh_addresses(self):
        """Test P2SH addresses for all networks"""
        script_hash = b'\x00' * 20
        script = b'\xa9\x14' + script_hash + b'\x87'
        
        # Mainnet P2SH addresses start with '3'
        mainnet_addr = self.checker._extract_address_from_script(script, network='mainnet')
        self.assertTrue(mainnet_addr.startswith('3'))
        
        # Testnet P2SH addresses start with '2'
        testnet_addr = self.checker._extract_address_from_script(script, network='testnet')
        self.assertTrue(testnet_addr.startswith('2'))
        
        # Regtest P2SH addresses also start with '2'
        regtest_addr = self.checker._extract_address_from_script(script, network='regtest')
        self.assertTrue(regtest_addr.startswith('2'))
        
        # Signet P2SH addresses also start with '2'
        signet_addr = self.checker._extract_address_from_script(script, network='signet')
        self.assertTrue(signet_addr.startswith('2'))
    
    def test_networks_config(self):
        """Test that network configurations are correct"""
        # Mainnet
        self.assertEqual(NETWORKS['mainnet']['p2pkh_version'], 0x00)
        self.assertEqual(NETWORKS['mainnet']['p2sh_version'], 0x05)
        self.assertEqual(NETWORKS['mainnet']['bech32_hrp'], 'bc')
        
        # Testnet
        self.assertEqual(NETWORKS['testnet']['p2pkh_version'], 0x6f)
        self.assertEqual(NETWORKS['testnet']['p2sh_version'], 0xc4)
        self.assertEqual(NETWORKS['testnet']['bech32_hrp'], 'tb')
        
        # Regtest
        self.assertEqual(NETWORKS['regtest']['p2pkh_version'], 0x6f)
        self.assertEqual(NETWORKS['regtest']['p2sh_version'], 0xc4)
        self.assertEqual(NETWORKS['regtest']['bech32_hrp'], 'bcrt')
        
        # Signet
        self.assertEqual(NETWORKS['signet']['p2pkh_version'], 0x6f)
        self.assertEqual(NETWORKS['signet']['p2sh_version'], 0xc4)
        self.assertEqual(NETWORKS['signet']['bech32_hrp'], 'tb')


class TestBitcoinKeysIntegration(unittest.TestCase):
    """Test integration with BitcoinKey class"""
    
    def test_generate_and_check(self):
        """Test generating addresses and checking balances"""
        checker = BalanceChecker()
        
        # Load a test file with one address
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as f:
            key = BitcoinKey()
            test_address = key.get_p2pkh_address()
            f.write(test_address + '\n')
            temp_file = f.name
        
        try:
            checker.load_addresses(temp_file)
            
            # Verify the loaded address is detected as funded
            balance = checker.check_balance(test_address)
            self.assertEqual(balance, 1)
            
            # Generate new addresses and verify they're not in the list
            for _ in range(5):
                new_key = BitcoinKey()
                new_address = new_key.get_p2pkh_address()
                if new_address != test_address:
                    balance = checker.check_balance(new_address)
                    self.assertEqual(balance, 0)
        finally:
            os.unlink(temp_file)
            checker.close()


def run_tests():
    """Run all tests"""
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add all test cases
    suite.addTests(loader.loadTestsFromTestCase(TestBalanceChecker))
    suite.addTests(loader.loadTestsFromTestCase(TestBitcoinKeysIntegration))
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Return exit code
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    sys.exit(run_tests())
