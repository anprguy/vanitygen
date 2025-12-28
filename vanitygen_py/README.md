# Python Bitcoin Vanity Address Generator

A Python-based Bitcoin vanity address generator that supports both CPU and GPU acceleration.

## Features
- CPU-based generation: Works on any system with Python installed
- GPU acceleration: OpenCL support (via pyopencl)
- Multiple address types: P2PKH, P2WPKH (SegWit), P2SH-P2WPKH
- Vanity pattern matching
- Progress tracking: Real-time speed statistics
- GUI Interface: PySide6-based graphical interface
- Balance Checking: Check against local UTXO set

## Requirements

### System Dependencies

Before installing Python packages, you may need to install system-level development libraries.

**Linux (Ubuntu/Debian):**
```bash
sudo apt-get update
sudo apt-get install ocl-icd-opencl-dev opencl-headers libleveldb-dev build-essential
```

**macOS:**
```bash
brew install opencl-headers leveldb
```

### Python Packages

```
pip install -r requirements.txt
```

## Usage
### GUI
```
python -m vanitygen_py.main --gui
```

### CLI
```
python -m vanitygen_py.main --prefix 1ABC
```

## Balance Checking

The vanity address generator now supports **real-time balance checking** against your local Bitcoin Core blockchain data. Features include:

- **Network-aware address encoding**: Automatically detects mainnet/testnet/regtest/signet
- **Multiple address types**: P2PKH, P2SH, P2WPKH, P2WSH, P2TR
- **Fast in-memory lookups**: All funded addresses cached after initial load
- **Multiple extraction methods**: Direct LevelDB (plyvel), btcposbal2csv, or CSV files
- **CSV import/export**: Save and reuse address lists for faster loading
- **Debug mode**: See detailed extraction info including addresses being derived

### Enabling Debug Mode

To see addresses being extracted from chainstate in real-time:

```python
from vanitygen_py.balance_checker import BalanceChecker

checker = BalanceChecker()
checker.enable_debug(True)  # Enable debug mode
if checker.load_from_bitcoin_core():
    print(f"Loaded {len(checker.address_balances)} addresses")
```

Debug output will show:
- Detected Bitcoin network
- UTXO details (version, height, coinbase flag, amount)
- ScriptPubKey for each UTXO
- **Extracted address for each UTXO** ← This shows addresses!
- Summary statistics

### Method 1: Bitcoin Core LevelDB (Recommended)

**Requirements:**
- Bitcoin Core installed and fully synchronized
- Bitcoin Core must be stopped before reading chainstate
- plyvel package (included in requirements.txt)

**Usage:**
1. Launch the GUI: `python -m vanitygen_py.main --gui`
2. Click "Load from Bitcoin Core Data" in the Settings tab
3. The application will:
   - Auto-detect your Bitcoin Core data directory
   - Read the chainstate LevelDB
   - Parse all UTXOs and extract addresses
   - Cache address balances for fast lookups

**Supported Address Types:**
- P2PKH (addresses starting with '1')
- P2SH (addresses starting with '3')
- P2WPKH (addresses starting with 'bc1q')
- P2WSH (addresses starting with 'bc1q')
- P2TR (addresses starting with 'bc1p')

**Bitcoin Core Data Locations:**
- Linux: `~/.bitcoin/chainstate/`
- Linux (Snap): `~/snap/bitcoin-core/common/.bitcoin/chainstate/`
- macOS: `~/Library/Application Support/Bitcoin/chainstate/`
- Windows: `%APPDATA%\Bitcoin\chainstate\`

For detailed documentation, see [BITCOIN_CORE_INTEGRATION.md](BITCOIN_CORE_INTEGRATION.md)

### Method 2: btcposbal2csv (Fast C++ Tool)

**Recommended for best performance!**

[btcposbal2csv](https://github.com/graymauser/btcposbal2csv) is a high-performance C++ tool that quickly extracts all funded addresses from Bitcoin Core's chainstate and exports them to CSV format.

**Benefits:**
- 2-5x faster than direct Python plyvel loading
- CSV output can be cached and reused (instant loading)
- Lower memory usage during extraction
- Portable CSV format for sharing/archiving

**Usage:**
```python
from vanitygen_py.balance_checker import BalanceChecker

# Method A: Auto-extract (detects Bitcoin Core path automatically)
checker = BalanceChecker()
checker.extract_addresses_with_btcposbal2csv()

# Method B: Extract to specific file for reuse
checker.extract_addresses_with_btcposbal2csv(output_csv="addresses.csv")

# Method C: Load from previously extracted CSV
checker.load_from_csv("addresses.csv")
```

**Installation:**
```bash
git clone https://github.com/graymauser/btcposbal2csv
cd btcposbal2csv
make
sudo cp btcposbal2csv /usr/local/bin/
```

See [BTCPOSBAL2CSV_INTEGRATION.md](../BTCPOSBAL2CSV_INTEGRATION.md) for complete documentation.

### Method 3: Address File

You can also load addresses from a text file (one address per line) or CSV file. This is useful if you prefer not to use Bitcoin Core directly or if you want to use a pre-processed address list.

**Text file:**
```python
checker = BalanceChecker()
checker.load_addresses("addresses.txt")  # One address per line
```

**CSV file:**
```python
checker = BalanceChecker()
checker.load_from_csv("addresses.csv")  # address,balance format
```
