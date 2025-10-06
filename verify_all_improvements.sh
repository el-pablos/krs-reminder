#!/bin/bash
# Comprehensive verification script for all improvements

set -e

echo "🔍 COMPREHENSIVE VERIFICATION SCRIPT"
echo "===================================="
echo ""

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Test counter
PASSED=0
FAILED=0

test_result() {
    if [ $1 -eq 0 ]; then
        echo -e "${GREEN}✅ PASSED${NC}: $2"
        ((PASSED++))
    else
        echo -e "${RED}❌ FAILED${NC}: $2"
        ((FAILED++))
    fi
    echo ""
}

echo "📊 TEST 1: Bot Status"
echo "--------------------"
./botctl.sh status > /dev/null 2>&1
test_result $? "Bot is running"

echo "📊 TEST 2: Performance Test"
echo "--------------------"
cd /root/work/krs-reminder
PYTHONPATH=src python3 tests/test_jadwal_performance.py > /tmp/perf_test.log 2>&1
if grep -q "EXCELLENT" /tmp/perf_test.log; then
    test_result 0 "Performance test (response time < 3s)"
else
    test_result 1 "Performance test"
fi

echo "📊 TEST 3: UI/UX Tests"
echo "--------------------"
PYTHONPATH=src python3 tests/test_ui_redesign.py > /tmp/ui_test.log 2>&1
if grep -q "4/4 tests passed" /tmp/ui_test.log; then
    test_result 0 "UI/UX tests (4/4 passed)"
else
    test_result 1 "UI/UX tests"
fi

echo "📊 TEST 4: Python Module Warning"
echo "--------------------"
./botctl.sh stop > /dev/null 2>&1
sleep 1
> var/log/bot.log  # Clear log
./botctl.sh start > /dev/null 2>&1
sleep 3
if grep -q "RuntimeWarning" var/log/bot.log; then
    test_result 1 "No Python warnings"
else
    test_result 0 "No Python warnings"
fi

echo "📊 TEST 5: Bot Control Commands"
echo "--------------------"
./botctl.sh restart > /dev/null 2>&1
sleep 2
./botctl.sh status > /dev/null 2>&1
test_result $? "Bot control commands work"

echo "📊 TEST 6: Configuration"
echo "--------------------"
TIMEOUT=$(PYTHONPATH=src python3 -c "from krs_reminder import config; print(config.TELEGRAM_POLL_TIMEOUT)" 2>/dev/null)
if [ "$TIMEOUT" = "30" ]; then
    test_result 0 "Timeout configuration correct (30s)"
else
    test_result 1 "Timeout configuration"
fi

echo ""
echo "===================================="
echo "📊 FINAL RESULTS"
echo "===================================="
echo -e "Passed: ${GREEN}$PASSED${NC}"
echo -e "Failed: ${RED}$FAILED${NC}"
echo "Total:  $((PASSED + FAILED))"
echo ""

if [ $FAILED -eq 0 ]; then
    echo -e "${GREEN}🎉 ALL TESTS PASSED!${NC}"
    echo "✅ Bot is production ready"
    exit 0
else
    echo -e "${RED}❌ SOME TESTS FAILED${NC}"
    echo "⚠️  Please review the failures above"
    exit 1
fi

