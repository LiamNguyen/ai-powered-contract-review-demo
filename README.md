# AI-Driven Contract Approval System

Automatically review sales contracts against company policies using Claude AI, then add comments and highlights directly to Google Docs.

## What It Does

1. **Reads** contracts from Google Docs
2. **Analyzes** contract terms against your approval matrix using Claude Sonnet 4.5
3. **Highlights** problematic clauses with yellow background
4. **Adds comments** explaining policy violations and required approvals
5. **Returns** HTML summary with escalation recommendations

## Key Features

- ✅ **Strict Policy Adherence**: Only flags violations matching your approval matrix (doesn't use general contract knowledge)
- ✅ **Precise Text Targeting**: Highlights the exact clause with the violation, not paragraph starts
- ✅ **Color-Coded Highlights**: Visual severity indicators
  - 🟡 Yellow = Head of BU approval needed
  - 🟠 Orange = BA President approval needed
  - 🔴 Red = CEO approval needed
- ✅ **Clear Comment Format**: Each comment shows required approval level upfront
- ✅ **Ready for API Integration**: Simple Python class, easy to wrap in FastAPI

## Quick Start

### Option A: Use the FastAPI (Recommended for Frontend Integration)

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Start the API server
uvicorn app:app --reload --port 8000

# 3. Send requests to the API
curl -X POST "http://localhost:8000/chat/stream" \
  -H "Content-Type: application/json" \
  -d '{"message": "Please evaluate: https://docs.google.com/document/d/YOUR_DOC_ID/edit"}' \
  --no-buffer
```

See [API.md](API.md) for complete API documentation.

### Option B: Use as Python Script

```bash
# 1. Install dependencies
pip install -r requirements.txt
```

## Setup

### 1. Configure Google Cloud

1. Create Google Cloud project
2. Enable Google Docs API + Google Drive API
3. Create OAuth 2.0 credentials (Desktop app)
4. Download `credentials.json` to project root

### 2. Configure AWS Bedrock

```bash
# Set AWS credentials
export AWS_ACCESS_KEY_ID=your_key
export AWS_SECRET_ACCESS_KEY=your_secret
export AWS_REGION=us-west-2
```

Ensure your AWS account has access to Claude Sonnet 4.5.

## Usage

### Using the API

```bash
# Start the server
uvicorn app:app --reload --port 8000

# Test with curl
curl -X POST "http://localhost:8000/chat/stream" \
  -H "Content-Type: application/json" \
  -d '{"message": "Evaluate: https://docs.google.com/document/d/YOUR_DOC_ID/edit"}' \
  --no-buffer

# Or use the Python test script
python test_api.py
```

### Using Python Scripts

```bash
# Analyze without modifying document (safe test)
python test_evaluate_contract.py

# Adds comments and highlights to document
python evaluate_contract.py
```

### Verify Results in Google Docs

Open the document in a web browser to see:
- Yellow highlighted text (flagged clauses)
- Comments with detailed explanations
- Approval recommendations

## Documentation

- **[USAGE.md](USAGE.md)** - Complete usage guide with examples
- **[TESTING.md](TESTING.md)** - Test scripts and verification steps
- **[CLAUDE.md](CLAUDE.md)** - Technical architecture and implementation details

## Project Structure

```
├── evaluate_contract.py           # Main application
├── google_docs_tools/             # Google API integration
│   ├── auth.py                    # OAuth authentication
│   ├── tools.py                   # Doc reading + comment adding
│   └── __init__.py
├── contract_approval_matrix.json  # Policy rules
├── test_evaluate_contract.py      # Safe analysis test
├── test_single_comment.py         # Single comment test
└── requirements.txt               # Python dependencies
```

## How It Works

### Approval Matrix

Define your policies in `contract_approval_matrix.json`:

```json
{
  "Category": "LIMITATION OF LIABILITY & LIQUIDATED DAMAGES",
  "Condition": "Total liability cap >100%",
  "Approval_Matrix": {
    "Legal": "Prepares/Initiates",
    "Sales": "Prepares/Initiates",
    "CEO": "Approves/Decides"
  }
}
```

### LLM Analysis

Claude analyzes the contract and **only** flags violations matching your matrix:

```
Found 3 violations:
1. Payment term longer than 60 days → Head of BU
2. Liquidated damages >15% → BA President
3. Total liability cap >100% → CEO

Highest escalation: CEO
```

### Comment Addition

For each violation:
1. Finds exact text in document
2. Highlights with yellow background (Docs API)
3. Adds comment with explanation (Drive API)
4. Falls back to substring search if exact match fails

## Example Usage

### Python API

```python
from evaluate_contract import ContractEvaluator

evaluator = ContractEvaluator()

# Full workflow
summary = evaluator.evaluate(document_url)
print(summary)  # HTML summary

# Analysis only
analysis = evaluator.analyze_contract(document_url)
print(f"Violations: {len(analysis['violations'])}")
print(f"Escalation: {analysis['highest_escalation']}")
```

### Command Line

```bash
# Analyze only (no document modification)
python test_evaluate_contract.py

# Add single comment (minimal test)
python test_single_comment.py

# Full evaluation (adds all comments)
python evaluate_contract.py
```

## Current Status

✅ **Implemented Features:**
- ✅ Contract reading from Google Docs
- ✅ LLM analysis via AWS Bedrock (Claude Sonnet 4.5)
- ✅ Strict approval matrix enforcement
- ✅ Color-coded highlights (Yellow/Orange/Red)
- ✅ Comment and highlight addition
- ✅ HTML summary generation
- ✅ **FastAPI with streaming endpoint**
- ✅ **Automatic URL extraction from user messages**
- ✅ **Real-time progress streaming**

📋 **Future Enhancements:**
- Batch processing multiple documents
- Historical tracking of reviews
- Authentication/API keys
- Rate limiting
- Websocket support

## Requirements

- Python 3.8+
- Google Cloud project with Docs + Drive APIs
- AWS account with Bedrock access (Claude Sonnet 4.5)
- Google Docs with edit permissions

## Troubleshooting

### Comments not visible?
- Use desktop web browser (not mobile)
- Hard refresh: Cmd+Shift+R (Mac) or Ctrl+Shift+F5 (Windows)
- Click "Show comments" button in Google Docs

### AWS Bedrock errors?
- Check credentials: `aws sts get-caller-identity`
- Verify model access in AWS Console
- Ensure region is `us-west-2`

See [TESTING.md](TESTING.md) for detailed troubleshooting.

## API Integration

The FastAPI endpoint is ready for frontend integration. See [API.md](API.md) for:
- Complete API documentation
- Usage examples in Python, JavaScript, and curl
- Deployment guides
- Frontend integration patterns

## License

[Your License Here]

## Support

For issues or questions, see the documentation files or create an issue in the repository.
