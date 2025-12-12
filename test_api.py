"""
Test script for the FastAPI contract evaluation endpoint.
"""

import requests
import sys

# API endpoint
API_URL = "http://localhost:8000"

# Test document URL
TEST_DOC_URL = "https://docs.google.com/document/d/1rHt_qNNnOEdVTS5q4fCMmUxotQNceUNYLjBhs1kqMfE/edit?tab=t.0"


def test_health():
    """Test health endpoint."""
    print("=" * 80)
    print("Testing Health Endpoint")
    print("=" * 80)

    try:
        response = requests.get(f"{API_URL}/health")
        print(f"Status: {response.status_code}")
        print(f"Response: {response.json()}")
        print("✓ Health check passed\n")
        return True
    except Exception as e:
        print(f"✗ Health check failed: {e}\n")
        return False


def test_non_streaming():
    """Test non-streaming chat endpoint."""
    print("=" * 80)
    print("Testing Non-Streaming Endpoint")
    print("=" * 80)

    try:
        payload = {
            "message": f"Please evaluate this contract: {TEST_DOC_URL}"
        }

        print(f"Sending request...")
        response = requests.post(
            f"{API_URL}/chat",
            json=payload,
            timeout=120
        )

        if response.status_code == 200:
            result = response.json()
            print("\nResponse:")
            print("-" * 80)
            print(result["response"])
            print("-" * 80)
            print("✓ Non-streaming test passed\n")
            return True
        else:
            print(f"✗ Request failed: {response.status_code}")
            print(f"Error: {response.text}\n")
            return False

    except Exception as e:
        print(f"✗ Test failed: {e}\n")
        return False


def test_streaming():
    """Test streaming chat endpoint."""
    print("=" * 80)
    print("Testing Streaming Endpoint")
    print("=" * 80)

    try:
        payload = {
            "message": f"Please evaluate this contract: {TEST_DOC_URL}"
        }

        print(f"Sending request...")
        print("\nStreaming response:")
        print("-" * 80)

        response = requests.post(
            f"{API_URL}/chat/stream",
            json=payload,
            stream=True,
            timeout=120
        )

        if response.status_code == 200:
            for chunk in response.iter_content(chunk_size=None, decode_unicode=True):
                if chunk:
                    print(chunk, end='', flush=True)

            print("\n" + "-" * 80)
            print("✓ Streaming test passed\n")
            return True
        else:
            print(f"✗ Request failed: {response.status_code}")
            print(f"Error: {response.text}\n")
            return False

    except Exception as e:
        print(f"✗ Test failed: {e}\n")
        return False


def test_no_url():
    """Test with message that has no URL."""
    print("=" * 80)
    print("Testing No URL Handling")
    print("=" * 80)

    try:
        payload = {
            "message": "Hello, can you help me?"
        }

        print(f"Sending request without URL...")
        response = requests.post(
            f"{API_URL}/chat",
            json=payload,
            timeout=30
        )

        if response.status_code == 200:
            result = response.json()
            print("\nResponse:")
            print("-" * 80)
            print(result["response"])
            print("-" * 80)
            print("✓ No URL handling test passed\n")
            return True
        else:
            print(f"✗ Request failed: {response.status_code}\n")
            return False

    except Exception as e:
        print(f"✗ Test failed: {e}\n")
        return False


def main():
    """Run all tests."""
    print("\n" + "=" * 80)
    print("FASTAPI CONTRACT EVALUATION API - TEST SUITE")
    print("=" * 80)
    print()
    print("Make sure the API is running: uvicorn app:app --reload --port 8000")
    print()

    # Check if API is running
    if not test_health():
        print("ERROR: API is not running or not accessible")
        print("Start the API with: uvicorn app:app --reload --port 8000")
        sys.exit(1)

    # Run tests
    tests = [
        ("No URL handling", test_no_url),
        ("Non-streaming endpoint", test_non_streaming),
        ("Streaming endpoint", test_streaming),
    ]

    results = []
    for name, test_func in tests:
        print(f"\n{'='*80}")
        print(f"Running: {name}")
        print('='*80)
        results.append((name, test_func()))

    # Summary
    print("\n" + "=" * 80)
    print("TEST SUMMARY")
    print("=" * 80)
    for name, passed in results:
        status = "✓ PASSED" if passed else "✗ FAILED"
        print(f"{status}: {name}")

    all_passed = all(result[1] for result in results)
    if all_passed:
        print("\n✓ All tests passed!")
    else:
        print("\n✗ Some tests failed")
        sys.exit(1)


if __name__ == "__main__":
    main()
