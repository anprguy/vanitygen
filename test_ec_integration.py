#!/usr/bin/env python3
"""
Test script to verify the integration of calc_addrs.cl EC math into vanitygen_py.
This script tests that the optimized EC functions are available and working.
"""

import sys
import os

# Add the vanitygen_py directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'vanitygen_py'))

def test_imports():
    """Test that all required modules can be imported"""
    print("Testing imports...")
    try:
        from gpu_generator import GPUGenerator
        print("✓ GPUGenerator imported successfully")
        return True
    except ImportError as e:
        print(f"✗ Failed to import GPUGenerator: {e}")
        return False

def test_gpu_initialization():
    """Test GPU initialization and kernel compilation"""
    print("\nTesting GPU initialization...")
    try:
        from gpu_generator import GPUGenerator
        
        # Create GPU generator instance
        gpu_gen = GPUGenerator('test', batch_size=1024, power_percent=50)
        
        # Try to initialize GPU
        if gpu_gen.init_cl():
            print("✓ GPU initialized successfully")
            print(f"  Device: {gpu_gen.device.name}")
            
            # Check if optimized kernels are available
            kernels_available = []
            if gpu_gen.kernel_ec_add_grid is not None:
                kernels_available.append("ec_add_grid")
            if gpu_gen.kernel_heap_invert is not None:
                kernels_available.append("heap_invert")
            if gpu_gen.kernel_test_optimized_ec is not None:
                kernels_available.append("test_optimized_ec")
            
            if kernels_available:
                print(f"✓ Optimized kernels available: {', '.join(kernels_available)}")
            else:
                print("✗ No optimized kernels available")
                
            # Test the optimized EC function
            if gpu_gen.kernel_test_optimized_ec is not None:
                print("\nTesting optimized EC functions...")
                priv_key, pub_key = gpu_gen._test_optimized_ec(12345, 0)
                if priv_key and pub_key:
                    print("✓ Optimized EC test successful")
                    print(f"  Private key: {priv_key.hex()}")
                    print(f"  Public key: {pub_key.hex()}")
                else:
                    print("✗ Optimized EC test failed")
            
            gpu_gen.cleanup()
            return True
        else:
            print("✗ Failed to initialize GPU")
            return False
            
    except Exception as e:
        print(f"✗ Error during GPU initialization: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_cpu_ec_consistency():
    """Test that GPU and CPU EC calculations produce consistent results"""
    print("\nTesting CPU/GPU EC consistency...")
    try:
        from gpu_generator import GPUGenerator
        from bitcoin_keys import BitcoinKey
        
        # Create GPU generator
        gpu_gen = GPUGenerator('test', batch_size=1024, power_percent=50)
        
        if not gpu_gen.init_cl():
            print("✗ GPU initialization failed")
            return False
            
        if gpu_gen.kernel_test_optimized_ec is None:
            print("✗ Optimized EC kernel not available")
            gpu_gen.cleanup()
            return False
        
        # Test with a known seed
        seed = 12345
        gid = 0
        
        # Get GPU result
        gpu_priv, gpu_pub = gpu_gen._test_optimized_ec(seed, gid)
        
        if not gpu_priv or not gpu_pub:
            print("✗ Failed to get GPU EC result")
            gpu_gen.cleanup()
            return False
        
        # Create CPU key from the same private key
        cpu_key = BitcoinKey(gpu_priv)
        cpu_pub = cpu_key.get_public_key()
        
        print(f"GPU Public Key: {gpu_pub.hex()}")
        print(f"CPU Public Key: {cpu_pub.hex()}")
        
        if gpu_pub == cpu_pub:
            print("✓ GPU and CPU EC calculations match!")
            result = True
        else:
            print("✗ GPU and CPU EC calculations do NOT match!")
            result = False
            
        gpu_gen.cleanup()
        return result
        
    except Exception as e:
        print(f"✗ Error during consistency test: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Main test function"""
    print("=" * 60)
    print("EC Integration Test Suite")
    print("=" * 60)
    
    tests = [
        ("Import Test", test_imports),
        ("GPU Initialization Test", test_gpu_initialization),
        ("CPU/GPU Consistency Test", test_cpu_ec_consistency),
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
        print("🎉 All tests passed! EC integration is working correctly.")
        return True
    else:
        print("❌ Some tests failed. Please check the output above.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)