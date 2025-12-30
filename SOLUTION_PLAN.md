# GPU Bitcoin Address Generator - Solution Plan

## Problem Summary

The user wants GPU-only mode where:
1. **GPU generates private keys and addresses** (very fast)
2. **GPU checks against a funded address list** (loaded in GPU memory)
3. **CPU periodically verifies** GPU EC correctness (every 10K/100K/1M addresses)
4. **GUI shows TWO separate counters**:
   - "Keys Generated" (total keys generated on GPU)
   - "Keys Checked" (keys checked against funded list)

## Current Issues

1. **EC Implementation Concerns**: Multiple attempts at fixing EC operations, uncertain if current implementation is correct
2. **Missing Separate Counters**: Only one counter shown (total keys)
3. **CPU Sampling May Be Broken**: EC verification sampling exists but might not be working

## Solution Approach

### Phase 1: Verify/Fix GPU EC Operations

The current `gpu_kernel.cl` has EC math from `calc_addrs.cl` integrated. Need to verify it works:
- Test GPU-generated addresses against CPU-generated addresses
- Use the proven `calc_addrs.cl` EC operations
- Ensure private key → public key → address pipeline is correct

### Phase 2: Add Separate Counter Tracking

Modify `GPUGenerator` to track:
- `keys_generated`: Total keys generated on GPU
- `keys_checked`: Keys checked against funded list (= keys_generated when checking every key, or sampled count if only checking periodically)

In GPU-only mode with balance checking:
- Every key is generated → `keys_generated++`
- Every key is checked against list → `keys_checked++`
- With sampling: Only sampled keys increment `keys_checked`

### Phase 3: Fix/Implement CPU Sampling

The user wants CPU to verify GPU EC correctness every N keys:
- Generate same key on GPU and CPU
- Compare pubkeys and addresses
- Log results to GUI

Current code has `ec_check_interval` but needs testing/fixing.

### Phase 4: Update GUI

Add two separate labels:
- "Keys Generated: X"
- "Keys Checked: Y"

Update `GeneratorThread` to emit both values.

##Implementation Plan

### 1. gpu_generator.py Changes

```python
class GPUGenerator:
    def __init__(self, ...):
        # Add separate counters
        self.keys_generated = 0  # Total keys generated
        self.keys_checked = 0     # Keys checked against funded list
        
    def get_stats(self):
        # Return both counters
        return {
            'keys_generated': self.keys_generated,
            'keys_checked': self.keys_checked
        }
```

### 2. gui.py Changes

```python
class GeneratorThread(QThread):
    # Change signal to include both counters
    stats_updated = Signal(int, int, float)  # generated, checked, speed
    
    def run(self):
        # Emit both stats
        stats = self.generator.get_stats()
        self.stats_updated.emit(
            stats['keys_generated'],
            stats['keys_checked'],
            speed
        )

class VanityGenGUI(QMainWindow):
    def update_stats(self, keys_generated, keys_checked, speed):
        self.stats_label.setText(
            f"Keys Generated: {keys_generated:,} | "
            f"Keys Checked: {keys_checked:,} | "
            f"Speed: {speed:.2f} keys/s"
        )
```

### 3. GPU Kernel Verification

Create test to verify GPU EC:
- Generate 1000 random keys
- Compute addresses on GPU and CPU
- Compare all addresses
- If any mismatch → GPU EC is broken
- If all match → GPU EC is correct

### 4. CPU Sampling Implementation

In `_search_loop_gpu_only()`:
```python
# Every N keys, sample one and verify on CPU
if self.ec_check_interval and (self.keys_generated % self.ec_check_interval == 0):
    # Get GPU pubkey for current key
    gpu_pubkey = ... # from GPU
    
    # Compute same key on CPU
    cpu_key = BitcoinKey(private_key_bytes)
    cpu_pubkey = cpu_key.get_public_key()
    
    # Compare
    if gpu_pubkey == cpu_pubkey:
        self.ec_check_queue.put((check_index, True, None))
    else:
        self.ec_check_queue.put((check_index, False, {...}))
```

## Files to Modify

1. `vanitygen_py/gpu_generator.py` - Add counters, fix sampling
2. `vanitygen_py/gui.py` - Update signals, labels, stats display
3. `vanitygen_py/gpu_kernel.cl` - Verify/fix EC operations if needed
4. Create test: `test_gpu_ec_verification.py`

## Testing Plan

1. Run EC verification test → confirms GPU EC is correct
2. Start GPU-only generation → verify counters increment properly
3. Enable EC sampling → verify CPU checks run and pass
4. Load funded list → verify balance checking works
5. Check GUI → verify both counters display correctly
