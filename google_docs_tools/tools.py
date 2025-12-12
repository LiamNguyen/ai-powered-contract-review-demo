"""Google Docs tools for LLM integration.

These functions can be used as tools for an LLM to read Google Docs
and add comments to specific text ranges.
"""

import base64
import json
import re
from email.mime.text import MIMEText
from pathlib import Path
from typing import Optional

from .auth import get_docs_service, get_drive_service, get_gmail_service

# Path to approval matrix
PROJECT_ROOT = Path(__file__).parent.parent
APPROVAL_MATRIX_FILE = PROJECT_ROOT / "contract_approval_matrix.json"


def extract_document_id(doc_id_or_url: str) -> str:
    """Extract document ID from a Google Docs URL or return ID if already an ID."""
    # Pattern for Google Docs URLs
    patterns = [
        r"/document/d/([a-zA-Z0-9-_]+)",
        r"^([a-zA-Z0-9-_]+)$",
    ]
    for pattern in patterns:
        match = re.search(pattern, doc_id_or_url)
        if match:
            return match.group(1)
    raise ValueError(f"Could not extract document ID from: {doc_id_or_url}")


def read_document(document_id: str) -> dict:
    """Read a Google Doc and return its structure.

    Args:
        document_id: The Google Doc ID or full URL.

    Returns:
        dict with:
            - title: Document title
            - document_id: The document ID
            - body: The full body content structure from the API
            - text_with_indices: List of text segments with their start/end indices
    """
    doc_id = extract_document_id(document_id)
    service = get_docs_service()

    doc = service.documents().get(documentId=doc_id).execute()

    # Extract text with indices for easier comment anchoring
    text_segments = []
    if "body" in doc and "content" in doc["body"]:
        for element in doc["body"]["content"]:
            _extract_text_from_element(element, text_segments)

    return {
        "title": doc.get("title", "Untitled"),
        "document_id": doc_id,
        "body": doc.get("body", {}),
        "text_with_indices": text_segments,
    }


def _extract_text_from_element(element: dict, segments: list) -> None:
    """Recursively extract text and indices from document elements."""
    start_index = element.get("startIndex", 0)
    end_index = element.get("endIndex", 0)

    if "paragraph" in element:
        para = element["paragraph"]
        for elem in para.get("elements", []):
            if "textRun" in elem:
                text_run = elem["textRun"]
                segments.append(
                    {
                        "text": text_run.get("content", ""),
                        "start_index": elem.get("startIndex", 0),
                        "end_index": elem.get("endIndex", 0),
                    }
                )

    if "table" in element:
        table = element["table"]
        for row in table.get("tableRows", []):
            for cell in row.get("tableCells", []):
                for content in cell.get("content", []):
                    _extract_text_from_element(content, segments)


def get_document_text(document_id: str) -> dict:
    """Get plain text content from a Google Doc with character indices.

    This is useful for finding the exact position to anchor comments.

    Args:
        document_id: The Google Doc ID or full URL.

    Returns:
        dict with:
            - title: Document title
            - document_id: The document ID
            - full_text: Complete plain text of the document
            - segments: List of text segments with indices
    """
    doc_data = read_document(document_id)

    full_text = ""
    for segment in doc_data["text_with_indices"]:
        full_text += segment["text"]

    return {
        "title": doc_data["title"],
        "document_id": doc_data["document_id"],
        "full_text": full_text,
        "segments": doc_data["text_with_indices"],
    }


