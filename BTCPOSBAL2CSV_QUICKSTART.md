# btcposbal2csv Quick Start Guide

## What is btcposbal2csv?

`btcposbal2csv` is a fast C++ tool that extracts all addresses with positive balances from Bitcoin Core's chainstate database and saves them to a CSV file.

**Why use it?**
- **Fast**: 2-5x faster than Python plyvel
- **Portable**: CSV files can be cached and reused instantly
- **Efficient**: Lower memory usage during extraction

## Installation (One-Time Setup)

### Step 1: Install System Dependencies

**Ubuntu/Debian:**
```bash
sudo apt-get install build-essential libleveldb-dev git
```

**macOS:**
```bash
brew install leveldb git
```

**Fedora/RHEL:**
```bash
sudo dnf install gcc-c++ leveldb-devel git
```

### Step 2: Build btcposbal2csv

```bash
# Clone the repository
git clone https://github.com/graymauser/btcposbal2csv
cd btcposbal2csv

# Build
make

# Install (optional - or just use from current directory)
sudo cp btcposbal2csv /usr/local/bin/
# OR add to PATH:
# export PATH=$PATH:$(pwd)
```

### Step 3: Verify Installation

```bash
btcposbal2csv -h
# Should show help/usage information
```

## Usage

### Method 1: Auto-Extract (Simplest)

```python
from vanitygen_py.balance_checker import BalanceChecker

checker = BalanceChecker()
if checker.extract_addresses_with_btcposbal2csv():
    print(f"✓ Loaded {len(checker.address_balances)} addresses")
```

This will:
1. Auto-detect Bitcoin Core chainstate path
2. Extract addresses to a temporary CSV file
3. Load CSV into memory
4. Clean up temporary file

### Method 2: Save CSV for Reuse (Recommended)

**First run (extract - slow):**
```python
from vanitygen_py.balance_checker import BalanceChecker

checker = BalanceChecker()
if checker.extract_addresses_with_btcposbal2csv(output_csv="addresses.csv"):
    print(f"✓ Extracted {len(checker.address_balances)} addresses to addresses.csv")
```

**Subsequent runs (load CSV - fast):**
```python
from vanitygen_py.balance_checker import BalanceChecker

checker = BalanceChecker()
if checker.load_from_csv("addresses.csv"):
    print(f"✓ Loaded {len(checker.address_balances)} addresses from CSV (instant!)")
```

### Method 3: Command Line Extraction

```bash
# Stop Bitcoin Core first
bitcoin-cli stop
sleep 10

# Extract addresses (replace ~/.bitcoin with your Bitcoin Core data directory)
btcposbal2csv ~/.bitcoin addresses.csv

# Restart Bitcoin Core
bitcoind -daemon

# Use in Python
python3 << EOF
from vanitygen_py.balance_checker import BalanceChecker
checker = BalanceChecker()
checker.load_from_csv("addresses.csv")
print(f"Loaded {len(checker.address_balances)} addresses")
EOF
```

## Common Workflows

### Daily Extraction Workflow

Create a script to extract addresses daily:

```bash
#!/bin/bash
# extract_addresses.sh

DATE=$(date +%Y%m%d)
OUTPUT="addresses_$DATE.csv"

echo "Stopping Bitcoin Core..."
bitcoin-cli stop
sleep 10

echo "Extracting addresses..."
btcposbal2csv ~/.bitcoin "$OUTPUT"

echo "Restarting Bitcoin Core..."
bitcoind -daemon

echo "Extracted addresses to $OUTPUT"
ls -lh "$OUTPUT"
```

Make it executable and run:
```bash
chmod +x extract_addresses.sh
./extract_addresses.sh
```

### Vanity Generation with Balance Checking

```python
from vanitygen_py.balance_checker import BalanceChecker
from vanitygen_py.cpu_generator import CPUGenerator

# Load pre-extracted addresses
checker = BalanceChecker()
print("Loading addresses from CSV...")
if not checker.load_from_csv("addresses.csv"):
    print("CSV not found. Extracting...")
    checker.extract_addresses_with_btcposbal2csv(output_csv="addresses.csv")

print(f"Loaded {len(checker.address_balances)} addresses")

# Generate vanity addresses
generator = CPUGenerator(prefix="1Bitcoin", case_sensitive=False)

print("Generating vanity addresses...")
while True:
    result = generator.generate_single()
    if checker.get_balance(result['address']) > 0:
        print(f"\n🎉 FOUND FUNDED ADDRESS!")
        print(f"Address: {result['address']}")
        print(f"Balance: {checker.get_balance(result['address'])} satoshis")
        break
```

## Performance Comparison

