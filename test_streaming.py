"""
Test script to verify streaming improvements.

This script tests:
1. Backend streaming works correctly
2. Progress updates appear in real-time
3. No long blocking periods
"""

import sys
import time
import requests

TEST_DOC_URL = "https://docs.google.com/document/d/1rHt_qNNnOEdVTS5q4fCMmUxotQNceUNYLjBhs1kqMfE/edit?tab=t.0"
API_URL = "http://localhost:8000/chat/stream"


def test_streaming():
    """Test the streaming endpoint."""
    print("=" * 60)
    print("Testing Streaming Performance")
    print("=" * 60)
    print()

    message = f"Please evaluate this contract: {TEST_DOC_URL}"

    print(f"📤 Sending request to: {API_URL}")
    print(f"📝 Message: {message[:80]}...")
    print()

    start_time = time.time()
    first_chunk_time = None
    chunk_count = 0

    try:
        response = requests.post(
            API_URL,
            json={"message": message},
            stream=True,
            timeout=120
        )

        if response.status_code != 200:
            print(f"❌ Error: HTTP {response.status_code}")
            print(response.text)
            return

        print("📥 Streaming response:")
        print("-" * 60)

        # Stream the response
        for chunk in response.iter_content(chunk_size=None, decode_unicode=True):
            if chunk:
                if first_chunk_time is None:
                    first_chunk_time = time.time()
                    elapsed = first_chunk_time - start_time
                    print(f"\n⏱️  First chunk received in {elapsed:.2f}s\n")
                    print("-" * 60)

                # Print chunk immediately
                print(chunk, end='', flush=True)
                chunk_count += 1

        end_time = time.time()
        total_time = end_time - start_time
        time_to_first_chunk = first_chunk_time - start_time if first_chunk_time else 0

        print()
        print("-" * 60)
        print()
        print("📊 Performance Metrics:")
        print(f"   ⏱️  Time to first chunk: {time_to_first_chunk:.2f}s")
        print(f"   ⏱️  Total time: {total_time:.2f}s")
        print(f"   📦 Total chunks: {chunk_count}")
        print()

        if time_to_first_chunk < 2.0:
            print("✅ Streaming is WORKING WELL")
            print("   First chunk arrived quickly (< 2s)")
        elif time_to_first_chunk < 5.0:
            print("⚠️  Streaming is OK but could be better")
            print("   First chunk took 2-5 seconds")
        else:
            print("❌ Streaming has issues")
            print("   First chunk took > 5 seconds")
            print("   Check for buffering problems")

    except requests.exceptions.ConnectionError:
        print("❌ Connection error: Is the FastAPI server running?")
        print("   Start it with: uvicorn app:app --reload --port 8000")
        return

    except requests.exceptions.Timeout:
        print("❌ Request timeout")
        print("   The request took longer than 120 seconds")
        return

    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return


def test_health():
    """Test if API is running."""
    try:
        response = requests.get("http://localhost:8000/health", timeout=5)
        if response.status_code == 200:
            print("✅ API is healthy")
            return True
        else:
            print(f"⚠️  API returned status {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to API at http://localhost:8000")
        print("   Start the server with: uvicorn app:app --reload --port 8000")
        return False


if __name__ == "__main__":
    print()
    print("🧪 Streaming Performance Test")
    print()

    # Check if API is running
    if not test_health():
        sys.exit(1)

    print()

    # Run streaming test
    test_streaming()

    print()
    print("=" * 60)
    print("Test complete!")
    print("=" * 60)
