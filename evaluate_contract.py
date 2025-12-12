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
import re
from typing import Dict, List, Any, Optional

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

# Previous contracts file
PREVIOUS_CONTRACTS_FILE = "previous-contracts.json"


def load_previous_contracts(file_path: str = PREVIOUS_CONTRACTS_FILE) -> List[Dict[str, Any]]:
    """Load previous contracts from JSON file.

    Args:
        file_path: Path to the previous contracts JSON file

    Returns:
        List of previous contract records
    """
    try:
        with open(file_path, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"Warning: Previous contracts file not found: {file_path}")
        return []
    except json.JSONDecodeError:
        print(f"Warning: Invalid JSON in previous contracts file: {file_path}")
        return []


def extract_customer_name(contract_text: str) -> Optional[str]:
    """Extract customer/purchaser name from contract text.

    Args:
        contract_text: Full contract text

    Returns:
        Customer name if found, None otherwise
    """
    # Common patterns for purchaser/customer name
    patterns = [
        # Pattern 1: PURCHASER on separate line, name on next line (more restrictive)
        r'PURCHASER\s*\n\s*([A-Z][a-zA-Z\s]+?(?:Oy|Ltd|Inc|Corp|GmbH|AB))\s*(?:\n|$)',
        # Pattern 2: PURCHASER: Name on same line
        r'PURCHASER[:\s]+([A-Z][a-zA-Z\s]+?(?:Oy|Ltd|Inc|Corp|GmbH|AB))(?:\s*\n|\s*,|\s*$)',
        # Pattern 3: Customer: Name
        r'Customer[:\s]+([A-Z][a-zA-Z\s]+?(?:Oy|Ltd|Inc|Corp|GmbH|AB))(?:\s*\n|\s*,|\s*$)',
        # Pattern 4: Buyer: Name
        r'Buyer[:\s]+([A-Z][a-zA-Z\s]+?(?:Oy|Ltd|Inc|Corp|GmbH|AB))(?:\s*\n|\s*,|\s*$)',
        # Pattern 5: between SUPPLIER and Name
        r'between[^a-zA-Z]+(?:the\s+)?SUPPLIER[^a-zA-Z]+and[^a-zA-Z]+([A-Z][a-zA-Z\s]+?(?:Oy|Ltd|Inc|Corp|GmbH|AB))',
        # Pattern 6: Name (purchaser) format
        r'([A-Z][a-zA-Z\s]+?(?:Oy|Ltd|Inc|Corp|GmbH|AB))\s*\((?:purchaser|customer|buyer)\)',
    ]

    for pattern in patterns:
        match = re.search(pattern, contract_text, re.IGNORECASE | re.MULTILINE)
        if match:
            customer_name = match.group(1).strip()
            # Clean up extra spaces
            customer_name = ' '.join(customer_name.split())
            # Verify it's not "SUPPLIER" or other common false positives
            if customer_name.upper() not in ['SUPPLIER', 'CONTRACTOR', 'VENDOR']:
                return customer_name

    return None


