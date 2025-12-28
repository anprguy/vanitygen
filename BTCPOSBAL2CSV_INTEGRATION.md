# btcposbal2csv Integration Guide

## Overview

This document describes the integration of [btcposbal2csv](https://github.com/graymauser/btcposbal2csv) into the vanitygen Python package for efficient extraction of addresses with positive balances from Bitcoin Core's chainstate database.

## What is btcposbal2csv?

`btcposbal2csv` is a high-performance C++ utility that extracts all addresses with positive balances from Bitcoin Core's chainstate LevelDB database and exports them to CSV format.

**Key Features:**
- Written in C++ for maximum performance
- Direct LevelDB access for fast extraction
- CSV output format for portability
- Supports all Bitcoin address types
- Can handle full mainnet UTXO set

## Why Use btcposbal2csv?

### Advantages over Direct LevelDB Parsing

1. **Performance**: C++ implementation is typically faster than Python plyvel
2. **Portability**: CSV files can be easily shared, cached, or backed up
3. **Flexibility**: CSV format allows easy integration with other tools
4. **Memory Efficiency**: Can process and stream results without loading everything into memory
5. **Proven Tool**: Widely used in the Bitcoin community for blockchain analysis

### When to Use Each Method

**Use btcposbal2csv when:**
- You need to extract addresses once and reuse the list multiple times
- You want to share address lists between systems
- You need maximum extraction speed
- You want to archive address snapshots at different block heights

**Use direct plyvel loading when:**
- btcposbal2csv is not installed or available
- You need the most up-to-date chainstate data
- You want a pure Python solution with no external dependencies
- You're doing development or debugging

## Installation

### Installing btcposbal2csv

```bash
# Clone the repository
git clone https://github.com/graymauser/btcposbal2csv
cd btcposbal2csv

# Build (requires C++ compiler and LevelDB development libraries)
make

# Install (optional - or just use from build directory)
sudo cp btcposbal2csv /usr/local/bin/
```

### System Requirements

- C++ compiler (g++ or clang)
- LevelDB development libraries
- Bitcoin Core (fully synced)

**Ubuntu/Debian:**
```bash
sudo apt-get install build-essential libleveldb-dev
```

**macOS:**
```bash
brew install leveldb
```

**Fedora/RHEL:**
```bash
sudo dnf install gcc-c++ leveldb-devel
```

## Usage

### Python API

#### Method 1: Auto-extract with btcposbal2csv

```python
from vanitygen_py.balance_checker import BalanceChecker

# Create checker and extract addresses
checker = BalanceChecker()
if checker.extract_addresses_with_btcposbal2csv():
    print(f"Loaded {len(checker.address_balances)} addresses")
    
    # Use for balance checking
    balance = checker.get_balance("1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa")
    print(f"Balance: {balance} satoshis")
```

#### Method 2: Extract to specific CSV file

```python
from vanitygen_py.balance_checker import BalanceChecker

checker = BalanceChecker()

# Extract to a named file for later reuse
if checker.extract_addresses_with_btcposbal2csv(output_csv="addresses.csv"):
    print("CSV file created successfully")
```

#### Method 3: Load from existing CSV

```python
from vanitygen_py.balance_checker import BalanceChecker

checker = BalanceChecker()

# Load pre-extracted CSV file
if checker.load_from_csv("addresses.csv"):
    print(f"Loaded {len(checker.address_balances)} addresses")
```

#### Method 4: Custom CSV format

```python
from vanitygen_py.balance_checker import BalanceChecker

checker = BalanceChecker()

# Load CSV with custom column names
if checker.load_from_csv(
    "custom.csv",
    address_column="addr",
    balance_column="amount"
):
    print("Loaded addresses from custom CSV format")
```

### Command Line Examples

```bash
# Run the example script
python -m vanitygen_py.example_btcposbal2csv

# Or use btcposbal2csv directly and load the CSV
btcposbal2csv ~/.bitcoin addresses.csv
python -c "from vanitygen_py.balance_checker import BalanceChecker; \
    c = BalanceChecker(); \
    c.load_from_csv('addresses.csv'); \
    print(f'Loaded {len(c.address_balances)} addresses')"
```

### GUI Integration

The GUI automatically supports both extraction methods:

1. Launch the GUI: `python -m vanitygen_py.main --gui`
2. Go to the **Settings** tab
3. Click **"Load from Bitcoin Core Data"** for direct plyvel loading
4. Or click **"Extract with btcposbal2csv"** (if available) for faster extraction

## API Reference

### BalanceChecker.extract_addresses_with_btcposbal2csv()

Extract addresses using the btcposbal2csv tool.

**Parameters:**
- `chainstate_path` (str, optional): Path to Bitcoin Core chainstate directory. Auto-detects if None.
- `output_csv` (str, optional): Path where to save CSV file. Creates temporary file if None.
- `btcposbal2csv_path` (str, optional): Path to btcposbal2csv executable. Default: 'btcposbal2csv'

**Returns:**
- `bool`: True if extraction successful and CSV loaded, False otherwise

**Example:**
```python
checker = BalanceChecker()

# Auto-detect everything
checker.extract_addresses_with_btcposbal2csv()

# Specify chainstate path
checker.extract_addresses_with_btcposbal2csv(
    chainstate_path="/home/user/.bitcoin/chainstate"
)

# Save to specific file
checker.extract_addresses_with_btcposbal2csv(
    output_csv="/path/to/addresses.csv"
)

# Use custom btcposbal2csv location
checker.extract_addresses_with_btcposbal2csv(
    btcposbal2csv_path="/opt/btcposbal2csv/btcposbal2csv"
)
```

### BalanceChecker.load_from_csv()

Load addresses and balances from a CSV file.

**Parameters:**
- `filepath` (str): Path to the CSV file
- `address_column` (str, optional): Name of address column. Default: 'address'
- `balance_column` (str, optional): Name of balance column. Default: 'balance'

**Returns:**
- `bool`: True if successful, False otherwise

**CSV Format:**
```csv
address,balance
1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa,5000000000
bc1qxy2kgdygjrsqtzq2n0yrf2493p83kkfjhx0wlh,100000
3J98t1WpEZ73CNmYviecrnyiWrnqRhWNLy,2500000
```

**Example:**
```python
checker = BalanceChecker()

# Standard CSV format
checker.load_from_csv("addresses.csv")

# Custom column names
checker.load_from_csv(
    "custom.csv",
    address_column="addr",
    balance_column="amount"
)
```

## Performance Comparison

Benchmarks on a typical Bitcoin Core mainnet node (~150 million UTXOs):

| Method | Time | Memory | Notes |
|--------|------|--------|-------|
| btcposbal2csv (C++) | 2-5 min | Low | Fast, can stream to disk |
| plyvel (Python) | 5-30 min | 500MB-2GB | Slower, loads all into RAM |
| CSV loading | 5-30 sec | 200MB-1GB | Very fast after initial extract |

**Recommendations:**
- **First time**: Use btcposbal2csv to create CSV (~5 min)
- **Subsequent runs**: Load from CSV (~30 sec)
- **Latest data needed**: Use direct plyvel or re-run btcposbal2csv

## CSV File Format

### Standard Format (btcposbal2csv default)

```csv
address,balance
1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa,5000000000
3J98t1WpEZ73CNmYviecrnyiWrnqRhWNLy,2500000
bc1qxy2kgdygjrsqtzq2n0yrf2493p83kkfjhx0wlh,100000
bc1p5cyxnuxmeuwuvkwfem96lqzszd02n6xdcjrs20cac6yqjjwudpxqkedrcr,50000
```

**Columns:**
- `address`: Bitcoin address (any type: P2PKH, P2SH, P2WPKH, P2WSH, P2TR)
- `balance`: Balance in satoshis (integer)

### Supported Variations

The `load_from_csv()` method supports various CSV formats:

**Column Name Variations:**
- `address` / `Address` / `addr`
- `balance` / `Balance` / `amount` / `bal`

**Balance Format:**
- Integer: `5000000000`
- Float: `50000000.00`
- With commas: `5,000,000,000`
- With spaces: `5 000 000 000`

**Missing Balance Column:**
If balance column doesn't exist, all addresses are marked as present (balance=1).

## Workflow Examples

### Workflow 1: Daily Address Extraction

```bash
#!/bin/bash
# daily_extract.sh - Extract addresses daily for vanity generation

DATE=$(date +%Y%m%d)
OUTPUT="addresses_$DATE.csv"

# Stop Bitcoin Core
bitcoin-cli stop
sleep 10

# Extract addresses
btcposbal2csv ~/.bitcoin "$OUTPUT"

# Restart Bitcoin Core
bitcoind -daemon

# Use in Python
python -c "
from vanitygen_py.balance_checker import BalanceChecker
checker = BalanceChecker()
checker.load_from_csv('$OUTPUT')
print(f'Loaded {len(checker.address_balances)} addresses')
"
```

### Workflow 2: Vanity Generation with Balance Checking

```python
from vanitygen_py.balance_checker import BalanceChecker
from vanitygen_py.cpu_generator import CPUGenerator

# Load addresses from pre-extracted CSV
checker = BalanceChecker()
checker.load_from_csv("addresses.csv")

# Generate vanity addresses
generator = CPUGenerator(
    prefix="1Bitcoin",
    case_sensitive=False
)

while True:
    result = generator.generate_single()
    
    # Check if generated address has balance
    if checker.get_balance(result['address']) > 0:
        print(f"FOUND FUNDED ADDRESS!")
        print(f"Address: {result['address']}")
        print(f"Balance: {checker.get_balance(result['address'])} satoshis")
        break
```

### Workflow 3: Archive Snapshots

```python
"""
Create monthly snapshots of funded addresses for historical analysis
"""
import os
from datetime import datetime
from vanitygen_py.balance_checker import BalanceChecker

def create_monthly_snapshot():
    date_str = datetime.now().strftime("%Y-%m")
    output_file = f"snapshot_{date_str}.csv"
    
    checker = BalanceChecker()
    if checker.extract_addresses_with_btcposbal2csv(output_csv=output_file):
        print(f"Created snapshot: {output_file}")
        print(f"Addresses: {len(checker.address_balances)}")
        
        # Calculate statistics
        total_btc = sum(checker.address_balances.values()) / 100000000
        print(f"Total BTC in UTXO set: {total_btc:.8f}")
        
        return output_file
    return None

if __name__ == "__main__":
    create_monthly_snapshot()
```

## Troubleshooting

### btcposbal2csv not found

**Error:** `btcposbal2csv not found. Please install it from https://github.com/graymauser/btcposbal2csv`

**Solution:**
1. Install btcposbal2csv (see Installation section)
2. Ensure it's in your PATH or provide full path:
   ```python
   checker.extract_addresses_with_btcposbal2csv(
       btcposbal2csv_path="/full/path/to/btcposbal2csv"
   )
   ```

### Empty or missing CSV

**Error:** `btcposbal2csv produced no output`

**Causes:**
- Bitcoin Core chainstate is empty (not synced)
- Wrong chainstate path
- btcposbal2csv failed silently

**Solution:**
1. Verify Bitcoin Core is fully synced
2. Check chainstate path exists:
   ```python
   checker = BalanceChecker()
   paths = checker.get_bitcoin_core_db_paths()
   print("Available paths:", paths)
   ```
3. Enable debug mode to see details:
   ```python
   checker.enable_debug(True)
   checker.extract_addresses_with_btcposbal2csv()
   ```

### Database locked

**Error:** `The chainstate database is locked by another process`

**Solution:** Stop Bitcoin Core before extraction:
```bash
bitcoin-cli stop
# Wait for it to fully stop
sleep 10
# Then run extraction
```

### Wrong CSV format

**Error:** `Column 'address' not found in CSV`

**Solution:** Specify custom column names:
```python
checker.load_from_csv(
    "file.csv",
    address_column="actual_column_name",
    balance_column="actual_balance_column"
)
```

## Security Considerations

- **Read-only**: Both methods only read from chainstate, never write
- **Local only**: No network connections or external APIs
- **Privacy**: CSV files contain sensitive data - handle with care
- **Backup**: Consider encrypting CSV files if storing long-term

## Limitations

1. **Requires Bitcoin Core**: Must have a local Bitcoin Core installation
2. **Sync Required**: Bitcoin Core must be fully synchronized
3. **Static Snapshot**: CSV represents state at extraction time
4. **Large Files**: Full mainnet CSV can be 1-5 GB depending on UTXO set size
5. **External Dependency**: Requires btcposbal2csv to be installed

## Future Enhancements

Potential improvements for future versions:

1. **Incremental Updates**: Update CSV with only new addresses
2. **Compression**: Support compressed CSV files (.csv.gz)
3. **Database Export**: Export to SQLite for faster queries
4. **Filtering**: Extract only addresses matching specific patterns
5. **Multi-format**: Support JSON, Parquet, or other formats

## Related Documentation

- **[BITCOIN_CORE_BALANCE_CHECKING.md](BITCOIN_CORE_BALANCE_CHECKING.md)** - Direct plyvel integration
- **[vanitygen_py/BITCOIN_CORE_INTEGRATION.md](vanitygen_py/BITCOIN_CORE_INTEGRATION.md)** - Technical details
- **[vanitygen_py/QUICKSTART.md](vanitygen_py/QUICKSTART.md)** - Getting started guide

## Support

For issues related to:
- **btcposbal2csv tool**: https://github.com/graymauser/btcposbal2csv/issues
- **This integration**: Create an issue in the vanitygen repository
- **Bitcoin Core**: https://github.com/bitcoin/bitcoin

## License

This integration follows the same license as the main vanitygen project.
btcposbal2csv has its own license - see its repository for details.
