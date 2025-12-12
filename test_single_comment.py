"""
Test adding a single comment to the document to verify the functionality works.
"""

from google_docs_tools import find_text_position, add_comment

# Test document URL
TEST_DOC_URL = "https://docs.google.com/document/d/1rHt_qNNnOEdVTS5q4fCMmUxotQNceUNYLjBhs1kqMfE/edit?tab=t.0"

# Known text from the contract
TEST_TEXT = "The invoices are due for payment 120 days net from the date of invoice"


def main():
    """Test adding a single comment."""
    print("=" * 80)
    print("TESTING SINGLE COMMENT ADDITION")
    print("=" * 80)
    print()

    try:
        print(f"1. Searching for text in document...")
        print(f"   Text: '{TEST_TEXT}'")

        position = find_text_position(TEST_DOC_URL, TEST_TEXT)

        if not position["found"]:
            print(f"   ✗ Text not found in document!")
            return

        print(f"   ✓ Text found at index: {position['start_index']}")
        print(f"   Context: {position['context']}")
        print()

        print(f"2. Adding comment with highlight...")

        result = add_comment(
            document_id=TEST_DOC_URL,
            comment_text="TEST COMMENT: Payment terms of 120 days exceed the 60-day policy threshold.",
            quoted_text=TEST_TEXT,
            highlight=True,
            add_prefix=True,
        )

        print(f"   ✓ Success: {result['success']}")
        print(f"   ✓ Comment ID: {result['comment_id']}")
        print(f"   ✓ Text highlighted: {result['highlighted']}")
        print()

        print("=" * 80)
        print("COMMENT ADDED SUCCESSFULLY")
        print(f"Please check the Google Doc to verify:")
        print(f"{TEST_DOC_URL}")
        print("=" * 80)

    except Exception as e:
        print(f"\n✗ ERROR: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
