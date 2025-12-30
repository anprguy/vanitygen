# GUI Startup Fix

## Issue

When starting the GUI, it crashed with:

```python
File "/home/server/Downloads/vanitygen-master7/vanitygen_py/gui.py", line 113, in run
    self.generator.set_balance_checker(self.balance_checker)
File "/home/server/Downloads/vanitygen-master7/vanitygen_py/hybrid_generator.py", line 350, in set_balance_checker
    print(f"[HybridGenerator] Loaded {len(self.check_hash160s)} addresses for matching")
TypeError: object of type 'NoneType' has no len()
```

## Root Cause

In `hybrid_generator.py`, the `set_balance_checker()` method tried to print the length of `self.check_hash160s` without checking if it was `None` first.

When:
1. GUI starts with Hybrid Mode selected
2. No balance checker is loaded yet
3. `set_balance_checker()` is called with an empty or not-yet-loaded balance checker
4. `_build_hash160_set()` sets `self.check_hash160s = None` (line 391)
5. Code tries to print `len(None)` → crash

## Fix Applied

**File**: `vanitygen_py/hybrid_generator.py`

**Changes**:

### Before (line 347-350):
```python
if balance_checker and balance_checker.is_loaded:
    print("[HybridGenerator] Loading addresses for matching...")
    self._build_hash160_set()
    print(f"[HybridGenerator] Loaded {len(self.check_hash160s)} addresses for matching")
```

### After (line 347-357):
```python
if balance_checker and balance_checker.is_loaded:
    print("[HybridGenerator] Loading addresses for matching...")
    self._build_hash160_set()
    # Handle case where check_hash160s might be None
    if self.check_hash160s:
        print(f"[HybridGenerator] Loaded {len(self.check_hash160s)} addresses for matching")
    else:
        print("[HybridGenerator] No addresses loaded (check_hash160s is None)")
else:
    # No balance checker or not loaded
    self.check_hash160s = None
```

## What This Fixes

✅ GUI starts without crashing  
✅ Hybrid Mode can be selected even without loading addresses  
✅ Clear message when no addresses are loaded  
✅ Proper initialization of `check_hash160s` to None when no balance checker

## Test Again

```bash
cd ~/Downloads/vanitygen-master7
python3 -m vanitygen_py.main --gui
```

**Expected**: GUI starts successfully!

Then:
1. Settings tab → Mode → "Hybrid (GPU+coincurve) ✓"
2. (Optional) Load address list if you have one
3. Progress tab → Start
4. GUI should work without crashing

## Notes

- It's OK to use Hybrid Mode without loading a balance checker
- In that case, it will just generate random addresses (useful for vanity search)
- To find funded addresses, you need to load a balance checker first:
  - Settings → "Load Bitcoin Core Chainstate"
  - Or "Load CSV File"
  - Or "Load btcposbal2csv Output"

## Status

✅ **FIXED** - GUI should now start successfully with Hybrid Mode

---

**What was changed**: Added None check before printing length of check_hash160s  
**File modified**: vanitygen_py/hybrid_generator.py (lines 347-357)  
**Impact**: GUI no longer crashes on startup
