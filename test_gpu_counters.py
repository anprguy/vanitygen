#!/usr/bin/env python3
"""
Test GPU-only mode with separate counters for keys generated and keys checked.
"""
import sys
import os
import time
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'vanitygen_py'))

from vanitygen_py.gpu_generator import GPUGenerator
from vanitygen_py.balance_checker import BalanceChecker

def test_gpu_counters():
    """Test that GPU generator tracks both keys_generated and keys_checked"""
    print("Testing GPU Counter Tracking...")
    print("="*60)
    
    # Create a GPU generator in GPU-only mode
    print("\n1. Creating GPU generator (GPU-only mode)...")
    gen = GPUGenerator(
        prefix="1",  # Simple prefix
        addr_type='p2pkh',
        batch_size=1000,  # Small batch for testing
        gpu_only=True  # GPU-only mode
    )
    
    # Initialize GPU
    print("2. Initializing GPU...")
    if not gen.init_cl():
        print("ERROR: Failed to initialize GPU")
        return False
    
    print(f"   ✓ Using GPU: {gen.device.name}\n")
    
    # Start generation
    print("3. Starting generation (will run for 5 seconds)...")
    gen.start()
    
    # Let it run for a few seconds
    start_time = time.time()
    last_generated = 0
    last_checked = 0
    
    while time.time() - start_time < 5:
        time.sleep(1)
        stats = gen.get_stats()
        
        if isinstance(stats, dict):
            generated = stats.get('keys_generated', 0)
            checked = stats.get('keys_checked', 0)
            
            print(f"   Stats: Generated={generated:,}, Checked={checked:,}")
            
            # Verify counters are incrementing
            if generated > 0 and checked > 0:
                if generated != checked:
                    print(f"   WARNING: Generated ({generated}) != Checked ({checked})")
                    print(f"   In GPU-only mode with balance checking, these should be equal!")
                else:
                    print(f"   ✓ Counters match (both {generated:,})")
            
            last_generated = generated
            last_checked = checked
        else:
            print(f"   Stats: {stats} (old format - expected dict)")
    
    # Stop generation
    print("\n4. Stopping generation...")
    gen.stop()
    
    # Final check
    print("\n" + "="*60)
    print("Test Results:")
    print(f"  Keys Generated: {last_generated:,}")
    print(f"  Keys Checked: {last_checked:,}")
    
    if last_generated > 0 and last_checked > 0:
        print("  ✓ Both counters incremented successfully!")
        if last_generated == last_checked:
            print("  ✓ Counters match (as expected in GPU-only mode)")
        else:
            print(f"  ⚠ Counter mismatch: {last_generated} vs {last_checked}")
    else:
        print("  ✗ Counters did not increment!")
        return False
    
    print("="*60)
    return True

def test_gpu_with_balance_checker():
    """Test GPU-only mode with balance checker"""
    print("\n\nTesting GPU with Balance Checker...")
    print("="*60)
    
    # Create a balance checker with dummy addresses
    print("\n1. Creating balance checker with test addresses...")
    checker = BalanceChecker()
    
    # Add some test addresses
    test_addresses = [
        "1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa",  # Genesis block
        "1BoatSLRHtKNngkdXEeobR76b53LETtpyT",  # Satoshi's
    ]
    
    # Create a temp CSV file
    import tempfile
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.csv') as f:
        for addr in test_addresses:
            f.write(f"{addr},0\n")
        csv_path = f.name
    
    try:
        print(f"   Loading {len(test_addresses)} test addresses...")
        checker.load_from_csv(csv_path)
        print(f"   ✓ Loaded: {checker.get_status()}")
        
        # Create GPU generator with balance checker
        print("\n2. Creating GPU generator with balance checker...")
        gen = GPUGenerator(
            prefix="",  # No prefix - just check against funded list
            addr_type='p2pkh',
            batch_size=1000,
            gpu_only=True,
            balance_checker=checker
        )
        
        # Initialize GPU
        print("3. Initializing GPU...")
        if not gen.init_cl():
            print("ERROR: Failed to initialize GPU")
            return False
        
        print(f"   ✓ Using GPU: {gen.device.name}")
        
        # Setup balance checker on GPU
        print("4. Setting up GPU balance checking...")
        gen.set_balance_checker(checker)
        
        # Start generation
        print("5. Starting generation (will run for 5 seconds)...")
        gen.start()
        
        # Let it run
        start_time = time.time()
        while time.time() - start_time < 5:
            time.sleep(1)
            stats = gen.get_stats()
            
            if isinstance(stats, dict):
                generated = stats.get('keys_generated', 0)
                checked = stats.get('keys_checked', 0)
                print(f"   Generated={generated:,}, Checked={checked:,}")
        
        # Stop
        print("\n6. Stopping generation...")
        gen.stop()
        
        print("\n✓ Test completed successfully!")
        
    finally:
        # Clean up temp file
        try:
            os.unlink(csv_path)
        except:
            pass
    
    print("="*60)
    return True

if __name__ == "__main__":
    try:
        print("GPU Counter Tracking Tests\n")
        
        # Test 1: Basic counter tracking
        success1 = test_gpu_counters()
        
        # Test 2: With balance checker
        success2 = test_gpu_with_balance_checker()
        
        print("\n\nFinal Results:")
        print("="*60)
        print(f"Basic Counter Test: {'✓ PASSED' if success1 else '✗ FAILED'}")
        print(f"Balance Checker Test: {'✓ PASSED' if success2 else '✗ FAILED'}")
        print("="*60)
        
        sys.exit(0 if (success1 and success2) else 1)
        
    except Exception as e:
        print(f"\nERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
