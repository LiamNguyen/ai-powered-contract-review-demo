# Contract Evaluator - Usage Guide

## Overview

The Contract Evaluator uses Claude Sonnet 4.5 (via AWS Bedrock) to automatically analyze sales contracts against your company's approval policies, add comments to problematic clauses, and provide actionable summaries.

## Prerequisites

1. **Google Cloud Setup** (for reading/modifying Google Docs)
   - Download `credentials.json` to project root
   - First run will authenticate via browser
   - Token cached in `token.json` for future runs

2. **AWS Bedrock Setup** (for Claude AI)
   - Configure AWS credentials (see below)
   - Ensure access to Claude Sonnet 4.5 in us-west-2 region
   - Model: `us.anthropic.claude-sonnet-4-5-20250929-v1:0`

3. **AWS Credentials Configuration**

   Choose one method:

   **Option A: Environment Variables**
   ```bash
   export AWS_ACCESS_KEY_ID=your_access_key
   export AWS_SECRET_ACCESS_KEY=your_secret_key
   export AWS_REGION=us-west-2
   ```

   **Option B: AWS Credentials File**
   ```bash
   # Create/edit ~/.aws/credentials
   [default]
   aws_access_key_id = your_access_key
   aws_secret_access_key = your_secret_key
   region = us-west-2
   ```

   **Option C: IAM Role** (if running on AWS EC2/ECS)
   - Automatically uses instance role

## Running the Evaluator

### 1. Test Analysis Only (Recommended First)

This analyzes the contract without modifying the Google Doc:

```bash
python test_evaluate_contract.py
```

Output includes:
- High-level summary
- Number of violations found
- Highest escalation level required
- Detailed breakdown of each violation

### 2. Full Evaluation (Analysis + Comments + Highlights)

This runs the complete workflow and modifies the Google Doc:

```bash
python evaluate_contract.py
```

This will:
1. Read the contract from Google Docs
2. Analyze it against the approval matrix
3. Add comments to each problematic clause
4. Highlight the problematic text (yellow background)
5. Return an HTML summary

### 3. Use as a Module

```python
from evaluate_contract import ContractEvaluator

# Initialize
evaluator = ContractEvaluator(aws_region="us-west-2")

# Option 1: Full evaluation (analysis + comments)
doc_url = "https://docs.google.com/document/d/YOUR_DOC_ID/edit"
summary_html = evaluator.evaluate(doc_url)
print(summary_html)

# Option 2: Analysis only
analysis = evaluator.analyze_contract(doc_url)
print(f"Found {len(analysis['violations'])} violations")
print(f"Highest escalation: {analysis['highest_escalation']}")
```

## Understanding the Output

### Summary Format

```
{High-level summary from AI - 2 sentences max}

<h2>Contract Terms Deviations from Policies</h2>

<p><strong>X</strong> contract term(s) violate company policies and require escalation.</p>

<p><strong>Highest Approval Level Required:</strong> CEO | BA President | Head of BU</p>

<p>Please visit the <a href="...">Google Docs contract</a> to review the highlighted
clauses and detailed comments.</p>
```

### Escalation Hierarchy

From lowest to highest authority:
1. **Head of BU** (Business Unit) - For moderate deviations
2. **BA President** (Business Area President) - For significant deviations
3. **CEO** (Chief Executive Officer) - For critical/extreme deviations

### Violation Details

Each violation includes:
- **Policy Violated**: Which approval matrix rule was triggered
- **Category**: Contract category (e.g., "LIMITATION OF LIABILITY")
- **Severity**: high | medium | low
- **Escalation Level**: Who must approve (from approval matrix)
- **Clause Text**: Exact text from contract
- **Comment**: AI explanation and recommendation

## How to Verify Comments Were Added

After running the evaluator, you MUST check the Google Doc in a web browser to see the comments:

### Steps to View Comments

1. **Open Document in Browser**
   ```
   https://docs.google.com/document/d/YOUR_DOC_ID/edit
   ```
   ⚠️ Use desktop web browser, not mobile app