| Method | First Load | Subsequent Loads | Memory |
|--------|-----------|------------------|--------|
| btcposbal2csv → CSV | 2-5 min | 5-30 sec (CSV load) | Low |
| Direct plyvel | 5-30 min | 5-30 min | 500MB-2GB |

**Recommendation:** Use btcposbal2csv once to create CSV, then load CSV for instant access.

## Troubleshooting

### "btcposbal2csv not found"

**Problem:** The tool is not installed or not in PATH.

**Solution:**
```bash
# Check if installed
which btcposbal2csv

# If not found, install it:
git clone https://github.com/graymauser/btcposbal2csv
cd btcposbal2csv
make
sudo cp btcposbal2csv /usr/local/bin/

# Or provide full path in Python:
checker.extract_addresses_with_btcposbal2csv(
    btcposbal2csv_path="/path/to/btcposbal2csv"
)
```

### "Database locked"

**Problem:** Bitcoin Core is still running.

**Solution:**
```bash
# Stop Bitcoin Core
bitcoin-cli stop

# Wait for it to fully stop
sleep 10

# Then extract
btcposbal2csv ~/.bitcoin addresses.csv
```

### "Empty CSV" or "No addresses found"

**Problem:** Bitcoin Core is not fully synced.

**Solution:**
1. Check Bitcoin Core sync status:
   ```bash
   bitcoin-cli getblockchaininfo | grep verificationprogress
   ```
2. Wait for full sync (verificationprogress = 0.9999+)
3. Try extraction again

### "Permission denied"

**Problem:** No permission to read Bitcoin Core data directory.

**Solution:**
```bash
# Option 1: Run as user that owns Bitcoin Core data
sudo -u bitcoin btcposbal2csv /path/to/.bitcoin addresses.csv

# Option 2: Adjust permissions (careful!)
sudo chmod -R a+r ~/.bitcoin/chainstate/
```

## CSV File Format

btcposbal2csv generates CSV files in this format:

```csv
address,balance
1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa,5000000000
bc1qxy2kgdygjrsqtzq2n0yrf2493p83kkfjhx0wlh,100000
3J98t1WpEZ73CNmYviecrnyiWrnqRhWNLy,2500000
```

- **Column 1 (address):** Bitcoin address (any type)
- **Column 2 (balance):** Balance in satoshis (integer)

You can load this with:
```python
checker.load_from_csv("addresses.csv")
```

## Best Practices

1. **Extract once, reuse many times**: Create CSV once, then load from CSV for subsequent runs
2. **Stop Bitcoin Core first**: Always stop Bitcoin Core before extraction to avoid database locks
3. **Keep CSV updated**: Re-extract periodically (daily/weekly) to get new addresses
4. **Archive snapshots**: Save dated CSVs for historical analysis
5. **Compress large files**: Use `gzip` to compress large CSV files:
   ```bash
   gzip addresses.csv  # Creates addresses.csv.gz
   # Python can read gzipped CSVs with minor code changes
   ```

## Next Steps

- **Full documentation**: See [BTCPOSBAL2CSV_INTEGRATION.md](BTCPOSBAL2CSV_INTEGRATION.md)
- **Examples**: Run `python -m vanitygen_py.example_btcposbal2csv`
- **Bitcoin Core integration**: See [BITCOIN_CORE_BALANCE_CHECKING.md](BITCOIN_CORE_BALANCE_CHECKING.md)

## Quick Reference Commands

```bash
# Extract addresses
btcposbal2csv ~/.bitcoin addresses.csv

# Check CSV size and line count
ls -lh addresses.csv
wc -l addresses.csv

# View first few addresses
head -10 addresses.csv

# Count total addresses
tail -n +2 addresses.csv | wc -l  # Exclude header

# Search for specific address
grep "1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa" addresses.csv

# Compress CSV
gzip addresses.csv
```

## Python Quick Reference

```python
from vanitygen_py.balance_checker import BalanceChecker

# Method 1: Auto-extract (slow first time)
checker = BalanceChecker()
checker.extract_addresses_with_btcposbal2csv()

# Method 2: Extract to file (slow)
checker = BalanceChecker()
checker.extract_addresses_with_btcposbal2csv(output_csv="addresses.csv")

# Method 3: Load from existing CSV (fast!)
checker = BalanceChecker()
checker.load_from_csv("addresses.csv")

# Check balance
balance = checker.get_balance("1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa")
print(f"Balance: {balance} satoshis")

# Get stats
print(f"Total addresses: {len(checker.address_balances)}")
print(f"Total BTC: {sum(checker.address_balances.values()) / 100000000:.8f}")
```