def get_customer_history(customer_name: str, previous_contracts: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Get contract history for a specific customer.

    Args:
        customer_name: Name of the customer
        previous_contracts: List of all previous contracts

    Returns:
        Dictionary with customer history statistics
    """
    # Filter contracts for this customer
    customer_contracts = [
        c for c in previous_contracts
        if c.get('purchaser', '').lower() == customer_name.lower()
    ]

    if not customer_contracts:
        return {
            "customer_name": customer_name,
            "has_history": False,
            "total_contracts": 0,
            "total_accepted_deviations": 0,
            "avg_negotiation_rounds": 0,
            "accepted_deviation_types": []
        }

    # Calculate statistics
    total_deviations = sum(len(c.get('accepted_deviations', [])) for c in customer_contracts)
    total_rounds = sum(c.get('customer_negotiation_rounds', 0) for c in customer_contracts)
    avg_rounds = total_rounds / len(customer_contracts) if customer_contracts else 0

    # Collect accepted deviation types
    accepted_types = []
    for contract in customer_contracts:
        for deviation in contract.get('accepted_deviations', []):
            accepted_types.append(deviation.get('condition', ''))

    return {
        "customer_name": customer_name,
        "has_history": True,
        "total_contracts": len(customer_contracts),
        "total_accepted_deviations": total_deviations,
        "avg_negotiation_rounds": round(avg_rounds, 1),
        "accepted_deviation_types": accepted_types,
        "recent_contracts": customer_contracts[:3]  # Most recent 3
    }


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

    def invoke_claude_streaming(self, system_prompt: str, user_message: str):
        """Invoke Claude via AWS Bedrock with streaming response.

        Args:
            system_prompt: System instructions for Claude
            user_message: User message/query

        Yields:
            Response text chunks from Claude
        """
        request_body = {
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": 4096,
            "temperature": 0.3,
            "system": system_prompt,
            "messages": [{"role": "user", "content": user_message}],
        }

        response = self.bedrock.invoke_model_with_response_stream(
            modelId=self.model_id,
            contentType="application/json",
            accept="application/json",
            body=json.dumps(request_body),
        )

        # Stream the response
        for event in response["body"]:
            chunk = json.loads(event["chunk"]["bytes"])

            if chunk["type"] == "content_block_delta":
                if "delta" in chunk and "text" in chunk["delta"]:
                    yield chunk["delta"]["text"]

    def analyze_contract(self, document_url: str) -> Dict[str, Any]:
        """Analyze a contract and identify policy violations.

        Args:
            document_url: Google Docs URL of the contract

        Returns:
            Dictionary with:
                - violations: List of found violations
                - highest_escalation: Highest approval level needed
                - summary: High-level summary
                - customer_name: Extracted customer name
                - customer_history: Historical data for this customer
                - recommendation: Strategic recommendation based on history
        """
        # Step 1: Read the contract
        print("Reading contract from Google Docs...")
        doc_data = get_document_text(document_url)
        contract_text = doc_data["full_text"]
        doc_title = doc_data["title"]

        print(f"Contract: {doc_title}")
        print(f"Length: {len(contract_text)} characters\n")

        # Step 2: Extract customer name and get history
        customer_name = extract_customer_name(contract_text)
        previous_contracts = load_previous_contracts()
        customer_history = None

        if customer_name:
            print(f"Customer identified: {customer_name}")
            customer_history = get_customer_history(customer_name, previous_contracts)
            print(f"Found {customer_history['total_contracts']} previous contracts with this customer")
            print(f"Accepted deviations: {customer_history['total_accepted_deviations']}")
            print(f"Avg negotiation rounds: {customer_history['avg_negotiation_rounds']}\n")
        else:
            print("Warning: Could not identify customer name from contract\n")

        # Step 3: Get approval matrix
        approval_matrix = get_approval_matrix_prompt(format="structured")

        # Step 4: Build historical context for LLM
        history_context = ""
        if customer_history and customer_history['has_history']:
            history_context = f"""

CUSTOMER HISTORY CONTEXT:
Customer: {customer_history['customer_name']}
Total previous contracts: {customer_history['total_contracts']}
Total accepted deviations: {customer_history['total_accepted_deviations']}
Average negotiation rounds: {customer_history['avg_negotiation_rounds']}
Previously accepted deviation types: {', '.join(customer_history['accepted_deviation_types']) if customer_history['accepted_deviation_types'] else 'None'}

IMPORTANT: Use this historical data when formulating your recommendation."""
        else:
            history_context = "\n\nCUSTOMER HISTORY: No previous contract history available for this customer."

        # Step 5: Ask Claude to analyze the contract
        print("Analyzing contract with Claude AI...")

        system_prompt = f"""You are a contract reviewer for a supplier company. Your ONLY job is to identify contract terms that trigger the specific approval matrix rules provided below, AND provide strategic recommendations based on customer history.

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

{history_context}

IMPORTANT CLARIFICATION ON "ACCEPTED DEVIATIONS":
- "Accepted deviations" means WE (the supplier) accepted the customer's non-standard terms that deviate from OUR policies
- This is NOT about whether the customer accepted our proposed changes
- High accepted deviations = We have been FLEXIBLE with this customer in the past
- Low/zero accepted deviations = We have been STRICT with this customer in the past

RECOMMENDATION GUIDELINES:
Based on the customer history and escalation level, provide ONE of these recommendations:

1. RECOMMEND RE-NEGOTIATION if:
   - High escalation level required (BA President or CEO) AND
   - WE have LOW/ZERO history of accepting this customer's deviations (< 30% or 0 deviations) AND/OR
   - Customer has HIGH average negotiation rounds (> 4 rounds)

   REASONING: Since we historically have NOT been flexible with this customer, these violations are UNLIKELY to be approved even with escalation. Better to re-negotiate with customer first to reduce/eliminate the violations before wasting executive time on escalation that will likely be rejected.

2. RECOMMEND DIRECT ESCALATION if:
   - WE have HIGH history of accepting this customer's deviations (> 50% or multiple accepted) AND
   - Customer has LOW average negotiation rounds (< 3 rounds) AND
   - Similar deviation types were accepted before

   REASONING: Since we have historically been flexible with this customer and accepted their deviations, these violations are LIKELY to be approved through escalation. Skip re-negotiation and escalate directly to save time.

3. RECOMMEND CAUTIOUS APPROACH if neither pattern is clear

RECOMMENDATION FORMAT REQUIREMENTS:
- Keep reasoning CONCISE (2-3 sentences maximum for intro + 3-4 short bullet points)
- Use plain text format with newlines
- Start with a brief intro sentence on its own line
- Add a blank line, then list 3-4 bullet points using dash (-)
- Each bullet point on a new line starting with "- "
- Keep each bullet to ONE line (max 100 characters)
- Example format:
  "Recommend re-negotiating before escalation given our strict historical stance.

- Zero accepted deviations with this customer (0/3 contracts)
- High negotiation rounds (6.3 avg) indicates difficult relationship
- Current violations unlikely to be approved internally
- Re-negotiation will save executive time and increase approval chances"

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
  "highest_escalation": "CEO|BA President|Head of BU",
  "recommendation": {{
    "action": "re-negotiate|escalate-directly|cautious-approach",
    "reasoning": "Plain text with intro, blank line, then bullet points (- ) on separate lines"
  }}
}}

