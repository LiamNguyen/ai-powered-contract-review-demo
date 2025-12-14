"""
Streaming assistant for contract evaluation.

Handles user messages, extracts Google Docs URLs, and streams evaluation progress.
"""

import json
import re
from typing import List, Dict, Generator

import boto3

from evaluate_contract import ContractEvaluator
from google_docs_tools import get_approval_matrix_prompt, send_escalation_email


class StreamingContractAssistant:
    """Streaming assistant for contract evaluation via chat interface."""

    def __init__(self, aws_region: str = "us-west-2"):
        """Initialize the streaming assistant."""
        self.bedrock = boto3.client("bedrock-runtime", region_name=aws_region)
        self.model_id = "us.anthropic.claude-sonnet-4-5-20250929-v1:0"
        self.evaluator = ContractEvaluator(aws_region=aws_region)

        # Store last evaluation for email sending
        self.last_evaluation = None

    def extract_google_docs_url(self, message: str) -> str:
        """Extract Google Docs URL from user message.

        Args:
            message: User's message

        Returns:
            Google Docs URL or empty string if not found
        """
        # Pattern for Google Docs URLs
        patterns = [
            r"https://docs\.google\.com/document/d/([a-zA-Z0-9-_]+)",
            r"docs\.google\.com/document/d/([a-zA-Z0-9-_]+)",
        ]

        for pattern in patterns:
            match = re.search(pattern, message)
            if match:
                doc_id = match.group(1)
                return f"https://docs.google.com/document/d/{doc_id}/edit"

        return ""

    def stream_agent(
        self, messages: List[Dict[str, str]]
    ) -> Generator[str, None, None]:
        """Stream agent responses for contract evaluation.

        Args:
            messages: List of chat messages with role and content

        Yields:
            String chunks of the response
        """
        # Get the latest user message
        user_message = messages[-1]["content"] if messages else ""

        # Check if user is confirming email send with a simple "yes"
        simple_affirmations = [
            "yes",
            "yeah",
            "yep",
            "sure",
            "ok",
            "okay",
            "send it",
            "please send",
            "go ahead",
        ]
        is_simple_yes = user_message.lower().strip().rstrip(".!") in simple_affirmations

        # If user says "yes" and we have a previous evaluation, send email
        if is_simple_yes and self.last_evaluation:
            yield "📧 Sending escalation email to Antti (Head of BU)...\n\n"

            email_result = send_escalation_email(
                to_email="liamnguyen1208@gmail.com",
                recipient_name="Antti",
                contract_title=self.last_evaluation["doc_title"],
                contract_url=self.last_evaluation["doc_url"],
                violations_summary=self.last_evaluation["violations_summary"],
                escalation_level=self.last_evaluation["highest_escalation"],
            )

            if email_result["success"]:
                yield f"✅ Email sent successfully to Antti (liamnguyen1208@gmail.com)\n\n"
            else:
                yield f"❌ Failed to send email: {email_result['error']}\n\n"
                yield "Please check your Gmail API credentials and permissions.\n\n"

            # Clear the stored evaluation
            self.last_evaluation = None
            return

        # Check if user wants to send an email (with URL in message)
        send_email_keywords = [
            "send email",
            "send the email",
            "yes send",
            "send escalation",
        ]
        is_email_request = any(
            keyword in user_message.lower() for keyword in send_email_keywords
        )

        # Extract Google Docs URL
        doc_url = self.extract_google_docs_url(user_message)

        if not doc_url:
            # If user said "yes" but no previous evaluation, inform them
            if is_simple_yes:
                yield "I don't have a recent contract evaluation to send an email for.\n\n"
                yield "**Note:** Emails are only sent when my recommendation is to **Escalate Directly**.\n"
                yield "If the recommendation was to **Re-Negotiate**, you should negotiate with the customer first before escalating.\n\n"
                yield "Please evaluate a contract first, then I can send the escalation email if appropriate.\n\n"
                yield "Example: Please evaluate this contract: https://docs.google.com/document/d/YOUR_DOC_ID/edit"
            else:
                yield "I couldn't find a Google Docs URL in your message. "
                yield "Please provide a Google Docs contract URL to evaluate.\n\n"
                yield "Example: Please evaluate this contract: https://docs.google.com/document/d/YOUR_DOC_ID/edit"
            return

        # Stream the evaluation process
        yield f"📄 Found Google Docs URL\n\n"
        yield f"🔍 Starting contract evaluation...\n\n"

        try:
            # Analyze the contract with streaming
            yield "📖 Reading contract from Google Docs...\n\n"

            # Show progress during analysis
            yield "🤖 Analyzing with Claude AI\n\n"

            # Use streaming analysis with progress dots
            import time

            analysis = None

            # Start analysis in a way that shows progress
            from google_docs_tools import get_document_text, get_approval_matrix_prompt
            from evaluate_contract import (
                extract_customer_name,
                get_customer_history,
                load_previous_contracts,
            )
            import json

            # Read document
            doc_data = get_document_text(doc_url)
            contract_text = doc_data["full_text"]
            doc_title = doc_data["title"]

            # Extract customer name and get history
            customer_name = extract_customer_name(contract_text)
            previous_contracts = load_previous_contracts()
            customer_history = None

            if customer_name:
                yield f"👤 Customer: {customer_name}\n\n"
                customer_history = get_customer_history(
                    customer_name, previous_contracts
                )
                if customer_history["has_history"]:
                    yield f"📊 {customer_history['total_contracts']} previous contracts, {customer_history['total_accepted_deviations']} accepted deviations\n\n"

            # Get approval matrix
            approval_matrix = get_approval_matrix_prompt(format="structured")

            # Build historical context for LLM
            history_context = ""
            if customer_history and customer_history["has_history"]:
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

            # Build prompts
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

            # Stream Claude's response with progress indicators
            response = ""
            last_dot_time = time.time()
            dot_count = 0

            for chunk in self.evaluator.invoke_claude_streaming(
                system_prompt, user_message
            ):
                response += chunk

                # Show a dot every 2 seconds to indicate progress
                current_time = time.time()
                if current_time - last_dot_time > 2.0:
                    dot_count += 1
                    if dot_count <= 15:  # Max 15 dots
                        yield "."
                    last_dot_time = current_time

            yield "\n"

            # Parse response
            json_text = response
            if "```json" in response:
                json_text = response.split("```json")[1].split("```")[0].strip()
            elif "```" in response:
                json_text = response.split("```")[1].split("```")[0].strip()

            analysis = json.loads(json_text)

            num_violations = len(analysis["violations"])
            highest_escalation = analysis.get("highest_escalation", "None")

            yield f"✅ Analysis complete\n\n"

            # Stream summary in small chunks for smooth effect
            yield "📊 **Summary**\n"
            summary_text = analysis["summary"]

            # Yield 2-3 words at a time (sweet spot for smooth streaming without buffering)
            words = summary_text.split()
            for i in range(0, len(words), 2):
                chunk = " ".join(words[i : i + 2]) + " "
                yield chunk

            yield "\n\n"

            # Stream violation count and escalation
            yield "⚠️ **Contract Terms Deviations from Policies**\n\n"
            yield f"Found **{num_violations}** violation(s) that require escalation.\n\n"
            yield f"**Highest Approval Level Required:** {highest_escalation}\n\n"

            # Stream recommendations section
            recommendation_action = None
            if "recommendation" in analysis:
                yield "💡 **My Recommendation**\n\n"

                recommendation = analysis["recommendation"]
                recommendation_action = recommendation.get("action", "")
                action = recommendation_action.replace("-", " ").title()

                # Stream action
                yield f"**Recommended Action:** {action}\n\n"

                # Stream reasoning (don't split HTML into words!)
                reasoning = recommendation.get("reasoning", "")
                yield reasoning
                yield "\n\n"

            # Add comments if violations found
            if num_violations > 0:
                yield "💬 Adding comments and highlights to document...\n\n"

                # Stream comment addition progress
                results = []
                for i, violation in enumerate(analysis["violations"], 1):
                    # Add single comment
                    result = self.evaluator.add_comments_to_contract(
                        doc_url, [violation]
                    )
                    results.extend(result)

                    # Yield progress after each comment
                    if result and result[0].get("success"):
                        yield f"   ✓ Added comment {i}/{num_violations}\n\n"
                    else:
                        yield f"   ⚠ Failed to add comment {i}/{num_violations}\n\n"

                successful = sum(1 for r in results if r.get("success", False))
                yield f"\n✅ Completed: {successful}/{num_violations} comments added\n\n"

                # Stream color legend
                yield "🎨 **Color Guide:**\n"
                yield "- 🟡 Yellow = Head of BU approval\n"
                yield "- 🟠 Orange = BA President approval\n"
                yield "- 🔴 Red = CEO approval\n\n"

            # Stream link to document
            yield f"📋 **Review the contract:** [Open in Google Docs]({doc_url})\n\n"

            if num_violations > 0:
                # Stream closing message in small chunks
                closing_msg = "The violations have been highlighted with color-coded backgrounds and detailed comments. Click on each highlight to see the comment explaining the policy violation and required approval."
                words = closing_msg.split()
                for i in range(0, len(words), 2):
                    chunk = " ".join(words[i : i + 2]) + " "
                    yield chunk
                yield "\n\n"

                # Build violations summary
                violations_summary = ""
                for i, violation in enumerate(analysis["violations"], 1):
                    violations_summary += f"{i}. {violation['category']}: {violation['policy_violated']}\n"

                # Check if we should prompt for email (only for "escalate-directly" recommendation)
                should_offer_email = recommendation_action == "escalate-directly"

                # Store evaluation for potential email sending (only if escalate-directly)
                if should_offer_email:
                    self.last_evaluation = {
                        "doc_url": doc_url,
                        "doc_title": doc_title,
                        "violations_summary": violations_summary,
                        "highest_escalation": highest_escalation,
                        "violations": analysis["violations"],
                    }

                # Handle email sending or prompt (only if escalate-directly)
                if should_offer_email:
                    if is_email_request:
                        # User requested to send email
                        yield "📧 Sending escalation email to Antti (Head of BU)...\n\n"

                        # Send email
                        email_result = send_escalation_email(
                            to_email="liamnguyen1208@gmail.com",
                            recipient_name="Antti",
                            contract_title=doc_title,
                            contract_url=doc_url,
                            violations_summary=violations_summary,
                            escalation_level=highest_escalation,
                        )

                        if email_result["success"]:
                            yield f"✅ Email sent successfully to Antti (liamnguyen1208@gmail.com)\n\n"
                            yield f"📨 Message ID: {email_result['message_id']}\n\n"
                        else:
                            yield f"❌ Failed to send email: {email_result['error']}\n\n"
                            yield "Please check your Gmail API credentials and permissions.\n\n"

                        # Clear stored evaluation after sending
                        self.last_evaluation = None
                    else:
                        # Prompt user to send email
                        yield "---\n\n"
                        yield f"📧 **Escalation Required**\n\n"
                        yield f"This contract requires **{highest_escalation}** approval. "
                        yield "Would you like me to send an escalation email to Antti (Head of BU)?\n\n"
                        yield "Simply reply: **Yes**\n"
            else:
                msg = "No policy violations found. The contract complies with all approval matrix rules."
                words = msg.split()
                for i in range(0, len(words), 2):
                    chunk = " ".join(words[i : i + 2]) + " "
                    yield chunk
                yield "\n"

        except Exception as e:
            yield f"\n❌ Error during evaluation: {str(e)}\n"
            yield "Please check:\n"
            yield "- The Google Docs URL is correct and accessible\n"
            yield "- You have edit/comment permissions on the document\n"
            yield "- AWS Bedrock credentials are configured\n"

    def invoke_streaming_claude(
        self, system_prompt: str, user_message: str
    ) -> Generator[str, None, None]:
        """Invoke Claude with streaming response.

        Args:
            system_prompt: System instructions
            user_message: User message

        Yields:
            Response chunks from Claude
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