2. **Look for Color-Coded Highlighted Text**
   - Flagged clauses have **colored backgrounds** indicating severity:
     - 🟡 **Yellow** = Head of BU approval required
     - 🟠 **Orange** = BA President approval required
     - 🔴 **Red** = CEO approval required
   - Multiple highlights = multiple violations
   - Scroll through document to see all highlights

3. **Open Comments Panel**
   - Click **"Show comments"** icon (top-right corner, speech bubble icon)
   - Or click directly on any highlighted text
   - Comments panel appears on right side

4. **Read Comment Details**
   - **Prefix**: `[Re: 'snippet of text']` - shows what was flagged
   - **Body**: Detailed explanation of the policy violation
   - **Reference**: Which approval matrix rule was triggered
   - **Recommendation**: Who needs to approve

### Important Notes

- ✅ Comments are Google Docs **annotations** (not text edits)
- ✅ Script reports "success" when API accepts comment
- ⚠️ May need to refresh browser to see comments (Cmd+Shift+R / Ctrl+Shift+F5)
- ⚠️ Desktop browser required (mobile app may not show properly)
- ⚠️ Requires edit/comment permission on the document

### Example Comment

```
[Re: 'The invoices are due for payment 120 days...']

Head of BU approval required

Payment terms of 120 days significantly exceed the 60-day threshold
defined in the approval matrix. This creates extended cash flow exposure
for the supplier.
```

Note the format:
1. First line: `[Re: 'quoted text']` - shows what was flagged
2. Second line: `{Role} approval required` - clear escalation requirement
3. Remaining lines: Detailed explanation of the violation

## Approval Matrix Rules

The system checks contracts against these policies:

| Category | Condition | Escalation |
|----------|-----------|------------|
| Liability & Damages | Total liability cap >100% | CEO |
| Liability & Damages | Total liability cap >70% | BA President |
| Liability & Damages | Liquidated damages >15% | BA President |
| Scope of Supply | Payment terms >60 days | Head of BU |

*Full rules in `contract_approval_matrix.json`*

## Customization

### Change the Document URL

Edit `evaluate_contract.py`:
```python
# Line 29
TEST_DOC_URL = "https://docs.google.com/document/d/YOUR_DOC_ID/edit"
```

Later versions will accept this as a parameter.

### Modify Approval Matrix

Edit `contract_approval_matrix.json`:
```json
{
  "Category": "YOUR_CATEGORY",
  "Condition": "YOUR_CONDITION",
  "Approval_Matrix": {
    "Role": "Approves/Decides"
  }
}
```

### Adjust Highlight Color

In your code:
```python
from google_docs_tools import add_comment

add_comment(
    document_id=doc_url,
    comment_text="Your comment",
    quoted_text="text to highlight",
    highlight=True,
    highlight_color={"red": 1.0, "green": 0.8, "blue": 0.8}  # Light red
)
```

## Troubleshooting

### Error: "credentials.json not found"
Download OAuth credentials from Google Cloud Console.

### Error: "AWS credentials not configured"
Set up AWS credentials using one of the methods above.

### Error: "ValidationException: Invocation of model ID..."
Your AWS account may not have access to Claude Sonnet 4.5 in Bedrock.
Contact AWS support to enable model access.

### Error: "Could not find text in document"
The contract text may have changed since analysis. Re-run the analysis.

### Slow Performance
- Normal: 30-60 seconds for analysis + comments
- If slower: Check network connection to AWS and Google APIs

## Next Steps

This script is ready to be integrated into a FastAPI endpoint for frontend chatbot-ui integration (to be implemented later).

Example FastAPI integration:
```python
from fastapi import FastAPI
from evaluate_contract import ContractEvaluator

app = FastAPI()
evaluator = ContractEvaluator()

@app.post("/evaluate")
async def evaluate(document_url: str):
    summary = evaluator.evaluate(document_url)
    return {"summary": summary}
```
