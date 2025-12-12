"""
Contract Evaluator using Claude via AWS Bedrock

This script:
1. Reads a Google Docs contract
2. Uses Claude Sonnet 4.5 to analyze it against the approval matrix
3. Adds comments and highlights to problematic clauses
4. Returns a summary of findings
"""

import json
import os
from typing import Dict, List, Any

import boto3

from google_docs_tools import (
    get_document_text,
    add_comment,
    find_text_position,
    get_approval_matrix_prompt,
)

# AWS Bedrock configuration
# Using inference profile for Claude Sonnet 4.5
BEDROCK_MODEL_ID = "us.anthropic.claude-sonnet-4-5-20250929-v1:0"
BEDROCK_REGION = os.environ.get("AWS_REGION", "us-west-2")

# Test document URL (will be parameterized later)
TEST_DOC_URL = "https://docs.google.com/document/d/1rHt_qNNnOEdVTS5q4fCMmUxotQNceUNYLjBhs1kqMfE/edit?tab=t.0"


class ContractEvaluator:
    """Evaluates contracts against approval matrix using Claude AI."""

    def __init__(self, aws_region: str = BEDROCK_REGION):
        """Initialize the evaluator with AWS Bedrock client."""
        self.bedrock = boto3.client("bedrock-runtime", region_name=aws_region)
        self.model_id = BEDROCK_MODEL_ID

    def invoke_claude(self, system_prompt: str, user_message: str) -> str:
        """Invoke Claude via AWS Bedrock.

        Args:
            system_prompt: System instructions for Claude
            user_message: User message/query

        Returns:
            Claude's response as string
        """
        request_body = {
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": 4096,
            "temperature": 0.3,
            "system": system_prompt,
            "messages": [{"role": "user", "content": user_message}],
        }

        response = self.bedrock.invoke_model(
            modelId=self.model_id,
            contentType="application/json",
            accept="application/json",
            body=json.dumps(request_body),
        )

        response_body = json.loads(response["body"].read())
        return response_body["content"][0]["text"]

    def analyze_contract(self, document_url: str) -> Dict[str, Any]:
        """Analyze a contract and identify policy violations.

        Args:
            document_url: Google Docs URL of the contract

        Returns:
            Dictionary with:
                - violations: List of found violations
                - highest_escalation: Highest approval level needed
                - summary: High-level summary
        """
        # Step 1: Read the contract
        print("Reading contract from Google Docs...")
        doc_data = get_document_text(document_url)
        contract_text = doc_data["full_text"]
        doc_title = doc_data["title"]

        print(f"Contract: {doc_title}")
        print(f"Length: {len(contract_text)} characters\n")

        # Step 2: Get approval matrix
        approval_matrix = get_approval_matrix_prompt(format="structured")

        # Step 3: Ask Claude to analyze the contract
        print("Analyzing contract with Claude AI...")

        system_prompt = f"""You are a contract reviewer for a supplier company. Your ONLY job is to identify contract terms that trigger the specific approval matrix rules provided below.

CRITICAL INSTRUCTIONS:
1. ONLY flag violations that EXACTLY match the approval matrix conditions below
2. DO NOT use your general knowledge about contracts or business practices
3. DO NOT flag issues that are not explicitly defined in the approval matrix
4. If a term doesn't match any approval matrix condition, ignore it completely

{approval_matrix}

ESCALATION HIERARCHY (lowest to highest):
- Head of BU (Business Unit)
- BA President (Business Area President)
- CEO (Chief Executive Officer)

CRITICAL: For "clause_text", extract the EXACT text containing the violating term:
- Find the SPECIFIC phrase that contains the violating number/percentage (e.g., "500%", "120 days", "20%")
- Extract the MINIMAL complete sentence or clause containing that number
- If the sentence is long (>150 chars), extract ONLY the relevant clause/phrase with the violation
- DO NOT include introductory or conditional clauses before the violation
- The text MUST be directly searchable and highlightable in the document

EXAMPLES:
❌ BAD: "If the equipment is delayed and attributable to supplier, the supplier shall pay 20% damages" (too long, includes conditions)
✅ GOOD: "the SUPPLIER shall pay, if the PURCHASER so demands, a sum of 20% per cent of the CONTRACT PRICE as liquidated damages"

❌ BAD: "The contract states that liability shall be 500%" (paraphrased)
✅ GOOD: "Total liability cap for the scope of this CONTRACT shall be 500%"

❌ BAD: "Payment terms are specified in section 3" (vague)
✅ GOOD: "The invoices are due for payment 120 days net from the date of invoice"

Your analysis must be returned as valid JSON with this structure:
{{
  "summary": "2-sentence high-level summary of the contract and violations found",
  "violations": [
    {{
      "clause_text": "EXACT text containing the violating term/number (must be findable in document)",
      "policy_violated": "EXACT condition text from approval matrix that is triggered",
      "category": "EXACT category from approval matrix",
      "severity": "high|medium|low",
      "escalation_level": "role that has 'Approves/Decides' for this condition",
      "comment": "explanation of how this clause triggers the policy and recommendation"
    }}
  ],
  "highest_escalation": "CEO|BA President|Head of BU"
}}

REMEMBER: Only include violations that EXACTLY match an approval matrix rule. Do not invent or infer policies."""

        user_message = f"""Please analyze this contract and identify all terms that trigger the approval matrix rules:

CONTRACT TITLE: {doc_title}

CONTRACT TEXT:
{contract_text}

Return your analysis as valid JSON."""

        response = self.invoke_claude(system_prompt, user_message)

        # Parse Claude's response
        # Extract JSON from the response (handle markdown code blocks)
        json_text = response
        if "```json" in response:
            json_text = response.split("```json")[1].split("```")[0].strip()
        elif "```" in response:
            json_text = response.split("```")[1].split("```")[0].strip()

        analysis = json.loads(json_text)
        return analysis

    def get_highlight_color(self, escalation_level: str) -> dict:
        """Get highlight color based on escalation level.

        Args:
            escalation_level: The approval level (Head of BU, BA President, CEO)

        Returns:
            RGB color dict for highlighting
        """
        colors = {
            "Head of BU": {"red": 1.0, "green": 1.0, "blue": 0.6},  # Yellow
            "BA President": {"red": 1.0, "green": 0.7, "blue": 0.4},  # Orange
            "CEO": {"red": 1.0, "green": 0.6, "blue": 0.6},  # Light Red
        }
        return colors.get(escalation_level, {"red": 1.0, "green": 1.0, "blue": 0.6})  # Default yellow

    def add_comments_to_contract(
        self, document_url: str, violations: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Add comments to the contract for each violation.

        Args:
            document_url: Google Docs URL
            violations: List of violation dictionaries from analysis

        Returns:
            List of results from adding comments
        """
        print("\nAdding comments to Google Docs...")
        results = []

        for i, violation in enumerate(violations, 1):
            try:
                print(f"\n  [{i}/{len(violations)}] Processing: {violation['policy_violated']}")
                escalation_level = violation.get("escalation_level", "Head of BU")
                print(f"     Escalation: {escalation_level}")

                # Find the text in the document
                clause_text = violation["clause_text"]
                print(f"     Searching for text (length: {len(clause_text)} chars)")
                print(f"     Preview: {clause_text[:80]}...")

                position = find_text_position(document_url, clause_text)

                if not position["found"]:
                    print(f"     ✗ WARNING: Could not find exact text in document")
                    print(f"     Trying to find a shorter substring...")

                    # Try to find a substring if full text not found
                    # Take first 100 chars as fallback
                    if len(clause_text) > 100:
                        shorter_text = clause_text[:100]
                        position = find_text_position(document_url, shorter_text)
                        if position["found"]:
                            print(f"     ✓ Found using shorter text")
                            clause_text = shorter_text
                        else:
                            print(f"     ✗ Still not found. Skipping this violation.")
                            results.append({
                                "success": False,
                                "reason": "Text not found in document",
                                "policy": violation["policy_violated"]
                            })
                            continue
                    else:
                        results.append({
                            "success": False,
                            "reason": "Text not found in document",
                            "policy": violation["policy_violated"]
                        })
                        continue

                # Get color based on escalation level
                highlight_color = self.get_highlight_color(escalation_level)
                color_name = {
                    "Head of BU": "Yellow",
                    "BA President": "Orange",
                    "CEO": "Red"
                }.get(escalation_level, "Yellow")

                print(f"     Highlight color: {color_name}")

                # Format comment with approval line
                formatted_comment = f"{escalation_level} approval required\n\n{violation['comment']}"

                # Add comment with highlight
                print(f"     Adding comment and highlighting text at index {position['start_index']}...")
                result = add_comment(
                    document_id=document_url,
                    comment_text=formatted_comment,
                    quoted_text=clause_text,
                    highlight=True,
                    highlight_color=highlight_color,
                    add_prefix=True,
                )

                print(f"     ✓ Comment added successfully (ID: {result['comment_id']})")
                print(f"     ✓ Text highlighted: {result['highlighted']}")
                results.append(result)

            except Exception as e:
                print(f"     ✗ ERROR: {str(e)}")
                import traceback
                traceback.print_exc()
                results.append({
                    "success": False,
                    "reason": str(e),
                    "policy": violation.get("policy_violated", "Unknown")
                })

        # Summary
        successful = sum(1 for r in results if r.get("success", False))
        print(f"\n{'='*60}")
        print(f"Comments added: {successful}/{len(violations)}")
        print(f"{'='*60}")

        return results

    def evaluate(self, document_url: str) -> str:
        """Main evaluation workflow.

        Args:
            document_url: Google Docs URL of the contract

        Returns:
            HTML summary of the evaluation
        """
        # Analyze the contract
        analysis = self.analyze_contract(document_url)

        # Add comments to the document
        if analysis["violations"]:
            self.add_comments_to_contract(document_url, analysis["violations"])

        # Generate summary
        summary = self._generate_summary(document_url, analysis)
        return summary

    def _generate_summary(self, document_url: str, analysis: Dict[str, Any]) -> str:
        """Generate HTML summary of evaluation.

        Args:
            document_url: Google Docs URL
            analysis: Analysis results from Claude

        Returns:
            HTML formatted summary
        """
        num_violations = len(analysis["violations"])
        highest_escalation = analysis.get("highest_escalation", "None")

        summary = f"""{analysis['summary']}

<h2>Contract Terms Deviations from Policies</h2>

<p><strong>{num_violations}</strong> contract term(s) violate company policies and require escalation.</p>

<p><strong>Highest Approval Level Required:</strong> {highest_escalation}</p>

<p>Please visit the <a href="{document_url}">Google Docs contract</a> to review the highlighted clauses and detailed comments.</p>
"""

        return summary


def main():
    """Run contract evaluation on test document."""
    print("=" * 80)
    print("CONTRACT EVALUATOR - Powered by Claude Sonnet 4.5")
    print("=" * 80)
    print()

    # Check AWS credentials
    try:
        boto3.client("sts").get_caller_identity()
        print("✓ AWS credentials configured\n")
    except Exception as e:
        print(f"ERROR: AWS credentials not configured properly")
        print(f"Error: {e}")
        print("\nPlease configure AWS credentials using:")
        print("  - Environment variables (AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY)")
        print("  - AWS credentials file (~/.aws/credentials)")
        print("  - IAM role (if running on AWS)")
        return

    # Create evaluator
    evaluator = ContractEvaluator()

    # Evaluate contract
    print(f"Document URL: {TEST_DOC_URL}\n")

    try:
        summary = evaluator.evaluate(TEST_DOC_URL)

        print("\n" + "=" * 80)
        print("EVALUATION COMPLETE")
        print("=" * 80)
        print()
        print(summary)

    except Exception as e:
        print(f"\nERROR during evaluation: {e}")
        raise


if __name__ == "__main__":
    main()
