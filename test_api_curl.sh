#!/bin/bash

# Test script for FastAPI endpoints using curl

API_URL="http://localhost:8000"
TEST_DOC="https://docs.google.com/document/d/1rHt_qNNnOEdVTS5q4fCMmUxotQNceUNYLjBhs1kqMfE/edit?tab=t.0"

echo "========================================"
echo "FastAPI Contract Evaluation API Tests"
echo "========================================"
echo ""

# Test 1: Health check
echo "1. Testing health endpoint..."
curl -s "$API_URL/health" | jq '.'
echo ""
echo ""

# Test 2: No URL in message
echo "2. Testing message without URL..."
curl -s -X POST "$API_URL/chat" \
  -H "Content-Type: application/json" \
  -d '{"message": "Hello, can you help me?"}' | jq -r '.response'
echo ""
echo ""

# Test 3: Non-streaming with URL
echo "3. Testing non-streaming endpoint with contract URL..."
curl -s -X POST "$API_URL/chat" \
  -H "Content-Type: application/json" \
  -d "{\"message\": \"Please evaluate this contract: $TEST_DOC\"}" \
  | jq -r '.response'
echo ""
echo ""

# Test 4: Streaming endpoint
echo "4. Testing streaming endpoint..."
curl -X POST "$API_URL/chat/stream" \
  -H "Content-Type: application/json" \
  -d "{\"message\": \"Please evaluate this contract: $TEST_DOC\"}" \
  --no-buffer
echo ""
echo ""

echo "========================================"
echo "Tests complete"
echo "========================================"
