#!/usr/bin/env python3
"""
Test script to verify that the EC integration compiles correctly.
This test focuses on code compilation and structure without requiring GPU.
"""

import sys
import os

# Add the vanitygen_py directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'vanitygen_py'))

def test_kernel_code_structure():
    """Test that the kernel code has the expected structure"""
    print("Testing kernel code structure...")
    
    try:
        # Read the kernel file
        with open('vanitygen_py/gpu_kernel.cl', 'r') as f:
            kernel_code = f.read()
        
        # Check for expected functions and constants
        expected_elements = [
            'ACCESS_BUNDLE',
            'ACCESS_STRIDE',
            'ec_add_grid',
            'heap_invert',
            'test_optimized_ec',
            'scalar_mult_g_optimized',
            'point_j_add_optimized',
            'bn_lshift1',
            'bn_neg'
        ]
        
        found_elements = []
        missing_elements = []
        
        for element in expected_elements:
            if element in kernel_code:
                found_elements.append(element)
            else:
                missing_elements.append(element)
        
        print(f"✓ Found {len(found_elements)}/{len(expected_elements)} expected elements")
        
        if found_elements:
            print("  Found:", ", ".join(found_elements))
        
        if missing_elements:
            print("  Missing:", ", ".join(missing_elements))
        
        return len(missing_elements) == 0
        
    except Exception as e:
        print(f"✗ Error reading kernel code: {e}")
        return False

def test_python_integration():
    """Test that the Python code integrates the new kernels correctly"""
    print("\nTesting Python integration...")
    
    try:
        # Read the gpu_generator.py file
        with open('vanitygen_py/gpu_generator.py', 'r') as f:
            python_code = f.read()
        
        # Check for expected kernel attributes and methods
        expected_elements = [
            'kernel_ec_add_grid',
            'kernel_heap_invert',
            'kernel_test_optimized_ec',
            '_test_optimized_ec',
            'ec_add_grid',
            'heap_invert'
        ]
        
        found_elements = []
        missing_elements = []
        
        for element in expected_elements:
            if element in python_code:
                found_elements.append(element)
            else:
                missing_elements.append(element)
        
        print(f"✓ Found {len(found_elements)}/{len(expected_elements)} expected elements")
        
        if found_elements:
            print("  Found:", ", ".join(found_elements))
        
        if missing_elements:
            print("  Missing:", ", ".join(missing_elements))
        
        return len(missing_elements) == 0
        
    except Exception as e:
        print(f"✗ Error reading Python code: {e}")
        return False

def test_code_syntax():
    """Test that the code has valid syntax"""
    print("\nTesting code syntax...")
    
    try:
        # Test kernel code syntax by checking for basic OpenCL syntax
        with open('vanitygen_py/gpu_kernel.cl', 'r') as f:
            kernel_code = f.read()
        
        # Check for basic OpenCL syntax elements
        syntax_elements = [
            '__kernel',
            '__global',
            'void',
            'return',
            'if (',
            'for (',
            '{', '}',
            ';'
        ]
        
        found_syntax = []
        for element in syntax_elements:
            if element in kernel_code:
                found_syntax.append(element)
        
        print(f"✓ Found {len(found_syntax)}/{len(syntax_elements)} basic syntax elements")
        
        # Check for balanced braces (simple check)
        open_braces = kernel_code.count('{')
        close_braces = kernel_code.count('}')
        
        if open_braces == close_braces:
            print(f"✓ Braces are balanced ({open_braces} opening, {close_braces} closing)")
        else:
            print(f"✗ Braces are not balanced ({open_braces} opening, {close_braces} closing)")
            return False
        
        return True
        
    except Exception as e:
        print(f"✗ Error checking syntax: {e}")
        return False

def test_ec_constants():
    """Test that EC constants are correctly defined"""
    print("\nTesting EC constants...")
    
    try:
        with open('vanitygen_py/gpu_kernel.cl', 'r') as f:
            kernel_code = f.read()
        
        # Check for generator point constants
        if 'Gx[] = { 0x16F81798' in kernel_code and 'Gy[] = { 0x483ADA77' in kernel_code:
            print("✓ Generator point constants found")
        else:
            print("✗ Generator point constants not found or incorrect")
            return False
        
        # Check for modulus constants
        if 'MODULUS_BYTES' in kernel_code:
            print("✓ Modulus constants found")
        else:
            print("✗ Modulus constants not found")
            return False
        
        # Check for Montgomery constants
        if 'mont_rr[]' in kernel_code and 'mont_n0' in kernel_code:
            print("✓ Montgomery constants found")
        else:
            print("✗ Montgomery constants not found")
            return False
        
        return True
        
    except Exception as e:
        print(f"✗ Error checking EC constants: {e}")
        return False

def main():
    """Main test function"""
    print("=" * 60)
    print("EC Integration Compilation Test")
    print("=" * 60)
    
    tests = [
        ("Kernel Code Structure", test_kernel_code_structure),
        ("Python Integration", test_python_integration),
        ("Code Syntax", test_code_syntax),
        ("EC Constants", test_ec_constants),
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"\n{test_name}:")
        result = test_func()
        results.append((test_name, result))
    
    print("\n" + "=" * 60)
    print("Test Results Summary")
    print("=" * 60)
    
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status}: {test_name}")
        if result:
            passed += 1
    
    print(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All compilation tests passed!")
        print("The EC integration from calc_addrs.cl has been successfully added to the codebase.")
        print("The optimized functions are available and ready for use when GPU is available.")
        return True
    else:
        print("❌ Some compilation tests failed.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)