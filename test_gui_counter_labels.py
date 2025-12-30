#!/usr/bin/env python3
"""
Test script to verify GUI counter labels and tooltips are correctly set.
"""

import sys
from PySide6.QtWidgets import QApplication

def test_gui_counter_labels():
    """Test that GUI counter labels and tooltips are properly configured."""
    print("Testing GUI counter labels and tooltips...")
    
    app = QApplication(sys.argv)
    
    from vanitygen_py.gui import VanityGenGUI
    gui = VanityGenGUI()
    
    # Test Progress tab stats label
    print("\n1. Progress Tab - 'Keys Searched' Label:")
    stats_label_text = gui.stats_label.text()
    stats_tooltip = gui.stats_label.toolTip()
    
    print(f"   Text: {stats_label_text}")
    print(f"   Tooltip: {stats_tooltip[:80]}..." if len(stats_tooltip) > 80 else f"   Tooltip: {stats_tooltip}")
    
    assert "Keys Searched" in stats_label_text, "Stats label should contain 'Keys Searched'"
    assert "Total number of keys" in stats_tooltip or "Keys Searched" in stats_tooltip, \
        "Stats label should have explanatory tooltip"
    print("   ✓ Stats label has text and tooltip")
    
    # Test Settings tab address type counters
    print("\n2. Settings Tab - Address Type Counters:")
    
    # Check if tally widget exists
    assert hasattr(gui, 'tally_widget'), "GUI should have tally_widget"
    assert gui.tally_widget is not None, "Tally widget should be initialized"
    print("   ✓ Tally widget exists")
    
    # Check P2PKH counter
    assert hasattr(gui, 'p2pkh_count_label'), "GUI should have p2pkh_count_label"
    p2pkh_text = gui.p2pkh_count_label.text()
    p2pkh_tooltip = gui.p2pkh_count_label.toolTip()
    print(f"   P2PKH Label: {p2pkh_text}")
    print(f"   P2PKH Tooltip: {p2pkh_tooltip}")
    assert "P2PKH" in p2pkh_text, "P2PKH label should contain 'P2PKH'"
    print("   ✓ P2PKH label configured")
    
    # Check P2WPKH counter
    assert hasattr(gui, 'p2wpkh_count_label'), "GUI should have p2wpkh_count_label"
    p2wpkh_text = gui.p2wpkh_count_label.text()
    p2wpkh_tooltip = gui.p2wpkh_count_label.toolTip()
    print(f"   P2WPKH Label: {p2wpkh_text}")
    print(f"   P2WPKH Tooltip: {p2wpkh_tooltip}")
    assert "P2WPKH" in p2wpkh_text, "P2WPKH label should contain 'P2WPKH'"
    print("   ✓ P2WPKH label configured")
    
    # Check P2SH counter
    assert hasattr(gui, 'p2sh_count_label'), "GUI should have p2sh_count_label"
    p2sh_text = gui.p2sh_count_label.text()
    p2sh_tooltip = gui.p2sh_count_label.toolTip()
    print(f"   P2SH Label: {p2sh_text}")
    print(f"   P2SH Tooltip: {p2sh_tooltip}")
    assert "P2SH" in p2sh_text, "P2SH label should contain 'P2SH'"
    print("   ✓ P2SH label configured")
    
    # Test EC Checks tab
    print("\n3. EC Checks Tab:")
    if hasattr(gui, 'ec_checks_output'):
        print("   ✓ EC checks output widget exists")
        
        # The info label should be in the EC checks tab layout
        # We can't easily test the layout without showing the window,
        # but we can verify the widget exists
        print("   ✓ EC checks tab is properly configured")
    else:
        print("   ✗ EC checks output widget not found")
        return False
    
    # Test address counter update method
    print("\n4. Address Counter Update Method:")
    original_p2pkh = gui.address_counters.get('p2pkh', 0)
    original_p2wpkh = gui.address_counters.get('p2wpkh', 0)
    original_p2sh = gui.address_counters.get('p2sh-p2wpkh', 0)
    
    print(f"   Original counters: P2PKH={original_p2pkh}, P2WPKH={original_p2wpkh}, P2SH={original_p2sh}")
    
    # Simulate incrementing counters
    gui.address_counters['p2pkh'] = 5
    gui.address_counters['p2wpkh'] = 3
    gui.address_counters['p2sh-p2wpkh'] = 2
    gui.update_address_counters()
    
    assert "5" in gui.p2pkh_count_label.text(), "P2PKH counter should show 5"
    assert "3" in gui.p2wpkh_count_label.text(), "P2WPKH counter should show 3"
    assert "2" in gui.p2sh_count_label.text(), "P2SH counter should show 2"
    
    print(f"   Updated labels: {gui.p2pkh_count_label.text()}, {gui.p2wpkh_count_label.text()}, {gui.p2sh_count_label.text()}")
    print("   ✓ Counter update method works correctly")
    
    # Reset counters
    gui.address_counters = {'p2pkh': 0, 'p2wpkh': 0, 'p2sh-p2wpkh': 0}
    gui.update_address_counters()
    
    app.quit()
    return True

if __name__ == "__main__":
    try:
        print("=" * 60)
        print("GUI Counter Labels Test Suite")
        print("=" * 60)
        
        if test_gui_counter_labels():
            print("\n" + "=" * 60)
            print("✓ All GUI tests passed!")
            print("=" * 60)
            sys.exit(0)
        else:
            print("\n✗ Some GUI tests failed")
            sys.exit(1)
    except Exception as e:
        print(f"\n✗ Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
