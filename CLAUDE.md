# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is an AI-driven contract approval system that integrates with Google Docs and Google Drive APIs. The system:
- Reads Google Docs contracts
- Analyzes contract terms against approval policies
- Adds visual anchored comments to specific clauses
- Uses an approval matrix to determine required stakeholder sign-offs

## Architecture

### FastAPI Application (Recommended for Production)

**app.py** - FastAPI web server with streaming endpoints
- Provides `/chat/stream` endpoint for real-time evaluation
- Accepts natural language messages with Google Docs URLs
- Streams progress updates during evaluation
- Provides `/send-email` endpoint for escalation notifications
- CORS-enabled for frontend integration

**streaming_assistant.py** - Streaming chat assistant
- Extracts Google Docs URLs from user messages using regex
- Orchestrates the evaluation workflow
- Streams response chunks back to client
- Integrates with ContractEvaluator
- Prompts user to send escalation emails after evaluation
- Detects "send email" intent in follow-up messages

Workflow:
1. User sends message via POST /chat/stream with Google Docs URL
2. StreamingAssistant extracts URL and analyzes contract
3. Streams real-time progress updates during evaluation
4. Returns formatted summary with evaluation results
5. If escalation required, stores evaluation and prompts: "Simply reply: Yes"
6. User replies "Yes" (or similar) → email sent immediately without re-evaluation
7. Evaluation cleared from memory after email is sent

### Standalone Application

**evaluate_contract.py** - AI-powered contract evaluator
- Uses Claude Sonnet 4.5 via AWS Bedrock to analyze contracts
- Reads Google Docs contracts and compares against approval matrix
- Automatically adds comments and highlights to problematic clauses
- Generates HTML summary with escalation recommendations

**IMPORTANT**: The LLM is strictly instructed to ONLY flag violations that match the approval matrix conditions. It does not use general contract knowledge to identify issues beyond the defined policies.

Workflow:
1. Read contract from Google Docs
2. Send contract + approval matrix to Claude for analysis
3. Claude identifies policy violations (ONLY those matching matrix rules)
4. Script adds comments to specific clauses in the doc
5. Returns HTML summary showing violations and required approvals

Comment Addition Process:
- Finds exact text in document using character-by-character mapping
- Highlights text with **color-coded background** based on escalation level:
  - Yellow (Head of BU)
  - Orange (BA President)
  - Red (CEO)
- Adds comment with detailed explanation (Drive API)
- Comment format: `[Re: '...']` then `{Role} approval required` then explanation
- Falls back to substring search if exact match not found

Text Extraction Strategy:
- LLM instructed to extract the EXACT clause containing the violation
- Targets the specific sentence/phrase with the violating number/term
- Avoids paragraph introductions or conditional clauses before the violation
- Example: Instead of extracting "If equipment is delayed...the supplier shall pay 20%", it extracts "the SUPPLIER shall pay...20% per cent of the CONTRACT PRICE as liquidated damages"

### Core Components