REMEMBER:
- Only include violations that EXACTLY match an approval matrix rule
- Base recommendation on ACTUAL customer history data provided
- Be specific about which historical factors influenced your recommendation"""

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

    def analyze_contract_streaming(self, document_url: str, progress_callback=None):
        """Analyze a contract with streaming progress updates.

        Args:
            document_url: Google Docs URL of the contract
            progress_callback: Optional callback function to yield progress updates

        Yields:
            Tuple of (message_type, data) where:
            - ('progress', str): Progress message
            - ('analysis', dict): Final analysis result

        Returns:
            Dictionary with analysis results including customer history and recommendations
        """
        # Step 1: Read the contract
        if progress_callback:
            progress_callback('progress', 'Reading contract from Google Docs...')

        doc_data = get_document_text(document_url)
        contract_text = doc_data["full_text"]
        doc_title = doc_data["title"]

        if progress_callback:
            progress_callback('progress', f'📄 Contract: {doc_title} ({len(contract_text)} chars)')

        # Step 2: Extract customer name and get history
        customer_name = extract_customer_name(contract_text)
        previous_contracts = load_previous_contracts()
        customer_history = None

        if customer_name and progress_callback:
            progress_callback('progress', f'👤 Customer: {customer_name}')

        if customer_name:
            customer_history = get_customer_history(customer_name, previous_contracts)
            if progress_callback and customer_history['has_history']:
                progress_callback('progress', f'📊 Found {customer_history["total_contracts"]} previous contracts')

        # Step 3: Get approval matrix
        approval_matrix = get_approval_matrix_prompt(format="structured")

        # Step 4: Build historical context
        history_context = ""
        if customer_history and customer_history['has_history']:
            history_context = f"""

