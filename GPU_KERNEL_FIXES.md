# GPU Kernel EC Fixes

## Critical Issues Found in gpu_kernel.cl

### Issue #1: Montgomery Multiplication (Lines 68-89)
**Current code** has comment: `// Very simplified carry handling` (line 83)

**Problem**: Carry overflow detection is incomplete. The condition `(t[7] < tea || (t[7] == tea && c > 0))` doesn't properly handle all carry cases.

**Proven implementation from calc_addrs.cl** (lines 521-586):
```c
void bn_mul_mont(bignum *r, bignum *a, bignum *b)
{
    bignum t;
    bn_word tea, teb, c, p, s, m;
    int q;

    c = 0;
    // First multiplication by b->d[0]
    for (int j = 0; j < 8; j++) {
        bn_mul_word(t.d[j], a->d[j], b->d[0], c, p, s);
    }
    tea = c;
    teb = 0;

    // Montgomery reduction step
    c = 0;
    m = t.d[0] * mont_n0[0];
    bn_mul_add_word(t.d[0], modulus[0], m, c, p, s);
    for (int j = 1; j < 8; j++) {
        bn_mul_add_word(t.d[j], modulus[j], m, c, p, s);
        t.d[j-1] = t.d[j];
    }
    t.d[7] = tea + c;
    tea = teb + ((t.d[7] < c) ? 1 : 0);

    // Main loop
    for (q = 1; q < 8; q++) {
        c = 0;
        for (int j = 0; j < 8; j++) {
            bn_mul_add_word(t.d[j], a->d[j], b->d[q], c, p, s);
        }
        tea += c;
        teb = ((tea < c) ? 1 : 0);
        
        c = 0;
        m = t.d[0] * mont_n0[0];
        bn_mul_add_word(t.d[0], modulus[0], m, c, p, s);
        for (int j = 1; j < 8; j++) {
            bn_mul_add_word(t.d[j], modulus[j], m, c, p, s);
            t.d[j-1] = t.d[j];
        }
        t.d[7] = tea + c;
        tea = teb + ((t.d[7] < c) ? 1 : 0);
    }

    // Final reduction
    c = tea || (t.d[7] >= modulus[7]);
    if (c) {
        c = tea | !bn_usub_c(r, &t, modulus);
        if (c)
            return;
    }
    *r = t;
}
```

**Key differences**:
1. Proper tracking of `tea` (top extension accumulator) and `teb` (top extension borrow)
2. Correct carry propagation: `tea = teb + ((t.d[7] < c) ? 1 : 0);`
3. More accurate final reduction condition

### Issue #2: Modular Inverse (Lines 91-112)
**Current code** has suspicious line 108: `while (yc < 0x80000000) yc -= bn_usub_c(&y, &y, modulus);`

**Problem**: Using unsigned comparison to check for "negative" (sign bit). The value `yc` is a `bn_word` (unsigned), so `yc < 0x80000000` is checking if the high bit is clear, not if it's negative. This is fragile and may not work correctly.

**Proven implementation from calc_addrs.cl** (lines 821-922):
```c
void bn_mod_inverse(bignum *r, bignum *n)
{
    bignum a, b, x, y, t;
    int i;

    a = *n;
    for (i = 0; i < 8; i++) {
        b.d[i] = modulus[i];
        x.d[i] = 0;
        y.d[i] = 0;
    }
    x.d[0] = 1;

    bn_word xc = 0;
    bn_word yc = 1;  // Start at 1, not 0

    while (!bn_is_zero(a)) {
        if (bn_is_even(a)) {
            bn_rshift1(&a);
            // If x is odd, add modulus before shifting
            if (bn_is_odd(x)) {
                xc += bn_uadd_c(&x, &x, modulus);
            }
            bn_rshift1(&x);
            x.d[7] |= (xc << 31);
            xc >>= 1;
        } else if (bn_is_even(b)) {
            bn_rshift1(&b);
            // If y is odd, add modulus before shifting  
            if (bn_is_odd(y)) {
                yc += bn_uadd_c(&y, &y, modulus);
            }
            bn_rshift1(&y);
            y.d[7] |= (yc << 31);
            yc >>= 1;
        } else {
            bn_word ac = bn_usub(&t, &a, &b);
            bn_word bc = bn_usub(&b, &b, &a);
            
            if (ac) {
                // a < b, so b = b - a is positive
                a = t;  // a was negative, now it's |a-b|
                // Need to adjust x
                if (xc >= yc) {
                    xc -= yc;
                    bn_usub(&x, &x, &y);
                } else {
                    // Need to borrow from modulus
                    xc = (yc - xc);
                    bn_usub(&t, &y, &x);
                    x = t;
                    if (xc) {
                        bn_uadd_c(&x, &x, modulus);
                        xc--;
                    }
                }
            } else {
                // a >= b, so a = a - b is positive
                // b is already computed
                a = t;
                if (yc >= xc) {
                    yc -= xc;
                    bn_usub(&y, &y, &x);
                } else {
                    yc = (xc - yc);
                    bn_usub(&t, &x, &y);
                    y = t;
                    if (yc) {
                        bn_uadd_c(&y, &y, modulus);
                        yc--;
                    }
                }
            }
        }
    }

    // y contains the inverse
    // Negate if needed (check sign bit in yc)
    if (yc & 1) {
        // Negative, need to compute modulus - y
        bn_usub_c(&y, (bignum*)modulus, &y);
    }
    *r = y;
}
```

