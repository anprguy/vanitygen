# How to Run the GPU EC Correctness Test

## Quick Start

```bash
cd ~/Downloads/vanitygen-master5/vanitygen-master
python test_gpu_ec_correctness.py
```

## What This Test Does

This test **verifies if your GPU generates correct Bitcoin addresses** by:

1. ✓ Generating 100 random private keys
2. ✓ Computing addresses on GPU (using gpu_kernel.cl)
3. ✓ Computing addresses on CPU (using proven BitcoinKey)
4. ✓ Comparing every single address
5. ✓ Reporting matches and mismatches

**Time required**: ~30 seconds

## Expected Output

### If GPU is CORRECT (All Addresses Match):

```
================================================================================
GPU EC CORRECTNESS TEST
================================================================================

This test verifies GPU generates correct Bitcoin addresses
by comparing GPU vs CPU output for the same private keys.

[1] Initializing OpenCL...
    Using device: NVIDIA GeForce RTX 3080

[2] Loading GPU kernel...
    ✓ Kernel compiled successfully

[3] Testing 100 random private keys...

    [GPU] Generating addresses...
    ✓ GPU generated 100 addresses
    [CPU] Verifying addresses...

    ✓ Match #1:
       Address: 1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa
       (GPU and CPU both generated same address)

    ✓ Match #2:
       Address: 1BoatSLRHtKNngkdXEeobR76b53LETtpyT
       (GPU and CPU both generated same address)

    ... (showing first 5 matches)

================================================================================
TEST RESULTS
================================================================================

Total addresses tested: 100
Matches (GPU == CPU):   100
Mismatches:             0

✓✓✓ SUCCESS! ALL ADDRESSES MATCH ✓✓✓

GPU EC operations are CORRECT!
GPU-generated addresses match CPU-generated addresses.
```

**What this means**: Your GPU implementation is correct! You can safely use GPU-only mode.

---

### If GPU is BROKEN (Addresses Don't Match):

```
================================================================================
TEST RESULTS
================================================================================

Total addresses tested: 100
Matches (GPU == CPU):   0
Mismatches:             100

✗✗✗ FAILURE! GPU EC OPERATIONS ARE INCORRECT ✗✗✗

GPU-generated addresses do NOT match CPU-generated addresses.

MISMATCH DETAILS:
--------------------------------------------------------------------------------

Mismatch #1:
  Private Key: a1b2c3d4e5f6...
  GPU Address: 1xyz123...
  CPU Address: 1abc789...
  CPU Pubkey:  02abcd...
  → Same version, different hash (EC or hash issue)

Mismatch #2:
  Private Key: f6e5d4c3b2a1...
  GPU Address: 1qwe456...
  CPU Address: 1rty123...
  CPU Pubkey:  03defg...
  → Same version, different hash (EC or hash issue)

... (up to 10 mismatches shown)

POSSIBLE CAUSES:
1. EC scalar multiplication implementation is incorrect
2. Montgomery domain conversions are wrong
3. Modular inverse implementation has bugs
4. Point normalization (Jacobian → affine) is incorrect
5. Endianness issues (byte order)
6. Hash160 implementation (SHA256 or RIPEMD160)
7. Base58 encoding errors

RECOMMENDATION:
Use Hybrid Mode instead (GPU RNG + coincurve EC)
This guarantees correct addresses using Bitcoin Core's libsecp256k1
```

**What this means**: Your GPU has EC bugs! DO NOT use GPU-only mode - you'll generate invalid addresses!

---

## What To Do Next

### ✅ If Test PASSES (All Match):

You're good! GPU works correctly.

1. Use GPU-only mode safely
2. Enjoy fast address generation
3. No bugs, no worries!

### ✗ If Test FAILS (Mismatches):

**CRITICAL**: Do NOT use GPU-only mode with balance checking!

**Immediate Solution - Use Hybrid Mode**:

1. Open GUI
2. Settings tab
3. Mode → Select "Hybrid (GPU+coincurve) ✓"
4. **This is guaranteed correct** (uses Bitcoin Core's libsecp256k1)
5. Fast enough: 30-100K keys/sec
6. No risk of invalid addresses

**Long-term Solution - Fix GPU EC**:

If you need maximum GPU speed, you must fix the bugs:

1. Read `GPU_KERNEL_FIXES.md` - detailed bug analysis
2. Port proven functions from calc_addrs.cl
3. Re-run test after each fix
4. Iterate until all addresses match

See `EC_IMPLEMENTATION_ANALYSIS.md` for technical details.

---

## Troubleshooting

### Error: "No OpenCL platforms found"

**Cause**: No OpenCL drivers installed or GPU not detected

**Fix**:
1. Install OpenCL drivers for your GPU
2. NVIDIA: Install CUDA
3. AMD: Install ROCm or AMD APP SDK
4. Intel: Install Intel OpenCL runtime

Test with:
```bash
python -c "import pyopencl as cl; print(cl.get_platforms())"
```

### Error: "pyopencl not installed"

**Fix**:
```bash
pip install pyopencl
```

### Error: "Kernel failed to compile"

**Cause**: OpenCL kernel has syntax errors or incompatible features

**Fix**:
1. Check gpu_kernel.cl for errors
2. Update GPU drivers
3. Try different OpenCL platform

### SyntaxError: f-string syntax

**Cause**: Python version < 3.6

**Fix**: Already fixed! The test now uses `.format()` instead of f-strings.

If you still see errors, ensure you're using:
```python
# At top of file
from __future__ import print_function
```

---

## Summary

**This test is CRITICAL** - it tells you if GPU generates valid Bitcoin addresses.

- ✓ **Pass** → Safe to use GPU
- ✗ **Fail** → Use Hybrid Mode or fix bugs

**Run it before using GPU-only mode with real addresses!**

---

**Files**:
- Test: `test_gpu_ec_correctness.py`
- Fixes: `GPU_KERNEL_FIXES.md`
- Analysis: `EC_IMPLEMENTATION_ANALYSIS.md`
- Quick start: `README_PLEASE_READ_FIRST.md`
