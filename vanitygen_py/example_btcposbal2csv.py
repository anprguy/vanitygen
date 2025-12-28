#!/usr/bin/env python3
"""
Example: Using btcposbal2csv for Address Extraction

This example demonstrates how to use the btcposbal2csv integration to extract
addresses with positive balances from Bitcoin Core's chainstate database.

btcposbal2csv is a high-performance C++ tool that can quickly extract all
funded addresses from the chainstate LevelDB and export them to CSV format.

Benefits:
- Faster extraction than pure Python LevelDB parsing
- CSV format is portable and can be shared/cached
- Reduced memory usage if you only need address presence (not balances)
- Can be used offline after initial extraction

Installation:
    git clone https://github.com/graymauser/btcposbal2csv
    cd btcposbal2csv
    make
    sudo cp btcposbal2csv /usr/local/bin/  # Or add to PATH
"""

import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from vanitygen_py.balance_checker import BalanceChecker
from vanitygen_py.bitcoin_keys import BitcoinKey


def example_1_extract_with_btcposbal2csv():
    """Example 1: Extract addresses using btcposbal2csv"""
    print("=" * 70)
    print("Example 1: Extract Addresses with btcposbal2csv")
    print("=" * 70)
    
    checker = BalanceChecker()
    checker.enable_debug(True)
    
    # This will:
    # 1. Auto-detect Bitcoin Core chainstate path
    # 2. Run btcposbal2csv to extract addresses to CSV
    # 3. Load the CSV into memory
    # 4. Clean up temporary files
    print("\nExtracting addresses from Bitcoin Core chainstate...")
    if checker.extract_addresses_with_btcposbal2csv():
        print(f"✓ Successfully loaded {len(checker.address_balances)} addresses")
        
        # Test with a few generated addresses
        print("\nTesting with randomly generated addresses:")
        for i in range(5):
            key = BitcoinKey()
            address = key.get_p2pkh_address()
            balance = checker.get_balance(address)
            print(f"  {address}: {balance} satoshis")
    else:
        print("✗ Failed to extract addresses")
        print("\nTroubleshooting:")
        print("1. Make sure Bitcoin Core is fully synced")
        print("2. Close Bitcoin Core before running")
        print("3. Install btcposbal2csv: https://github.com/graymauser/btcposbal2csv")


def example_2_extract_to_specific_file():
    """Example 2: Extract to a specific CSV file for later use"""
    print("\n" + "=" * 70)
    print("Example 2: Extract to Specific CSV File")
    print("=" * 70)
    
    checker = BalanceChecker()
    output_file = "funded_addresses.csv"
    
    print(f"\nExtracting addresses to: {output_file}")
    if checker.extract_addresses_with_btcposbal2csv(output_csv=output_file):
        print(f"✓ CSV file created: {output_file}")
        print(f"✓ Loaded {len(checker.address_balances)} addresses")
        
        # Show CSV stats
        if os.path.exists(output_file):
            file_size = os.path.getsize(output_file) / 1024 / 1024  # MB
            print(f"\nCSV file size: {file_size:.2f} MB")
            print(f"You can now share or cache this file for faster loading")
    else:
        print("✗ Extraction failed")


def example_3_load_from_existing_csv():
    """Example 3: Load addresses from an existing CSV file"""
    print("\n" + "=" * 70)
    print("Example 3: Load from Existing CSV")
    print("=" * 70)
    
    csv_file = "funded_addresses.csv"
    
    if not os.path.exists(csv_file):
        print(f"CSV file not found: {csv_file}")
        print("Run Example 2 first to create the CSV file")
        return
    
    checker = BalanceChecker()
    
    print(f"\nLoading addresses from CSV: {csv_file}")
    if checker.load_from_csv(csv_file):
        print(f"✓ Loaded {len(checker.address_balances)} addresses")
        
        # Show some stats
        if checker.address_balances:
            total_balance = sum(checker.address_balances.values())
            avg_balance = total_balance / len(checker.address_balances)
            max_balance = max(checker.address_balances.values())
            
            print(f"\nStatistics:")
            print(f"  Total addresses: {len(checker.address_balances):,}")
            print(f"  Total balance: {total_balance:,} satoshis ({total_balance / 100000000:.8f} BTC)")
            print(f"  Average balance: {avg_balance:.2f} satoshis")
            print(f"  Maximum balance: {max_balance:,} satoshis")
    else:
        print("✗ Failed to load CSV")