**Key differences**:
1. Proper handling of "negative" values using carry words
2. Explicit borrow/carry tracking
3. Correct final negation check

### Issue #3: Scalar Multiplication Initial Setup (Lines 260-269)
**Current code**:
```c
void scalar_mult_g(point_j *res, bignum *k) {
    point_j base, curr;
    for(int i=0; i<8; i++){
        base.x.d[i]=Gx[i]; 
        base.y.d[i]=Gy[i]; 
        base.z.d[i]=0;      // ← BUG: Should be 1, not 0
        curr.z.d[i]=0;      // ← Correct: point at infinity
    }
    base.z.d[0]=1;
    // ...
}
```

**Problem**: Loop sets `base.z.d[i]=0` for all i, then immediately after the loop sets `base.z.d[0]=1`. This works but is confusing and error-prone.

**Fixed version**:
```c
void scalar_mult_g(point_j *res, bignum *k) {
    point_j base, curr;
    
    // Initialize base = generator point in affine coordinates
    for(int i=0; i<8; i++){
        base.x.d[i] = Gx[i]; 
        base.y.d[i] = Gy[i]; 
        base.z.d[i] = 0;
    }
    base.z.d[0] = 1;  // z = 1 (affine coordinates)
    
    // Initialize curr = point at infinity
    for(int i=0; i<8; i++){
        curr.x.d[i] = 0;
        curr.y.d[i] = 0;
        curr.z.d[i] = 0;  // Point at infinity has z = 0
    }
    
    // Convert base to Montgomery domain
    bn_to_mont(&base.x, &base.x);
    bn_to_mont(&base.y, &base.y);
    bn_to_mont(&base.z, &base.z);
    
    // Double-and-add algorithm
    for (int i = 255; i >= 0; i--) {
        point_j_double(&curr);
        if ((k->d[i / 32] >> (i % 32)) & 1) {
            point_j_add(&curr, &base);
        }
    }
    *res = curr;
}
```

## Recommended Fix Approach

### Option 1: Replace Functions with Proven Implementations
1. Replace `bn_mul_mont` (lines 68-89) with calc_addrs.cl version
2. Replace `bn_mod_inverse` (lines 91-112) with calc_addrs.cl version
3. Fix scalar multiplication initialization
4. Test with `test_gpu_ec_correctness.py`

### Option 2: Use Hybrid Mode (Immediate Solution)
- GPU generates random bytes
- CPU does EC with coincurve (proven correct)
- Guaranteed correct addresses
- 30-100K keys/sec

### Option 3: Port Full Batch Approach from calc_addrs.cl
- Use `ec_add_grid` + `heap_invert` kernels
- Batch modular inversion (faster)
- Proven correct
- Maximum GPU performance
- More complex integration

## Testing After Fixes

After applying fixes, run:
```bash
python test_gpu_ec_correctness.py
```

This will:
1. Generate 100 random private keys
2. Compute addresses on GPU (with fixes)
3. Compute addresses on CPU (proven correct)
4. Compare - ALL must match for success

## Next Steps

1. **Choose fix approach** (Option 1, 2, or 3)
2. **Apply fixes** to gpu_kernel.cl
3. **Test extensively** with test_gpu_ec_correctness.py
4. **Benchmark** performance once correct
5. **Document** which approach was used

## Summary

**Current State**: GPU EC operations are UNVERIFIED and have SUSPICIOUS CODE  
**Root Cause**: AI-generated implementations with simplified/buggy carry handling  
**Solution**: Replace with proven calc_addrs.cl implementations OR use Hybrid Mode  
**Test**: `test_gpu_ec_correctness.py` will reveal if fixes work  

**Immediate Recommendation**: Use Hybrid Mode (guaranteed correct) while fixing GPU EC operations.
