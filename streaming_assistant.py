"""
Streaming assistant for contract evaluation.

Handles user messages, extracts Google Docs URLs, and streams evaluation progress.
"""

import json
import re
from typing import List, Dict, Generator

import boto3

from evaluate_contract import ContractEvaluator
from google_docs_tools import get_approval_matrix_prompt


class StreamingContractAssistant:
    """Streaming assistant for contract evaluation via chat interface."""

    def __init__(self, aws_region: str = "us-west-2"):
        """Initialize the streaming assistant."""
        self.bedrock = boto3.client("bedrock-runtime", region_name=aws_region)
        self.model_id = "us.anthropic.claude-sonnet-4-5-20250929-v1:0"
        self.evaluator = ContractEvaluator(aws_region=aws_region)

    def extract_google_docs_url(self, message: str) -> str:
        """Extract Google Docs URL from user message.

        Args:
            message: User's message

        Returns:
            Google Docs URL or empty string if not found
        """
        # Pattern for Google Docs URLs
        patterns = [
            r'https://docs\.google\.com/document/d/([a-zA-Z0-9-_]+)',
            r'docs\.google\.com/document/d/([a-zA-Z0-9-_]+)',
        ]

        for pattern in patterns:
            match = re.search(pattern, message)
            if match:
                doc_id = match.group(1)
                return f"https://docs.google.com/document/d/{doc_id}/edit"

        return ""

    def stream_agent(self, messages: List[Dict[str, str]]) -> Generator[str, None, None]:
        """Stream agent responses for contract evaluation.

        Args:
            messages: List of chat messages with role and content

        Yields:
            String chunks of the response
        """
        # Get the latest user message
        user_message = messages[-1]["content"] if messages else ""

        # Extract Google Docs URL
        doc_url = self.extract_google_docs_url(user_message)

        if not doc_url:
            yield "I couldn't find a Google Docs URL in your message. "
            yield "Please provide a Google Docs contract URL to evaluate.\n\n"
            yield "Example: Please evaluate this contract: https://docs.google.com/document/d/YOUR_DOC_ID/edit"
            return

        # Stream the evaluation process
        yield f"📄 Found Google Docs URL\n"
        yield f"🔍 Starting contract evaluation...\n\n"

        try:
            # Analyze the contract
            yield "Reading contract from Google Docs...\n"
            analysis = self.evaluator.analyze_contract(doc_url)

            num_violations = len(analysis["violations"])
            highest_escalation = analysis.get("highest_escalation", "None")

            yield f"✅ Analysis complete\n\n"

            # Stream summary
            yield "📊 **Summary**\n"
            yield f"{analysis['summary']}\n\n"

            # Stream violation count and escalation
            yield "⚠️ **Contract Terms Deviations from Policies**\n\n"
            yield f"Found **{num_violations}** violation(s) that require escalation.\n\n"
            yield f"**Highest Approval Level Required:** {highest_escalation}\n\n"

            # Add comments if violations found
            if num_violations > 0:
                yield "💬 Adding comments and highlights to document...\n"

                results = self.evaluator.add_comments_to_contract(doc_url, analysis["violations"])

                successful = sum(1 for r in results if r.get("success", False))
                yield f"✅ Added {successful}/{num_violations} comments\n\n"

                # Stream color legend
                yield "🎨 **Color Guide:**\n"
                yield "- 🟡 Yellow = Head of BU approval\n"
                yield "- 🟠 Orange = BA President approval\n"
                yield "- 🔴 Red = CEO approval\n\n"

            # Stream link to document
            yield f"📋 **Review the contract:** [Open in Google Docs]({doc_url})\n\n"

            if num_violations > 0:
                yield "The violations have been highlighted with color-coded backgrounds and detailed comments. "
                yield "Click on each highlight to see the comment explaining the policy violation and required approval.\n"
            else:
                yield "No policy violations found. The contract complies with all approval matrix rules.\n"

        except Exception as e:
            yield f"\n❌ Error during evaluation: {str(e)}\n"
            yield "Please check:\n"
            yield "- The Google Docs URL is correct and accessible\n"
            yield "- You have edit/comment permissions on the document\n"
            yield "- AWS Bedrock credentials are configured\n"

    def invoke_streaming_claude(
        self,
        system_prompt: str,
        user_message: str
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
