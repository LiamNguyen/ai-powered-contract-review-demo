"""
Test script for contract evaluator - Analysis only (no document modification)

This script tests the contract analysis without adding comments to the document.
"""

from evaluate_contract import ContractEvaluator

# Test document URL
TEST_DOC_URL = "https://docs.google.com/document/d/1rHt_qNNnOEdVTS5q4fCMmUxotQNceUNYLjBhs1kqMfE/edit?tab=t.0"


def main():
    """Test contract analysis without modifying the document."""
    print("=" * 80)
    print("CONTRACT EVALUATOR - ANALYSIS TEST (No document modification)")
    print("=" * 80)
    print()

    # Create evaluator
    evaluator = ContractEvaluator()

    # Run analysis only (don't add comments)
    print(f"Document URL: {TEST_DOC_URL}\n")

    try:
        # Just analyze, don't modify
        analysis = evaluator.analyze_contract(TEST_DOC_URL)

        print("\n" + "=" * 80)
        print("ANALYSIS RESULTS")
        print("=" * 80)
        print()

        print("SUMMARY:")
        print(analysis["summary"])
        print()

        print(f"VIOLATIONS FOUND: {len(analysis['violations'])}")
        print(f"HIGHEST ESCALATION: {analysis.get('highest_escalation', 'None')}")
        print()

        if analysis["violations"]:
            print("DETAILED VIOLATIONS:")
            print("-" * 80)
            for i, v in enumerate(analysis["violations"], 1):
                print(f"\n{i}. {v['policy_violated']}")
                print(f"   Category: {v['category']}")
                print(f"   Severity: {v['severity']}")
                print(f"   Escalation: {v['escalation_level']}")
                print(f"   Clause: {v['clause_text'][:100]}...")
                print(f"   Comment: {v['comment'][:150]}...")

        print("\n" + "=" * 80)
        print("Note: No comments were added to the document in this test.")
        print("Run evaluate_contract.py to add comments and highlights.")
        print("=" * 80)

    except Exception as e:
        print(f"\nERROR during analysis: {e}")
        raise


if __name__ == "__main__":
    main()
