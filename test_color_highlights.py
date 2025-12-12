"""
Test color-coded highlights for different escalation levels.
"""

from google_docs_tools import add_comment

# Test document URL
TEST_DOC_URL = "https://docs.google.com/document/d/1rHt_qNNnOEdVTS5q4fCMmUxotQNceUNYLjBhs1kqMfE/edit?tab=t.0"


def main():
    """Test color-coded highlights."""
    print("=" * 80)
    print("TESTING COLOR-CODED HIGHLIGHTS")
    print("=" * 80)
    print()

    tests = [
        {
            "text": "The invoices are due for payment 120 days net from the date of invoice",
            "escalation": "Head of BU",
            "color": {"red": 1.0, "green": 1.0, "blue": 0.6},
            "color_name": "Yellow"
        },
        {
            "text": "Total liability cap for the scope of this CONTRACT shall be 500%",
            "escalation": "CEO",
            "color": {"red": 1.0, "green": 0.6, "blue": 0.6},
            "color_name": "Red"
        }
    ]

    for i, test in enumerate(tests, 1):
        print(f"\n{i}. Testing {test['escalation']} ({test['color_name']} highlight)")
        print(f"   Text: {test['text'][:60]}...")

        try:
            # Format comment with approval line
            comment = f"{test['escalation']} approval required\n\nThis is a test comment for {test['escalation']} escalation level."

            result = add_comment(
                document_id=TEST_DOC_URL,
                comment_text=comment,
                quoted_text=test['text'],
                highlight=True,
                highlight_color=test['color'],
                add_prefix=True,
            )

            print(f"   ✓ Success: {result['success']}")
            print(f"   ✓ Comment ID: {result['comment_id']}")
            print(f"   ✓ Highlighted: {result['highlighted']}")

        except Exception as e:
            print(f"   ✗ ERROR: {e}")

    print("\n" + "=" * 80)
    print("TESTS COMPLETE")
    print(f"Check the document for colored highlights:")
    print(f"{TEST_DOC_URL}")
    print("=" * 80)


if __name__ == "__main__":
    main()