CUSTOMER HISTORY CONTEXT:
Customer: {customer_history['customer_name']}
Total previous contracts: {customer_history['total_contracts']}
Total accepted deviations: {customer_history['total_accepted_deviations']}
Average negotiation rounds: {customer_history['avg_negotiation_rounds']}
Previously accepted deviation types: {', '.join(customer_history['accepted_deviation_types']) if customer_history['accepted_deviation_types'] else 'None'}

IMPORTANT: Use this historical data when formulating your recommendation."""
        else:
            history_context = "\n\nCUSTOMER HISTORY: No previous contract history available for this customer."

        # Step 5: Stream Claude analysis
        if progress_callback:
            progress_callback('progress', '🤖 Analyzing contract with Claude AI...')

        system_prompt = f"""You are a contract reviewer for a supplier company. Your ONLY job is to identify contract terms that trigger the specific approval matrix rules provided below, AND provide strategic recommendations based on customer history.

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

{history_context}

IMPORTANT CLARIFICATION ON "ACCEPTED DEVIATIONS":
- "Accepted deviations" means WE (the supplier) accepted the customer's non-standard terms that deviate from OUR policies
- This is NOT about whether the customer accepted our proposed changes
- High accepted deviations = We have been FLEXIBLE with this customer in the past
- Low/zero accepted deviations = We have been STRICT with this customer in the past

RECOMMENDATION GUIDELINES:
Based on the customer history and escalation level, provide ONE of these recommendations:

1. RECOMMEND RE-NEGOTIATION if:
   - High escalation level required (BA President or CEO) AND
   - WE have LOW/ZERO history of accepting this customer's deviations (< 30% or 0 deviations) AND/OR
   - Customer has HIGH average negotiation rounds (> 4 rounds)

   REASONING: Since we historically have NOT been flexible with this customer, these violations are UNLIKELY to be approved even with escalation. Better to re-negotiate with customer first to reduce/eliminate the violations before wasting executive time on escalation that will likely be rejected.

2. RECOMMEND DIRECT ESCALATION if:
   - WE have HIGH history of accepting this customer's deviations (> 50% or multiple accepted) AND
   - Customer has LOW average negotiation rounds (< 3 rounds) AND
   - Similar deviation types were accepted before

   REASONING: Since we have historically been flexible with this customer and accepted their deviations, these violations are LIKELY to be approved through escalation. Skip re-negotiation and escalate directly to save time.

3. RECOMMEND CAUTIOUS APPROACH if neither pattern is clear

RECOMMENDATION FORMAT REQUIREMENTS:
- Keep reasoning CONCISE (2-3 sentences maximum for intro + 3-4 short bullet points)
- Use plain text format with newlines
- Start with a brief intro sentence on its own line
- Add a blank line, then list 3-4 bullet points using dash (-)
- Each bullet point on a new line starting with "- "
- Keep each bullet to ONE line (max 100 characters)
- Example format:
  "Recommend re-negotiating before escalation given our strict historical stance.

- Zero accepted deviations with this customer (0/3 contracts)
- High negotiation rounds (6.3 avg) indicates difficult relationship
- Current violations unlikely to be approved internally
- Re-negotiation will save executive time and increase approval chances"

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
  "highest_escalation": "CEO|BA President|Head of BU",
  "recommendation": {{
    "action": "re-negotiate|escalate-directly|cautious-approach",
    "reasoning": "Plain text with intro, blank line, then bullet points (- ) on separate lines"
  }}
}}

REMEMBER:
- Only include violations that EXACTLY match an approval matrix rule
- Base recommendation on ACTUAL customer history data provided
- Be specific about which historical factors influenced your recommendation"""

        user_message = f"""Please analyze this contract and identify all terms that trigger the approval matrix rules:

CONTRACT TITLE: {doc_title}

CONTRACT TEXT:
{contract_text}

Return your analysis as valid JSON."""

        # Stream the response
        response = ""
        for chunk in self.invoke_claude_streaming(system_prompt, user_message):
            response += chunk
            # Don't yield every token to avoid overwhelming the frontend
            # Just show we're making progress

        if progress_callback:
            progress_callback('progress', '✅ Analysis complete, parsing results...')

        # Parse Claude's response
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
