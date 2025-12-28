# Chainstate Network Address Encoding Fix

## Summary

This fix addresses a critical issue where the BalanceChecker was incorrectly encoding addresses from Bitcoin Core chainstate data. The problem was that addresses were always being encoded using **mainnet** parameters, regardless of which Bitcoin network the chainstate belonged to (testnet, regtest, or signet).

## The Problem

### What is in Chainstate?

The user's concern was correct: **the chainstate database does NOT contain addresses directly**. Instead, it contains:

- **scriptPubKey**: The locking script for each UTXO (Unspent Transaction Output)
- **Metadata**: Version, block height, coinbase flag, and amount (compressed format)

### How Addresses are Derived

Addresses are **derived** from scriptPubKeys through a network-specific encoding process:

1. **P2PKH addresses** (`1...` for mainnet, `m.../n...` for testnet):
   - Extract 20-byte public key hash from script
   - Encode with Base58Check using a network-specific version byte
   - Mainnet: version `0x00` → addresses start with `1`
   - Testnet: version `0x6f` → addresses start with `m` or `n`

2. **P2SH addresses** (`3...` for mainnet, `2...` for testnet):
   - Extract 20-byte script hash from script
   - Encode with Base58Check using a network-specific version byte
   - Mainnet: version `0x05` → addresses start with `3`
   - Testnet: version `0xc4` → addresses start with `2`

3. **Witness addresses** (`bc1...` for mainnet, `tb1...` for testnet):
   - Extract witness program from script
   - Encode with Bech32 using a network-specific Human-Readable Part (HRP)
   - Mainnet: HRP `bc` → addresses start with `bc1`
   - Testnet: HRP `tb` → addresses start with `tb1`
   - Regtest: HRP `bcrt` → addresses start with `bcrt1`

### The Bug

Before this fix, the code **hardcoded mainnet encoding parameters**:

```python
# OLD CODE - ALWAYS used mainnet
def _extract_address_from_script(self, script):
    if (len(script) == 25 and script[0] == 0x76 ...):
        pubkey_hash = script[3:23]
        return base58check_encode(0, pubkey_hash)  # ❌ Always version 0x00 (mainnet)
    
    if (len(script) == 23 and script[0] == 0xa9 ...):
        script_hash = script[2:22]
        return base58check_encode(5, script_hash)  # ❌ Always version 0x05 (mainnet)
    
    if (len(script) == 22 and script[0] == 0x00 ...):
        witness_program = script[2:22]
        return bech32_encode('bc', 0, list(witness_program))  # ❌ Always 'bc' (mainnet)
```

**Impact**: When loading from a testnet chainstate, addresses were incorrectly encoded as mainnet addresses. This meant:
- Generating testnet vanity addresses
- Checking them against a testnet chainstate
- **The addresses wouldn't match because they were encoded with wrong parameters!**

## The Fix

### 1. Network Configuration

Added a `NETWORKS` dictionary with correct parameters for all Bitcoin networks:

```python
NETWORKS = {
    'mainnet': {
        'p2pkh_version': 0x00,
        'p2sh_version': 0x05,
        'bech32_hrp': 'bc',
    },
    'testnet': {
        'p2pkh_version': 0x6f,    # ❌ Was using 0x00 before
        'p2sh_version': 0xc4,     # ❌ Was using 0x05 before
        'bech32_hrp': 'tb',        # ❌ Was using 'bc' before
    },
    'regtest': {
        'p2pkh_version': 0x6f,
        'p2sh_version': 0xc4,
        'bech32_hrp': 'bcrt',
    },
    'signet': {
        'p2pkh_version': 0x6f,
        'p2sh_version': 0xc4,
        'bech32_hrp': 'tb',
    }
}
```

### 2. Network Detection

Added `detect_network_from_path()` to automatically detect network from chainstate path:

```python
def detect_network_from_path(path: str) -> str:
    """Detect Bitcoin network from chainstate path."""
    parts = os.path.normpath(path).split(os.sep)
    for part in parts:
        part_lower = part.lower()
        if part_lower == 'testnet3':
            return 'testnet'
        elif part_lower == 'regtest':
            return 'regtest'
        elif part_lower == 'signet':
            return 'signet'
    return 'mainnet'
```

Examples:
- `/home/user/.bitcoin/chainstate` → `mainnet`
- `/home/user/.bitcoin/testnet3/chainstate` → `testnet`
- `/home/user/.bitcoin/regtest/chainstate` → `regtest`
- `/home/user/.bitcoin/signet/chainstate` → `signet`

### 3. Network-Aware Address Extraction

Updated `_extract_address_from_script()` to accept network parameter:

