#!/usr/bin/env python3
"""
Script to help extract and compare EC functions between calc_addrs.cl and gpu_kernel.cl

This script identifies the exact lines to replace for each buggy function.
"""
import re

def extract_function(file_content, function_name):
    """Extract a complete function from C/OpenCL code"""
    # Find function definition
    pattern = rf'(void|int|bn_word)\s+{re.escape(function_name)}\s*\([^)]*\)\s*\{{'
    match = re.search(pattern, file_content)
    
    if not match:
        return None, None
    
    start_pos = match.start()
    start_line = file_content[:start_pos].count('\n') + 1
    
    # Find matching closing brace
    brace_count = 0
    in_function = False
    end_pos = start_pos
    
    for i, char in enumerate(file_content[start_pos:], start=start_pos):
        if char == '{':
            brace_count += 1
            in_function = True
        elif char == '}':
            brace_count -= 1
            if in_function and brace_count == 0:
                end_pos = i + 1
                break
    
    end_line = file_content[:end_pos].count('\n') + 1
    function_code = file_content[start_pos:end_pos]
    
    return function_code, (start_line, end_line)


def main():
    print("="*80)
    print("GPU EC Function Extraction Tool")
    print("="*80)
    print()
    
    # Read files
    try:
        with open('calc_addrs.cl', 'r') as f:
            calc_addrs_content = f.read()
        print("✓ Loaded calc_addrs.cl")
    except FileNotFoundError:
        print("ERROR: calc_addrs.cl not found in current directory")
        return
    
    try:
        with open('vanitygen_py/gpu_kernel.cl', 'r') as f:
            gpu_kernel_content = f.read()
        print("✓ Loaded vanitygen_py/gpu_kernel.cl")
    except FileNotFoundError:
        print("ERROR: vanitygen_py/gpu_kernel.cl not found")
        return
    
    print()
    print("="*80)
    print("FUNCTION COMPARISON")
    print("="*80)
    print()
    
    # Functions to compare
    functions = [
        'bn_mul_mont',
        'bn_mod_inverse',
        'bn_from_mont'
    ]
    
    for func_name in functions:
        print(f"\n### Function: {func_name}")
        print("-" * 40)
        
        # Extract from calc_addrs.cl
        calc_func, calc_lines = extract_function(calc_addrs_content, func_name)
        if calc_func:
            print(f"calc_addrs.cl:      lines {calc_lines[0]}-{calc_lines[1]} ({calc_lines[1]-calc_lines[0]+1} lines)")
            print(f"  Size: {len(calc_func)} characters")
        else:
            print(f"calc_addrs.cl:      NOT FOUND")
        
        # Extract from gpu_kernel.cl
        gpu_func, gpu_lines = extract_function(gpu_kernel_content, func_name)
        if gpu_func:
            print(f"gpu_kernel.cl:      lines {gpu_lines[0]}-{gpu_lines[1]} ({gpu_lines[1]-gpu_lines[0]+1} lines)")
            print(f"  Size: {len(gpu_func)} characters")
            
            # Check for suspicious comments
            if 'simplified' in gpu_func.lower() or 'todo' in gpu_func.lower() or 'fixme' in gpu_func.lower():
                print(f"  ⚠️  WARNING: Contains suspicious comments!")
        else:
            print(f"gpu_kernel.cl:      NOT FOUND")
        
        if calc_func and gpu_func:
            # Simple comparison
            if calc_func.strip() == gpu_func.strip():
                print(f"  ✓ Functions are IDENTICAL")
            else:
                size_diff = len(calc_func) - len(gpu_func)
                print(f"  ✗ Functions DIFFER (size diff: {size_diff:+d} chars)")
    
    print()
    print("="*80)
    print("RECOMMENDATIONS")
    print("="*80)
    print()
    print("1. Review GPU_KERNEL_FIXES.md for detailed analysis")
    print("2. Run test_gpu_ec_correctness.py to verify current implementation")
    print("3. If test fails, replace buggy functions with calc_addrs.cl versions")
    print("4. Or use Hybrid Mode (GPU+coincurve) for guaranteed correctness")
    print()


if __name__ == '__main__':
    main()