def example_4_custom_csv_format():
    """Example 4: Load CSV with custom column names"""
    print("\n" + "=" * 70)
    print("Example 4: Custom CSV Format")
    print("=" * 70)
    
    # Create a sample CSV with custom column names
    sample_csv = "custom_addresses.csv"
    with open(sample_csv, 'w') as f:
        f.write("addr,amount,type\n")
        f.write("1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa,5000000000,p2pkh\n")
        f.write("bc1qxy2kgdygjrsqtzq2n0yrf2493p83kkfjhx0wlh,100000,p2wpkh\n")
        f.write("3J98t1WpEZ73CNmYviecrnyiWrnqRhWNLy,2500000,p2sh\n")
    
    print(f"\nCreated sample CSV: {sample_csv}")
    
    checker = BalanceChecker()
    
    # Load with custom column names
    print("Loading with custom columns (addr, amount)...")
    if checker.load_from_csv(sample_csv, address_column='addr', balance_column='amount'):
        print(f"✓ Loaded {len(checker.address_balances)} addresses")
        
        print("\nChecking loaded addresses:")
        for addr, balance in checker.address_balances.items():
            print(f"  {addr}: {balance:,} satoshis")
    else:
        print("✗ Failed to load CSV")
    
    # Clean up
    if os.path.exists(sample_csv):
        os.remove(sample_csv)


def example_5_compare_methods():
    """Example 5: Compare btcposbal2csv vs direct LevelDB loading"""
    print("\n" + "=" * 70)
    print("Example 5: Method Comparison")
    print("=" * 70)
    
    import time
    
    print("\nMethod 1: Direct LevelDB Loading (Python plyvel)")
    print("-" * 50)
    checker1 = BalanceChecker()
    start = time.time()
    success1 = checker1.load_from_bitcoin_core()
    elapsed1 = time.time() - start
    
    if success1:
        print(f"✓ Loaded {len(checker1.address_balances)} addresses in {elapsed1:.2f}s")
    else:
        print("✗ Direct loading failed")
    
    print("\nMethod 2: btcposbal2csv Extraction")
    print("-" * 50)
    checker2 = BalanceChecker()
    start = time.time()
    success2 = checker2.extract_addresses_with_btcposbal2csv(output_csv="temp_addresses.csv")
    elapsed2 = time.time() - start
    
    if success2:
        print(f"✓ Loaded {len(checker2.address_balances)} addresses in {elapsed2:.2f}s")
    else:
        print("✗ btcposbal2csv extraction failed")
    
    # Compare results
    if success1 and success2:
        print("\nComparison:")
        print(f"  Method 1 (plyvel):      {len(checker1.address_balances):,} addresses in {elapsed1:.2f}s")
        print(f"  Method 2 (btcposbal2csv): {len(checker2.address_balances):,} addresses in {elapsed2:.2f}s")
        
        if elapsed2 < elapsed1:
            speedup = elapsed1 / elapsed2
            print(f"  → btcposbal2csv is {speedup:.1f}x faster!")
        else:
            print(f"  → Direct loading was faster this time")
    
    # Clean up
    if os.path.exists("temp_addresses.csv"):
        os.remove("temp_addresses.csv")


def main():
    """Run all examples"""
    print("\n" + "=" * 70)
    print("btcposbal2csv Integration Examples")
    print("=" * 70)
    print("\nThese examples demonstrate the btcposbal2csv integration feature.")
    print("btcposbal2csv is a fast C++ tool for extracting funded addresses.")
    print("\nPrerequisites:")
    print("1. Bitcoin Core installed and fully synced")
    print("2. Bitcoin Core stopped (not running)")
    print("3. btcposbal2csv installed (https://github.com/graymauser/btcposbal2csv)")
    
    try:
        # Run examples
        example_1_extract_with_btcposbal2csv()
        
        # Uncomment to run additional examples:
        # example_2_extract_to_specific_file()
        # example_3_load_from_existing_csv()
        # example_4_custom_csv_format()
        # example_5_compare_methods()
        
    except KeyboardInterrupt:
        print("\n\nInterrupted by user")
    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