```python
def _extract_address_from_script(self, script, network: Optional[str] = None):
    # Get network configuration
    if network is None:
        network = self.network
    if network not in NETWORKS:
        network = 'mainnet'
    
    net_config = NETWORKS[network]
    
    # P2PKH - now uses network-specific version
    if (len(script) == 25 and script[0] == 0x76 ...):
        pubkey_hash = script[3:23]
        return base58check_encode(net_config['p2pkh_version'], pubkey_hash)
    
    # P2SH - now uses network-specific version
    if (len(script) == 23 and script[0] == 0xa9 ...):
        script_hash = script[2:22]
        return base58check_encode(net_config['p2sh_version'], script_hash)
    
    # Witness - now uses network-specific HRP
    if (len(script) == 22 and script[0] == 0x00 ...):
        witness_program = script[2:22]
        return bech32_encode(net_config['bech32_hrp'], 0, list(witness_program))
```

### 4. Automatic Network Detection in Loading

Updated `load_from_bitcoin_core()` to detect network automatically:

```python
def load_from_bitcoin_core(self, path=None):
    # ... (path detection code) ...
    
    path = selected_path
    self._debug(f"Chainstate directory found at: {path}")
    
    # ❌ NEW: Detect network from path
    self.network = detect_network_from_path(path)
    self._debug(f"Detected network: {self.network}")
    
    # Continue with UTXO parsing...
    for key, value in db:
        # ... extract scriptPubKey ...
        # ... now uses self.network for encoding ...
        address = self._extract_address_from_script(script_pubkey)
```

### 5. Manual Network Setting (Optional)

Added `set_network()` for when loading from files:

```python
checker = BalanceChecker()
checker.set_network('testnet')  # Manually set network
checker.load_addresses('testnet_addresses.txt')
```

## Testing

Comprehensive unit tests added to verify:

1. **Network address encoding**: Same script produces different addresses per network
2. **P2PKH encoding**: Correct version bytes and address prefixes
3. **P2SH encoding**: Correct version bytes and address prefixes
4. **Witness encoding**: Correct HRP for all networks
5. **Network detection**: Correctly identifies network from paths
6. **Network configurations**: All parameters are correct

Run tests:
```bash
cd /home/engine/project
python -m vanitygen_py.test_balance_checker
```

## Demonstration

Run the demonstration script to see the issue and fix in action:

```bash
python NETWORK_FIX_DEMO.py
```

Example output:
```
P2PKH Address Encoding Example
ScriptPubKey (P2PKH): 76a914000102030405060708090a0b0c0d0e0f1011121388ac
mainnet   : 112D2adLM3UKy4Z4giRbReR6gjWuvHUqB   (version: 0x00)
testnet   : mfWyW5fc9NUj75YAnFgoRLrjxgLDn2MMth  (version: 0x6f)
regtest   : mfWyW5fc9NUj75YAnFgoRLrjxgLDn2MMth  (version: 0x6f)

P2SH Address Encoding Example
ScriptPubKey (P2SH): a914000102030405060708090a0b0c0d0e0f1011121387
mainnet   : 31h38a54tFMrR8kzBnP2241MFD2EUHtGha  (version: 0x05)
testnet   : 2MsFFCK16VhsCcvPXruztdzzcTZEQCbNKjJ ( (version: 0xc4)
```

## Files Modified

1. **vanitygen_py/balance_checker.py**
   - Added `NETWORKS` configuration dictionary
   - Added `detect_network_from_path()` function
   - Updated `BalanceChecker.__init__()` to add `network` attribute
   - Updated `_extract_address_from_script()` to accept `network` parameter
   - Updated `load_from_bitcoin_core()` to auto-detect network
   - Added `set_network()` and `get_network()` methods

2. **vanitygen_py/test_balance_checker.py**
   - Added tests for network detection
   - Added tests for network-specific address encoding
   - Added tests for all Bitcoin networks (mainnet, testnet, regtest, signet)
   - Updated imports to include new functions

3. **NETWORK_FIX_DEMO.py** (new)
   - Demonstration script showing the issue and fix
   - Visual comparison of address encoding across networks

## Backward Compatibility

The fix is **fully backward compatible**:

1. Default network is `mainnet` (same as before)
2. Existing code that doesn't specify network will work unchanged
3. Network detection is automatic when loading from Bitcoin Core
4. Manual network setting is optional

## Usage

### Automatic (Recommended)

```python
from vanitygen_py.balance_checker import BalanceChecker

checker = BalanceChecker()
# Network is automatically detected from chainstate path
if checker.load_from_bitcoin_core():
    print(f"Loaded addresses from {checker.get_network()} network")
```

### Manual (For File Loading)

```python
from vanitygen_py.balance_checker import BalanceChecker

checker = BalanceChecker()
checker.set_network('testnet')  # Specify network manually
checker.load_addresses('testnet_addresses.txt')
```

## Summary

- **Issue**: Addresses were always encoded as mainnet, breaking testnet/regtest/signet balance checking
- **Root Cause**: Hardcoded network encoding parameters
- **Fix**: Added network detection, network configuration, and network-aware address encoding
- **Impact**: Balance checking now works correctly for all Bitcoin networks
- **Backward Compatibility**: Fully maintained
