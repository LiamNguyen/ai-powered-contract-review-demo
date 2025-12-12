"""Test script for Google Docs tools.

Run this to verify your setup works correctly.
Make sure credentials.json is in the project root before running.
"""

from google_docs_tools import (
    read_document,
    get_document_text,
    add_comment,
    find_text_position,
)

# The test document URL
TEST_DOC_URL = "https://docs.google.com/document/d/1rHt_qNNnOEdVTS5q4fCMmUxotQNceUNYLjBhs1kqMfE/edit?tab=t.0"


def test_read_document():
    """Test reading document structure."""
    print("=" * 50)
    print("Testing: read_document()")
    print("=" * 50)

    result = read_document(TEST_DOC_URL)

    print(f"Title: {result['title']}")
    print(f"Document ID: {result['document_id']}")
    print(f"Number of text segments: {len(result['text_with_indices'])}")
    print()
    return result


def test_get_document_text():
    """Test getting plain text."""
    print("=" * 50)
    print("Testing: get_document_text()")
    print("=" * 50)

    result = get_document_text(TEST_DOC_URL)

    print(f"Title: {result['title']}")
    print(f"Full text preview (first 500 chars):")
    print("-" * 40)
    print(result["full_text"][:500])
    print("-" * 40)
    print()
    return result


def test_find_text():
    """Test finding text position."""
    print("=" * 50)
    print("Testing: find_text_position()")
    print("=" * 50)

    # First get some text to search for
    doc = get_document_text(TEST_DOC_URL)
    # Get first 20 characters of actual content (skip newlines)
    sample_text = doc["full_text"].strip()[:20]

    print(f"Searching for: '{sample_text}'")
    result = find_text_position(TEST_DOC_URL, sample_text)

    print(f"Found: {result['found']}")
    if result["found"]:
        print(f"Start index: {result['start_index']}")
        print(f"Length: {result['length']}")
        print(f"Context: {result['context']}")
    print()
    return result


def test_comment_on_liquidated_damages():
    """Test adding a comment to the liquidated damages clause."""
    print("=" * 50)
    print("Testing: Comment on liquidated damages clause")
    print("=" * 50)

    target_text = (
        "if the PURCHASER so demands, a sum of 10 per cent of the DELIVERY PRICE "
        "as liquidated damages for each commencing day of the delay, however not "
        "exceeding in total fifty (50) per cent of the DELIVERY PRICE"
    )

    print(f"Target text: '{target_text[:60]}...'")

    position = find_text_position(TEST_DOC_URL, target_text)

    if not position["found"]:
        print("Could not find liquidated damages clause!")
        return None

    print(f"Found at index: {position['start_index']}, length: {position['length']}")

    result = add_comment(
        document_id=TEST_DOC_URL,
        comment_text=(
            "AI Review: The 10% daily penalty rate is unusually high. "
            "Standard contracts typically use 0.5-1% per day. "
            "The 50% cap is reasonable but consider negotiating the daily rate down."
        ),
        quoted_text=target_text,
    )

    print(f"Success: {result['success']}")
    print(f"Comment ID: {result['comment_id']}")
    print(f"Text highlighted: {result['highlighted']}")
    print()
    return result


def test_comment_on_payment_terms():
    """Test adding a comment to Battery limits section."""
    print("=" * 50)
    print("Testing: Comment on Battery limits")
    print("=" * 50)

    target_text = (
        "The invoices are due for payment 120 days net from the date of invoice"
    )

    print(f"Target text: '{target_text}'")

    position = find_text_position(TEST_DOC_URL, target_text)

    if not position["found"]:
        print("Could not find 'Battery limits'!")
        return None

    print(f"Found at index: {position['start_index']}, length: {position['length']}")

    result = add_comment(
        document_id=TEST_DOC_URL,
        comment_text="AI Review: Extending payment terms to 120 days would severely strain our working capital, significantly increase our credit risk exposure, and create an unsustainable financial burden.",
        quoted_text=target_text,
    )

    print(f"Success: {result['success']}")
    print(f"Comment ID: {result['comment_id']}")
    print(f"Text highlighted: {result['highlighted']}")
    print()
    return result


def test_comment_on_total_liability_cap():
    """Test adding a comment to Battery limits section."""
    print("=" * 50)
    print("Testing: Comment on Battery limits")
    print("=" * 50)

    target_text = "Total liability cap for the scope of this CONTRACT shall be 500%"

    print(f"Target text: '{target_text}'")

    position = find_text_position(TEST_DOC_URL, target_text)

    if not position["found"]:
        print("Could not find 'Battery limits'!")
        return None

    print(f"Found at index: {position['start_index']}, length: {position['length']}")

    result = add_comment(
        document_id=TEST_DOC_URL,
        comment_text="AI Review: This violates our contractual policies. Recommend to review with high-level management, check with legal or re-negotiate with customer.",
        quoted_text=target_text,
    )

    print(f"Success: {result['success']}")
    print(f"Comment ID: {result['comment_id']}")
    print(f"Text highlighted: {result['highlighted']}")
    print()
    return result


if __name__ == "__main__":
    print("\nGoogle Docs Tools - Test Suite")
    print("=" * 50)
    print()

    try:
        # Test reading
        # test_read_document()
        # test_get_document_text()
        # test_find_text()

        # Test Payment terms comment
        print("\n" + "=" * 50)
        print("Test comment on Payment terms:")
        test_comment_on_payment_terms()

        # Test liquidated damages comment
        print("\n" + "=" * 50)
        print("Test comment on specific contract clause:")
        test_comment_on_liquidated_damages()

        # Test Total liability cap comment
        print("\n" + "=" * 50)
        print("Test comment on Total liability cap:")
        test_comment_on_total_liability_cap()

        print("\nAll tests completed!")

    except FileNotFoundError as e:
        print(f"\nERROR: {e}")
        print("\nMake sure to:")
        print("1. Create a Google Cloud project")
        print("2. Enable Google Docs API and Google Drive API")
        print("3. Create OAuth credentials (Desktop app)")
        print("4. Download credentials.json to project root")

    except Exception as e:
        print(f"\nERROR: {e}")
        raise
