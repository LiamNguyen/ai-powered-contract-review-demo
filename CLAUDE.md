# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is an AI-driven contract approval system that integrates with Google Docs and Google Drive APIs. The system:
- Reads Google Docs contracts
- Analyzes contract terms against approval policies
- Adds visual anchored comments to specific clauses
- Uses an approval matrix to determine required stakeholder sign-offs

## Architecture

### Core Components

**google_docs_tools/** - Python package for Google API integration
- `auth.py`: OAuth2 authentication with token caching
- `tools.py`: High-level API wrappers for reading docs and adding comments
- `__init__.py`: Exports main functions: `read_document`, `add_comment`, `get_document_text`, `find_text_position`, `create_document`, `get_approval_matrix_prompt`

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
2. Enable Google Docs API and Google Drive API
3. Create OAuth 2.0 credentials (Desktop app type)
4. Download `credentials.json` to project root
5. First run opens browser for authentication
6. Token cached in `token.json` for subsequent runs

**Dependencies:**
```bash
pip install -r requirements.txt
# Installs: google-api-python-client, google-auth-httplib2, google-auth-oauthlib
```

## Common Commands

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

## Key Implementation Details

**OAuth Scopes Required:**
- `https://www.googleapis.com/auth/documents` - Read and create docs
- `https://www.googleapis.com/auth/drive.file` - Access files created by app

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
