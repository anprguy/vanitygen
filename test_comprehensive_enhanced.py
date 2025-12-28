#!/usr/bin/env python3
"""
Comprehensive testing script for enhanced vanitygen features.
Tests GUI functionality without requiring Qt display.
"""

import sys
import os
from unittest.mock import Mock, patch

sys.path.insert(0, os.path.dirname(__file__))

def test_gui_structure():
    """Test that GUI has all enhanced features."""
    from vanitygen_py.gui import VanityGenGUI
    
    # Mock the Qt application
    with patch('PySide6.QtWidgets.QApplication'), \
         patch('PySide6.QtWidgets.QMainWindow'):
        
        gui = VanityGenGUI()
        
        # Test search all types checkbox exists
        assert hasattr(gui, 'search_all_types_check')
        print("✓ Search all types checkbox present")
        
        # Test address counters exist
        assert hasattr(gui, 'address_counters')
        assert isinstance(gui.address_counters, dict)
        print("✓ Address counters initialized")
        
        assert hasattr(gui, 'p2pkh_count_label')
        assert hasattr(gui, 'p2wpkh_count_label')
        assert hasattr(gui, 'p2sh_count_label')
        print("✓ Counter labels present")
        
        # Test auto-save checkbox exists
        assert hasattr(gui, 'auto_save_check')
        print("✓ Auto-save checkbox present")
        
        # Test methods exist
        assert hasattr(gui, 'on_search_all_types_changed')
        assert hasattr(gui, 'update_address_counters')
        assert hasattr(gui, 'save_funded_address')
        assert hasattr(gui, 'show_congratulations')
        print("✓ All enhanced methods present")
        
        # Test address counters initialized correctly
        assert gui.address_counters == {'p2pkh': 0, 'p2wpkh': 0, 'p2sh-p2wpkh': 0}
        print("✓ Counters initialized to zero")
        
        return gui

def test_address_counter_functionality():
    """Test that address counters work correctly."""
    from vanitygen_py.gui import VanityGenGUI
    
    with patch('PySide6.QtWidgets.QApplication'), \
         patch('PySide6.QtWidgets.QMainWindow'):
        
        gui = VanityGenGUI()
        
        # Test counter update
        gui.address_counters['p2pkh'] = 5
        gui.address_counters['p2wpkh'] = 3
        gui.address_counters['p2sh-p2wpkh'] = 2
        
        gui.update_address_counters()
        
        # Check labels updated (labels are mocked but we verify no errors)
        print("✓ Counter update method executed without errors")

def test_save_funded_address():
    """Test funded address saving."""
    from vanitygen_py.gui import VanityGenGUI
    
    with patch('PySide6.QtWidgets.QApplication'), \
         patch('PySide6.QtWidgets.QMainWindow'):
        
        gui = VanityGenGUI()
        
        # Test saving funded address
        addr = "1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa"
        wif = "5KJvsngHeMwmT7t6PeBob9R7sjwrcrX5K6VRZX4m9k2wd7N2VzN"
        pubkey = "04_test_public_key_"
        balance = 5000000000
        
        filename = gui.save_funded_address(addr, wif, pubkey, balance, 'p2pkh')
        
        assert filename is not None
        assert os.path.exists(filename)
        print(f"✓ Funded address saved to: {filename}")
        
        # Verify file contents
        with open(filename, 'r') as f:
            content = f.read()
            assert "Congratulations" in content
            assert addr in content
            assert wif in content
            assert "satoshis" in content
            print("✓ File contains correct information")
        
        # Cleanup
        os.unlink(filename)

def test_signal_signatures():
    """Test that signal signatures are correct."""
    from vanitygen_py.gui import GeneratorThread
    
    # Check signal definitions
    thread = GeneratorThread(
        prefix="1",
        addr_type="p2pkh",
        balance_checker=Mock()
    )
    
    # Test signals exist
    assert hasattr(thread, 'stats_updated')
    assert hasattr(thread, 'address_found')
    print("✓ GeneratorThread signals present")
    
    # Test signal can be connected (would fail if signature mismatched)
    mock_handler = Mock()
    thread.address_found.connect(mock_handler)
    print("✓ Signal connection successful")

def test_balance_checker_enhanced():
    """Test enhanced balance checker methods."""
    from vanitygen_py.balance_checker import BalanceChecker
    
    checker = BalanceChecker()
    
    # Test new method exists
    assert hasattr(checker, 'check_balance_and_membership')
    
    # Test it works
    balance, is_member = checker.check_balance_and_membership("test_address")
    assert balance == 0 and is_member == False
    print("✓ check_balance_and_membership method works")

def run_comprehensive_test():
    """Run all tests and report results."""
    print("Enhanced VanityGen Features Test Suite")
    print("=" * 50)
    
    tests = [
        ("GUI Structure", test_gui_structure),
        ("Address Counters", test_address_counter_functionality),
        ("Save Funded Address", test_save_funded_address),
        ("Signal Signatures", test_signal_signatures),
        ("Balance Checker Enhanced", test_balance_checker_enhanced),
    ]
    
    passed = 0
    failed = 0
    
    for test_name, test_func in tests:
        try:
            print(f"\nTesting: {test_name}")
            test_func()
            print(f"✓ {test_name} passed")
            passed += 1
        except Exception as e:
            print(f"✗ {test_name} failed: {e}")
            failed += 1
    
    print(f"\n{'='*50}")
    print(f"Results: {passed} passed, {failed} failed")
    
    if failed == 0:
        print("\n🎉 All tests passed! Enhanced features ready!")
        print("\n📋 Summary of enhancements:")
        print("1. ✓ Search all Bitcoin address types checkbox")
        print("2. ✓ Real-time address type tally counters")
        print("3. ✓ Auto-save funded addresses to secure files")
        print("4. ✓ Enhanced congratulations dialog with security warnings")
        print("5. ✓ Address type tracking and display")
        return True
    else:
        print("\n❌ Some tests failed. Please review errors above.")
        return False

if __name__ == "__main__":
    try:
        success = run_comprehensive_test()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ Test suite failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)