def add_comment(
    document_id: str,
    comment_text: str,
    quoted_text: str,
    highlight: bool = True,
    highlight_color: Optional[dict] = None,
    add_prefix: bool = True,
) -> dict:
    """Add a comment to specific text in a Google Doc with visual anchoring.

    Since the Google Drive API cannot create native click-to-highlight anchors
    for Google Docs, this function uses "visual anchoring":
    1. Highlights the target text with a background color (Docs API)
    2. Adds the comment with quotedFileContent for context (Drive API)
    3. Prefixes comment with target text for easy identification

    Args:
        document_id: The Google Doc ID or full URL.
        comment_text: The content of the comment.
        quoted_text: The exact text to anchor the comment to.
        highlight: Whether to highlight the text (default True).
        highlight_color: RGB color dict, e.g. {"red": 1.0, "green": 1.0, "blue": 0.8}.
                        Defaults to light yellow.
        add_prefix: Whether to add "[Re: '...']" prefix to comment (default True).

    Returns:
        dict with:
            - success: Whether the comment was created
            - comment_id: The ID of the created comment
            - comment: The full comment resource from the API
            - highlighted: Whether text was highlighted
    """
    doc_id = extract_document_id(document_id)

    # Find the position of the quoted text
    position = find_text_position(document_id, quoted_text)

    if not position["found"]:
        raise ValueError(f"Could not find text: {quoted_text[:50]}...")

    highlighted = False

    # Step 1: Highlight the text using Docs API
    if highlight:
        docs_service = get_docs_service()

        if highlight_color is None:
            highlight_color = {"red": 1.0, "green": 1.0, "blue": 0.8}  # Light yellow

        requests = [
            {
                "updateTextStyle": {
                    "range": {
                        "startIndex": position["start_index"],
                        "endIndex": position["start_index"] + position["length"],
                    },
                    "textStyle": {
                        "backgroundColor": {"color": {"rgbColor": highlight_color}}
                    },
                    "fields": "backgroundColor",
                }
            }
        ]

        docs_service.documents().batchUpdate(
            documentId=doc_id,
            body={"requests": requests},
        ).execute()
        highlighted = True

    # Step 2: Add comment with quotedFileContent (no anchor field)
    drive_service = get_drive_service()

    # Add prefix to comment for easy identification
    if add_prefix:
        # Truncate quoted text if too long for prefix
        prefix_text = (
            quoted_text if len(quoted_text) <= 50 else quoted_text[:47] + "..."
        )
        final_comment_text = f"[Re: '{prefix_text}']\n\n{comment_text}"
    else:
        final_comment_text = comment_text

    comment_body = {
        "content": final_comment_text,
        "quotedFileContent": {
            "mimeType": "text/html",
            "value": quoted_text,
        },
    }

    result = (
        drive_service.comments()
        .create(
            fileId=doc_id,
            body=comment_body,
            fields="id,content,quotedFileContent,author,createdTime",
        )
        .execute()
    )

    return {
        "success": True,
        "comment_id": result.get("id"),
        "comment": result,
        "highlighted": highlighted,
    }


def create_document(title: str, content: str = "") -> dict:
    """Create a new Google Doc.

    Args:
        title: The title of the document.
        content: Optional initial text content.

    Returns:
        dict with:
            - document_id: The ID of the created document
            - title: The document title
            - url: URL to open the document
    """
    service = get_docs_service()

    # Create empty document
    doc = service.documents().create(body={"title": title}).execute()
    doc_id = doc.get("documentId")

    # Add content if provided
    if content:
        requests = [
            {
                "insertText": {
                    "location": {"index": 1},
                    "text": content,
                }
            }
        ]
        service.documents().batchUpdate(
            documentId=doc_id, body={"requests": requests}
        ).execute()

    return {
        "document_id": doc_id,
        "title": title,
        "url": f"https://docs.google.com/document/d/{doc_id}/edit",
    }


def find_text_position(document_id: str, search_text: str) -> dict:
    """Find the position of specific text in a document.

    Uses actual Google Docs indices for proper comment anchoring.

    Args:
        document_id: The Google Doc ID or full URL.
        search_text: The text to search for.

    Returns:
        dict with:
            - found: Whether the text was found
            - start_index: The actual document index (for anchoring)
            - length: Length of the text
            - context: Surrounding text for verification
    """
    doc_data = read_document(document_id)
    segments = doc_data["text_with_indices"]

    # Build full text while tracking the document index for each character
    full_text = ""
    char_to_doc_index = []  # Maps each char position in full_text to doc index

    for segment in segments:
        seg_text = segment["text"]
        seg_start = segment["start_index"]
        for i, char in enumerate(seg_text):
            char_to_doc_index.append(seg_start + i)
        full_text += seg_text

    # Find the search text in full_text
    text_pos = full_text.find(search_text)
    if text_pos == -1:
        return {
            "found": False,
            "start_index": None,
            "length": None,
            "context": None,
        }

    # Get the actual document index
    doc_index = char_to_doc_index[text_pos]

    # Get some context around the match
    context_start = max(0, text_pos - 20)
    context_end = min(len(full_text), text_pos + len(search_text) + 20)
    context = full_text[context_start:context_end]

    return {
        "found": True,
        "start_index": doc_index,
        "length": len(search_text),
        "context": f"...{context}...",
    }


