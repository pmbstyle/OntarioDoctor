#!/bin/bash
set -e

echo "🧪 OntarioDoctor Smoke Tests"
echo "=============================="
echo ""

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Test counter
PASSED=0
FAILED=0

# Helper functions
pass() {
    echo -e "${GREEN}✓${NC} $1"
    ((PASSED++))
}

fail() {
    echo -e "${RED}✗${NC} $1"
    ((FAILED++))
}

info() {
    echo -e "${YELLOW}ℹ${NC} $1"
}

# Test 1: Health checks
echo "Test 1: Service Health Checks"
echo "------------------------------"

if curl -s -f http://localhost:8080/health > /dev/null; then
    pass "Gateway is healthy"
else
    fail "Gateway is unhealthy"
fi

if curl -s -f http://localhost:8001/health > /dev/null; then
    pass "RAG service is healthy"
else
    fail "RAG service is unhealthy"
fi

if curl -s -f http://localhost:8002/health > /dev/null; then
    pass "Orchestrator is healthy"
else
    fail "Orchestrator is unhealthy"
fi

if curl -s -f http://localhost:11435/api/tags > /dev/null; then
    pass "Ollama is healthy"
else
    fail "Ollama is unhealthy"
fi

if curl -s -f http://localhost:6333/health > /dev/null; then
    pass "Qdrant is healthy"
else
    fail "Qdrant is unhealthy"
fi

echo ""

# Test 2: Data ingestion
echo "Test 2: Data Ingestion"
echo "----------------------"

INGEST_RESPONSE=$(curl -s -X POST http://localhost:8080/ingest \
    -H "Content-Type: application/json" \
    -d '{"documents":[{"text":"Test document for smoke test","title":"Test","url":"http://test.com","source":"test","section":"test"}]}')

if echo "$INGEST_RESPONSE" | grep -q "ingested_count"; then
    pass "Data ingestion successful"
    info "Response: $INGEST_RESPONSE"
else
    fail "Data ingestion failed"
    info "Response: $INGEST_RESPONSE"
fi

echo ""

# Test 3: RAG retrieval
echo "Test 3: RAG Retrieval"
echo "---------------------"

RETRIEVAL_RESPONSE=$(curl -s -X POST http://localhost:8001/retrieve \
    -H "Content-Type: application/json" \
    -d '{"query":"fever","k":3,"rerank_top_n":2}')

if echo "$RETRIEVAL_RESPONSE" | grep -q "hits"; then
    pass "RAG retrieval successful"
    HITS_COUNT=$(echo "$RETRIEVAL_RESPONSE" | grep -o '"hits"' | wc -l)
    info "Retrieved documents"
else
    fail "RAG retrieval failed"
    info "Response: $RETRIEVAL_RESPONSE"
fi

echo ""

# Test 4: Chat endpoint
echo "Test 4: Chat Endpoint"
echo "---------------------"

CHAT_RESPONSE=$(curl -s -X POST http://localhost:8080/chat \
    -H "Content-Type: application/json" \
    -d '{"messages":[{"role":"user","content":"I have a fever of 38.5C for 2 days"}]}')

if echo "$CHAT_RESPONSE" | grep -q "answer"; then
    pass "Chat endpoint successful"
    if echo "$CHAT_RESPONSE" | grep -q "citations"; then
        pass "Response includes citations"
    else
        fail "Response missing citations"
    fi
    if echo "$CHAT_RESPONSE" | grep -q "triage"; then
        pass "Response includes triage level"
    else
        fail "Response missing triage level"
    fi
else
    fail "Chat endpoint failed"
    info "Response: $CHAT_RESPONSE"
fi

echo ""

# Test 5: Red flag detection
echo "Test 5: Red Flag Detection"
echo "--------------------------"

RED_FLAG_RESPONSE=$(curl -s -X POST http://localhost:8080/chat \
    -H "Content-Type: application/json" \
    -d '{"messages":[{"role":"user","content":"I have severe chest pain and shortness of breath"}]}')

if echo "$RED_FLAG_RESPONSE" | grep -q "ER\|911"; then
    pass "Red flag detection working"
    if echo "$RED_FLAG_RESPONSE" | grep -q "red_flags"; then
        pass "Red flags array present"
    fi
else
    fail "Red flag detection not working"
    info "Response: $RED_FLAG_RESPONSE"
fi

echo ""

# Test 6: Frontend accessibility
echo "Test 6: Frontend Accessibility"
echo "-------------------------------"

if curl -s -f http://localhost:5173 > /dev/null; then
    pass "Frontend is accessible"
else
    fail "Frontend is not accessible"
fi

echo ""

# Summary
echo "=============================="
echo "Test Summary"
echo "=============================="
echo -e "${GREEN}Passed: $PASSED${NC}"
echo -e "${RED}Failed: $FAILED${NC}"
echo ""

if [ $FAILED -eq 0 ]; then
    echo -e "${GREEN}✓ All tests passed!${NC}"
    exit 0
else
    echo -e "${RED}✗ Some tests failed${NC}"
    exit 1
fi
