"""
Full test of improved contract evaluator with:
1. Exact text extraction for violations
2. Color-coded highlights (Yellow/Orange/Red)
3. Approval role in comments
"""

from evaluate_contract import ContractEvaluator

# Test document URL
TEST_DOC_URL = "https://docs.google.com/document/d/1rHt_qNNnOEdVTS5q4fCMmUxotQNceUNYLjBhs1kqMfE/edit?tab=t.0"


def main():
    """Test full improved workflow."""
    print("=" * 80)
    print("CONTRACT EVALUATOR - FULL IMPROVED TEST")
    print("=" * 80)
    print()
    print("Improvements:")
    print("  1. ✓ Exact text extraction (targets violating clause)")
    print("  2. ✓ Color-coded highlights (Yellow/Orange/Red)")
    print("  3. ✓ Approval role in comments")
    print()
    print("=" * 80)
    print()

    # Create evaluator
    evaluator = ContractEvaluator()

    print(f"Document URL: {TEST_DOC_URL}\n")

    try:
        # Run full evaluation
        summary = evaluator.evaluate(TEST_DOC_URL)

        print("\n" + "=" * 80)
        print("EVALUATION COMPLETE")
        print("=" * 80)
        print()
        print(summary)
        print()
        print("=" * 80)
        print("VERIFICATION STEPS:")
        print("=" * 80)
        print("1. Open the document in your browser")
        print("2. Look for color-coded highlights:")
        print("   - Yellow = Head of BU approval")
        print("   - Orange = BA President approval")
        print("   - Red = CEO approval")
        print("3. Click on each highlight to see the comment")
        print("4. Verify each comment starts with '[Re: ...]' then '{Role} approval required'")
        print()
        print(f"Document: {TEST_DOC_URL}")
        print("=" * 80)

    except Exception as e:
        print(f"\nERROR during evaluation: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    import sys

    # Safety check
    print("\nThis will add colored comments and highlights to your Google Doc.")
    print(f"Document: {TEST_DOC_URL}")
    response = input("\nContinue? (yes/no): ")

    if response.lower() == "yes":
        main()
    else:
        print("Aborted.")
        sys.exit(0)
