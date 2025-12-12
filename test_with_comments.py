"""
Test contract evaluator with full workflow - adds comments to document

WARNING: This will modify the Google Doc by adding comments and highlights.
"""

from evaluate_contract import ContractEvaluator

# Test document URL
TEST_DOC_URL = "https://docs.google.com/document/d/1rHt_qNNnOEdVTS5q4fCMmUxotQNceUNYLjBhs1kqMfE/edit?tab=t.0"


def main():
    """Test the full evaluation workflow with comments."""
    print("=" * 80)
    print("CONTRACT EVALUATOR - FULL TEST WITH COMMENTS")
    print("WARNING: This WILL modify the Google Doc")
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

    except Exception as e:
        print(f"\nERROR during evaluation: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    import sys

    # Safety check - require confirmation
    print("\nThis script will add comments and highlights to your Google Doc.")
    print(f"Document: {TEST_DOC_URL}")
    response = input("\nContinue? (yes/no): ")

    if response.lower() == "yes":
        main()
    else:
        print("Aborted.")
        sys.exit(0)