def get_approval_matrix_prompt(
    matrix_file: Optional[str] = None, format: str = "markdown"
) -> str:
    """Format the contract approval matrix for embedding in LLM system prompts.

    Args:
        matrix_file: Path to approval matrix JSON file. Defaults to contract_approval_matrix.json.
        format: Output format - "markdown" (default), "structured", or "compact"

    Returns:
        Formatted string ready to be embedded in an LLM system prompt.
    """
    if matrix_file is None:
        matrix_file = APPROVAL_MATRIX_FILE

    with open(matrix_file, "r") as f:
        rules = json.load(f)

    if format == "markdown":
        return _format_matrix_markdown(rules)
    elif format == "structured":
        return _format_matrix_structured(rules)
    elif format == "compact":
        return _format_matrix_compact(rules)
    else:
        raise ValueError(
            f"Unknown format: {format}. Use 'markdown', 'structured', or 'compact'"
        )


def _format_matrix_markdown(rules: list) -> str:
    """Format approval matrix as markdown tables."""
    output = ["# Contract Approval Matrix", ""]
    output.append("Use this matrix to determine required approvals for contract terms:")
    output.append("")

    # Group rules by category
    by_category = {}
    for rule in rules:
        category = rule["Category"]
        if category not in by_category:
            by_category[category] = []
        by_category[category].append(rule)

    for category, category_rules in by_category.items():
        output.append(f"## {category}")
        output.append("")

        for rule in category_rules:
            output.append(f"### Condition: {rule['Condition']}")
            output.append("")
            output.append("| Role | Involvement Level |")
            output.append("|------|-------------------|")

            for role, involvement in rule["Approval_Matrix"].items():
                output.append(f"| {role} | {involvement} |")

            output.append("")

    return "\n".join(output)


def _format_matrix_structured(rules: list) -> str:
    """Format approval matrix as structured text blocks."""
    output = ["CONTRACT APPROVAL MATRIX", "=" * 80, ""]

    for i, rule in enumerate(rules, 1):
        output.append(f"RULE #{i}")
        output.append("-" * 80)
        output.append(f"Category: {rule['Category']}")
        output.append(f"Trigger Condition: {rule['Condition']}")
        output.append("")
        output.append("Required Approvals:")

        for role, involvement in rule["Approval_Matrix"].items():
            output.append(f"  • {role}: {involvement}")

        output.append("")

    return "\n".join(output)


def _format_matrix_compact(rules: list) -> str:
    """Format approval matrix in compact format for smaller prompts."""
    output = ["CONTRACT APPROVAL RULES:"]

    for i, rule in enumerate(rules, 1):
        approvers = [
            f"{role}({involvement})"
            for role, involvement in rule["Approval_Matrix"].items()
        ]
        output.append(
            f"{i}. [{rule['Category']}] IF {rule['Condition']} "
            f"THEN REQUIRE: {', '.join(approvers)}"
        )

    return "\n".join(output)


def send_escalation_email(
    to_email: str,
    recipient_name: str,
    contract_title: str,
    contract_url: str,
    violations_summary: str,
    escalation_level: str,
) -> dict:
    """Send an escalation email via Gmail API.

    Args:
        to_email: Recipient's email address
        recipient_name: Recipient's name (e.g., "Antti")
        contract_title: Title of the contract document
        contract_url: URL to the Google Docs contract
        violations_summary: Summary of contract violations
        escalation_level: Required escalation level (e.g., "Head of BU", "BA President", "CEO")

    Returns:
        dict with:
            - success: Whether the email was sent successfully
            - message_id: The ID of the sent message
            - error: Error message if failed
    """
    try:
        gmail_service = get_gmail_service()

        # Create email content
        subject = f"Contract Approval Required: {contract_title}"

        body = f"""Dear {recipient_name},

Approval is required for the following contract that has been evaluated and requires escalation to {escalation_level}.

Contract: {contract_title}
Review here: {contract_url}

Summary of Policy Violations:
{violations_summary}

Please review the contract at your earliest convenience. The violations have been highlighted in the document with color-coded backgrounds and detailed comments.

Color Guide:
- Yellow = Head of BU approval
- Orange = BA President approval
- Red = CEO approval

Best regards,
Contract Approval System
"""

        # Create MIME message
        message = MIMEText(body)
        message["to"] = to_email
        message["subject"] = subject

        # Encode the message
        raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode("utf-8")

        # Send the email
        send_message = (
            gmail_service.users()
            .messages()
            .send(userId="me", body={"raw": raw_message})
            .execute()
        )

        return {"success": True, "message_id": send_message.get("id"), "error": None}

    except Exception as e:
        return {"success": False, "message_id": None, "error": str(e)}
