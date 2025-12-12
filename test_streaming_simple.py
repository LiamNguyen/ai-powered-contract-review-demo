"""
Simple streaming test to verify word-by-word streaming.
"""

import requests
import time
import sys

TEST_DOC_URL = "https://docs.google.com/document/d/1rHt_qNNnOEdVTS5q4fCMmUxotQNceUNYLjBhs1kqMfE/edit?tab=t.0"
API_URL = "http://localhost:8000/chat/stream"

def test_word_by_word_streaming():
    """Test that words arrive individually, not in big chunks."""

    print("🧪 Testing Word-by-Word Streaming")
    print("=" * 60)
    print()

    message = f"Please evaluate this contract: {TEST_DOC_URL}"

    try:
        response = requests.post(
            API_URL,
            json={"message": message},
            stream=True,
            timeout=120
        )

        if response.status_code != 200:
            print(f"❌ Error: HTTP {response.status_code}")
            return

        print("Streaming response (watch for word-by-word arrival):")
        print("-" * 60)

        chunk_count = 0
        chunk_sizes = []
        last_time = time.time()

        # Use iter_content with small chunk size to see individual yields
        for chunk in response.iter_content(chunk_size=1, decode_unicode=True):
            if chunk:
                current_time = time.time()
                elapsed = current_time - last_time

                # Print the chunk
                print(chunk, end='', flush=True)

                chunk_count += 1
                chunk_sizes.append(len(chunk))
                last_time = current_time

        print()
        print("-" * 60)
        print()
        print(f"📊 Received {chunk_count} chunks")
        print(f"📏 Average chunk size: {sum(chunk_sizes)/len(chunk_sizes):.1f} chars")
        print()

        # Check if we're getting small chunks (indicating word-by-word streaming)
        avg_size = sum(chunk_sizes) / len(chunk_sizes)
        if avg_size < 50:
            print("✅ EXCELLENT: Small chunks indicate smooth streaming")
        elif avg_size < 100:
            print("✔️  GOOD: Reasonable chunk sizes")
        else:
            print("⚠️  LARGE CHUNKS: Might still have buffering")

    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to API")
        print("   Start server: uvicorn app:app --reload --port 8000")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    test_word_by_word_streaming()