**google_docs_tools/** - Python package for Google API integration
- `auth.py`: OAuth2 authentication with token caching, Gmail API service
- `tools.py`: High-level API wrappers for reading docs, adding comments, and sending emails
- `__init__.py`: Exports main functions: `read_document`, `add_comment`, `get_document_text`, `find_text_position`, `create_document`, `get_approval_matrix_prompt`, `send_escalation_email`

**contract_approval_matrix.json** - Policy rules defining:
- Contract condition thresholds (e.g., "Total liability cap >100%")
- Required approvers per category
- Approval workflows by stakeholder role

### Comment Anchoring Strategy

The system uses "visual anchoring" due to Google API limitations:
1. Highlights target text with background color via Docs API `updateTextStyle` request
2. Creates comment via Drive API with `quotedFileContent` for context
3. Adds `[Re: '...']` prefix to comment for easy identification

This approach works around the fact that the Drive API cannot create native click-to-highlight anchors for Google Docs.

### Index Mapping

Document indices from the Docs API don't match plain text positions. The `find_text_position()` function builds a character-to-document-index mapping by:
1. Extracting all text segments with their `startIndex`/`endIndex` from the API
2. Building a lookup table that maps each character position in the plain text to its actual document index
3. Using this mapping to get correct indices for the `updateTextStyle` range

## Development Setup

**Prerequisites:**
```bash
# Virtual environment is already set up in venv/
source venv/bin/activate  # macOS/Linux
```

**Google Cloud Setup Required:**
1. Create Google Cloud project
2. Enable Google Docs API, Google Drive API, and Gmail API
3. Create OAuth 2.0 credentials (Desktop app type)
4. Download `credentials.json` to project root
5. First run opens browser for authentication
6. Token cached in `token.json` for subsequent runs
7. **IMPORTANT**: After adding Gmail scope, delete `token.json` and re-authenticate to get Gmail permissions

**Dependencies:**
```bash
pip install -r requirements.txt
# Installs: google-api-python-client, google-auth-httplib2, google-auth-oauthlib, boto3
```

**AWS Bedrock Setup Required:**
1. Configure AWS credentials (one of these methods):
   - Environment variables: `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`
   - AWS credentials file: `~/.aws/credentials`
   - IAM role (if running on AWS EC2/ECS)
2. Ensure your AWS account has access to Claude Sonnet 4.5 in Bedrock
3. Default region: `us-west-2` (can be changed via `AWS_REGION` env var)
4. Inference profile used: `us.anthropic.claude-sonnet-4-5-20250929-v1:0`

## Common Commands

**Run FastAPI server (recommended for frontend integration):**
```bash
# Development mode with auto-reload
uvicorn app:app --reload --port 8000

# Production mode
uvicorn app:app --host 0.0.0.0 --port 8000 --workers 4

# Test the API
python test_api.py
```

**Run contract evaluator (standalone Python script):**
```bash
# Requires AWS credentials configured for Bedrock access
python evaluate_contract.py
```

**Run tests:**
```bash
python test_google_docs.py
```

**Test specific functionality:**
```python
# In test_google_docs.py, uncomment the test functions you want:
# - test_read_document()      # Tests reading doc structure
# - test_get_document_text()  # Tests plain text extraction
# - test_find_text()          # Tests text position finding
# - test_comment_on_liquidated_damages()  # Tests adding comment to specific clause
# - test_comment_on_payment_terms()       # Tests adding comment to payment terms
# - test_comment_on_total_liability_cap() # Tests adding comment to liability cap
```

**Interactive testing:**
```python
from google_docs_tools import read_document, get_document_text, add_comment, find_text_position

# Read a document
doc = get_document_text("https://docs.google.com/document/d/...")

# Find text position
pos = find_text_position(doc_id, "specific text to find")

# Add comment with highlight
result = add_comment(
    document_id=doc_id,
    comment_text="Your comment here",
    quoted_text="exact text to anchor to",
    highlight=True,  # Adds yellow background
    add_prefix=True  # Adds [Re: '...'] prefix
)
```

**Get approval matrix for LLM prompts:**
```python
from google_docs_tools import get_approval_matrix_prompt

# Markdown format - best for readability, includes tables grouped by category
prompt = get_approval_matrix_prompt(format="markdown")

# Structured format - clear text blocks with rule numbers
prompt = get_approval_matrix_prompt(format="structured")

# Compact format - one-line rules, saves tokens in LLM prompts
prompt = get_approval_matrix_prompt(format="compact")

# Use in system prompt:
system_prompt = f"""You are a contract reviewer. Use these approval rules:

{get_approval_matrix_prompt(format='compact')}

Review the contract and identify which clauses trigger these rules."""
```

**Send escalation emails:**
```python
from google_docs_tools import send_escalation_email

# Send email to approver
result = send_escalation_email(
    to_email="approver@example.com",
    recipient_name="Antti",
    contract_title="Supply Agreement with Acme Corp",
    contract_url="https://docs.google.com/document/d/...",
    violations_summary="1. Payment Terms: Payment terms >60 days\n2. Liquidated Damages: Penalty >5%",
    escalation_level="Head of BU"
)

if result["success"]:
    print(f"Email sent! Message ID: {result['message_id']}")
else:
    print(f"Failed: {result['error']}")
```

**Email Escalation via API:**
```bash
# Using the /send-email endpoint
curl -X POST "http://localhost:8000/send-email" \
  -H "Content-Type: application/json" \
  -d '{
    "to_email": "liamnguyen1208@gmail.com",
    "recipient_name": "Antti",
    "contract_title": "Supply Agreement",
    "contract_url": "https://docs.google.com/document/d/1rHt_qNNnOEdVTS5q4fCMmUxotQNceUNYLjBhs1kqMfE/edit",
    "violations_summary": "1. Payment Terms: Payment terms >60 days",
    "escalation_level": "Head of BU"
  }'
```

**Conversational Email Flow:**
After evaluating a contract with violations, the assistant will prompt:
```
This contract requires CEO approval. Would you like me to send an escalation email to Antti (Head of BU)?

Simply reply: Yes
```

Just reply "Yes" (or "yeah", "sure", "ok", "send it") and the system will automatically send the email using the stored evaluation - no need to re-evaluate!

## Key Implementation Details

**OAuth Scopes Required:**
- `https://www.googleapis.com/auth/documents` - Read and create docs
- `https://www.googleapis.com/auth/drive.file` - Access files created by app
- `https://www.googleapis.com/auth/gmail.send` - Send emails via Gmail

**Document ID Extraction:**
The `extract_document_id()` function accepts both:
- Full URLs: `https://docs.google.com/document/d/{id}/edit`
- Just the ID: `1rHt_qNNnOEdVTS5q4fCMmUxotQNceUNYLjBhs1kqMfE`

**Text Segment Extraction:**
The `_extract_text_from_element()` function recursively walks:
- Paragraphs with text runs
- Tables with nested cells and content
- Preserves exact `startIndex` and `endIndex` from the API

**Approval Matrix Schema:**
Each rule in `contract_approval_matrix.json` has:
- `Category`: Contract clause category
- `Condition`: Threshold that triggers the rule
- `Approval_Matrix`: Dict of roles to involvement level:
  - "Prepares/Initiates" - Creates the proposal
  - "Support required" - Must provide input
  - "Always involved" - Must be in the loop
  - "Approves/Decides" - Final decision maker

## Test Document

The test suite uses a sample contract at:
```
https://docs.google.com/document/d/1rHt_qNNnOEdVTS5q4fCMmUxotQNceUNYLjBhs1kqMfE/edit?tab=t.0
```

This document contains clauses that trigger various approval matrix rules:
- Liquidated damages clauses with high penalty rates
- Payment terms exceeding standard durations
- Liability caps above policy thresholds
