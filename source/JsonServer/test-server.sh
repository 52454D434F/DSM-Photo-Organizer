#!/bin/bash
# Test script for JSON Server
# Usage: ./test-server.sh [HOST] [PORT]

set -e

HOST="${1:-localhost}"
PORT="${2:-3000}"
BASE_URL="http://${HOST}:${PORT}"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Test counter
TESTS_PASSED=0
TESTS_FAILED=0

# Function to print test result
print_result() {
    local test_name="$1"
    local status="$2"
    local details="$3"
    
    if [ "$status" = "PASS" ]; then
        echo -e "${GREEN}✓${NC} $test_name"
        ((TESTS_PASSED++))
    else
        echo -e "${RED}✗${NC} $test_name"
        if [ -n "$details" ]; then
            echo -e "  ${RED}Error:${NC} $details"
        fi
        ((TESTS_FAILED++))
    fi
}

# Function to test endpoint
test_endpoint() {
    local endpoint="$1"
    local expected_status="${2:-200}"
    local description="$3"
    
    local url="${BASE_URL}${endpoint}"
    local response=$(curl -s -w "\n%{http_code}" "$url" 2>/dev/null || echo -e "\n000")
    local body=$(echo "$response" | head -n -1)
    local status_code=$(echo "$response" | tail -n 1)
    
    if [ "$status_code" = "$expected_status" ]; then
        # Check if response is valid JSON (if status is 200)
        if [ "$expected_status" = "200" ]; then
            if echo "$body" | python3 -m json.tool >/dev/null 2>&1; then
                print_result "$description" "PASS"
                return 0
            else
                print_result "$description" "FAIL" "Response is not valid JSON"
                return 1
            fi
        else
            print_result "$description" "PASS"
            return 0
        fi
    else
        print_result "$description" "FAIL" "Expected HTTP $expected_status, got $status_code"
        return 1
    fi
}

echo "======================================"
echo "JSON Server Test Suite"
echo "======================================"
echo "Testing server at: $BASE_URL"
echo ""

# Test 1: Check if server is reachable
echo "Test 1: Server connectivity"
if curl -s --connect-timeout 5 "$BASE_URL" >/dev/null 2>&1; then
    print_result "Server is reachable" "PASS"
else
    print_result "Server is reachable" "FAIL" "Cannot connect to server. Is it running?"
    echo ""
    echo "Make sure the server is running:"
    echo "  - On Synology: sudo synopkg status Json-Server"
    echo "  - Check logs: tail -f /var/packages/Json-Server/var/service.log"
    exit 1
fi
echo ""

# Test 2: Root endpoint
echo "Test 2: Root endpoint"
test_endpoint "/" "200" "GET / (root endpoint)"

# Test 3: Posts endpoint
echo ""
echo "Test 3: Posts endpoints"
test_endpoint "/posts" "200" "GET /posts (all posts)"
test_endpoint "/posts/1" "200" "GET /posts/1 (post by ID)"
test_endpoint "/posts/999" "404" "GET /posts/999 (non-existent post)"

# Test 4: Comments endpoint
echo ""
echo "Test 4: Comments endpoints"
test_endpoint "/comments" "200" "GET /comments (all comments)"
test_endpoint "/comments/1" "200" "GET /comments/1 (comment by ID)"
test_endpoint "/comments?postId=1" "200" "GET /comments?postId=1 (filtered comments)"

# Test 5: Profile endpoint
echo ""
echo "Test 5: Profile endpoint"
test_endpoint "/profile" "200" "GET /profile"

# Test 6: Filtering
echo ""
echo "Test 6: Filtering"
test_endpoint "/posts?author=John" "200" "GET /posts?author=John (filtered posts)"

# Test 7: POST request (create new post)
echo ""
echo "Test 7: POST request"
NEW_POST_RESPONSE=$(curl -s -X POST "$BASE_URL/posts" \
    -H "Content-Type: application/json" \
    -d '{"title": "Test Post", "author": "Test Script"}' \
    -w "\n%{http_code}" 2>/dev/null || echo -e "\n000")
NEW_POST_BODY=$(echo "$NEW_POST_RESPONSE" | head -n -1)
NEW_POST_STATUS=$(echo "$NEW_POST_RESPONSE" | tail -n 1)

if [ "$NEW_POST_STATUS" = "201" ] || [ "$NEW_POST_STATUS" = "200" ]; then
    if echo "$NEW_POST_BODY" | python3 -m json.tool >/dev/null 2>&1; then
        NEW_POST_ID=$(echo "$NEW_POST_BODY" | python3 -c "import sys, json; print(json.load(sys.stdin).get('id', ''))" 2>/dev/null || echo "")
        if [ -n "$NEW_POST_ID" ]; then
            print_result "POST /posts (create new post)" "PASS" "Created post with ID: $NEW_POST_ID"
            
            # Test DELETE
            DELETE_STATUS=$(curl -s -X DELETE "$BASE_URL/posts/$NEW_POST_ID" -w "%{http_code}" -o /dev/null 2>/dev/null || echo "000")
            if [ "$DELETE_STATUS" = "200" ] || [ "$DELETE_STATUS" = "204" ]; then
                print_result "DELETE /posts/$NEW_POST_ID" "PASS"
            else
                print_result "DELETE /posts/$NEW_POST_ID" "FAIL" "HTTP status: $DELETE_STATUS"
            fi
        else
            print_result "POST /posts (create new post)" "FAIL" "Response missing ID"
        fi
    else
        print_result "POST /posts (create new post)" "FAIL" "Response is not valid JSON"
    fi
else
    print_result "POST /posts (create new post)" "FAIL" "Expected HTTP 201/200, got $NEW_POST_STATUS"
fi

# Summary
echo ""
echo "======================================"
echo "Test Summary"
echo "======================================"
echo -e "${GREEN}Passed:${NC} $TESTS_PASSED"
if [ $TESTS_FAILED -gt 0 ]; then
    echo -e "${RED}Failed:${NC} $TESTS_FAILED"
    exit 1
else
    echo -e "${GREEN}Failed:${NC} $TESTS_FAILED"
    echo ""
    echo -e "${GREEN}All tests passed!${NC} ✓"
    exit 0
fi
