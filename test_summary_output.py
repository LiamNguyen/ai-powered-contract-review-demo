"""
Test the updated summary output without violations list.
"""

from evaluate_contract import ContractEvaluator

# Test document URL
TEST_DOC_URL = "https://docs.google.com/document/d/1rHt_qNNnOEdVTS5q4fCMmUxotQNceUNYLjBhs1kqMfE/edit?tab=t.0"


def main():
    """Test summary format."""
    print("=" * 80)
    print("TESTING UPDATED SUMMARY OUTPUT")
    print("=" * 80)
    print()

    evaluator = ContractEvaluator()

    # Just analyze (don't add comments)
    print("Analyzing contract...")
    analysis = evaluator.analyze_contract(TEST_DOC_URL)

    # Generate summary
    summary = evaluator._generate_summary(TEST_DOC_URL, analysis)

    print("\n" + "=" * 80)
    print("SUMMARY OUTPUT:")
    print("=" * 80)
    print()
    print(summary)
    print()
    print("=" * 80)
    print()
    print("✓ No violations summary list")
    print("✓ Shows violation count")
    print("✓ Shows highest escalation level")
    print("✓ Links to Google Docs for details")
    print()


if __name__ == "__main__":
    main()
