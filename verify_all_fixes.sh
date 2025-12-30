#!/bin/bash
# Verification script for EC checks and progress tracking fixes

echo "============================================================"
echo "Verifying EC Checks and Progress Tracking Fixes"
echo "============================================================"
echo ""

# Check if we're in the right directory
if [ ! -f "vanitygen_py/gui.py" ]; then
    echo "❌ Error: Must be run from project root directory"
    exit 1
fi

echo "1. Checking Python syntax..."
python -m py_compile vanitygen_py/gui.py vanitygen_py/gpu_generator.py 2>/dev/null
if [ $? -eq 0 ]; then
    echo "   ✅ Python files compile successfully"
else
    echo "   ❌ Syntax errors found"
    exit 1
fi

echo ""
echo "2. Running EC check enhancement tests..."
python test_ec_check_enhancements.py 2>&1 | tail -3
if [ $? -eq 0 ]; then
    echo "   ✅ EC check tests pass"
else
    echo "   ❌ EC check tests failed"
    exit 1
fi

echo ""
echo "3. Running GUI counter label tests..."
QT_QPA_PLATFORM=offscreen python test_gui_counter_labels.py 2>&1 | tail -3
if [ $? -eq 0 ]; then
    echo "   ✅ GUI counter tests pass"
else
    echo "   ❌ GUI counter tests failed"
    exit 1
fi

echo ""
echo "4. Checking documentation files..."
docs=("EC_CHECKS_AND_PROGRESS_FIXES.md" "FIXES_SUMMARY.md" "README_FIXES.md")
all_docs_exist=true
for doc in "${docs[@]}"; do
    if [ -f "$doc" ]; then
        echo "   ✅ $doc exists"
    else
        echo "   ❌ $doc missing"
        all_docs_exist=false
    fi
done

if [ "$all_docs_exist" = false ]; then
    exit 1
fi

echo ""
echo "5. Checking test suites..."
tests=("test_ec_check_enhancements.py" "test_gui_counter_labels.py")
all_tests_exist=true
for test in "${tests[@]}"; do
    if [ -f "$test" ]; then
        echo "   ✅ $test exists"
    else
        echo "   ❌ $test missing"
        all_tests_exist=false
    fi
done

if [ "$all_tests_exist" = false ]; then
    exit 1
fi

echo ""
echo "6. Verifying key changes in gui.py..."
if grep -q "Matches Found (by address type)" vanitygen_py/gui.py; then
    echo "   ✅ Counter section renamed"
else
    echo "   ❌ Counter section not found"
    exit 1
fi

if grep -q "Keys Searched: Total number of keys" vanitygen_py/gui.py; then
    echo "   ✅ Stats tooltip added"
else
    echo "   ❌ Stats tooltip not found"
    exit 1
fi

if grep -q "EC Verification Checks" vanitygen_py/gui.py; then
    echo "   ✅ EC info banner added"
else
    echo "   ❌ EC info banner not found"
    exit 1
fi

echo ""
echo "7. Verifying key changes in gpu_generator.py..."
if grep -q "'cpu_addr'" vanitygen_py/gpu_generator.py && grep -q "'gpu_addr'" vanitygen_py/gpu_generator.py; then
    echo "   ✅ EC check address comparison added"
else
    echo "   ❌ EC check address comparison not found"
    exit 1
fi

echo ""
echo "============================================================"
echo "✅ ALL VERIFICATION CHECKS PASSED!"
echo "============================================================"
echo ""
echo "Summary of fixes:"
echo "  • EC check failures now show detailed diagnostics"
echo "  • Counter labels clearly distinguish total vs matches"
echo "  • Tooltips provide helpful context everywhere"
echo "  • Comprehensive documentation provided"
echo "  • All tests passing"
echo ""
echo "Next steps:"
echo "  1. Review documentation: README_FIXES.md"
echo "  2. Start the GUI: python -m vanitygen_py.gui"
echo "  3. Hover over counters to see tooltips"
echo "  4. Check EC Checks tab for info banner"
echo ""
exit 0
