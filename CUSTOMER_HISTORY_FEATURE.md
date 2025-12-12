# Customer History & Intelligent Recommendations Feature

## Overview

The contract evaluator now considers **historical contract data** when analyzing contracts, providing intelligent recommendations on whether to re-negotiate with the customer or escalate directly based on:

1. **Customer acceptance patterns** for deviations
2. **Historical negotiation complexity** (number of rounds)
3. **Current escalation level** required
4. **Previously accepted deviation types**

## How It Works

### 1. Customer History Data

The system reads from `previous-contracts.json`:

```json
[
    {
        "contract_id": 1,
        "purchaser": "Zeus Fiction Oy",
        "contract_closing_date": "3 months ago",
        "accepted_deviations": [],
        "customer_negotiation_rounds": 8
    },
    {
        "contract_id": 4,
        "purchaser": "Metis Fiction Oy",
        "contract_closing_date": "5 months ago",
        "accepted_deviations": [
            {
                "condition": "Total liability cap >100%",
                "negotiated_term": "Total liability cap agreed 500%"
            }
        ],
        "customer_negotiation_rounds": 1
    }
]
```

### 2. Customer Profile Analysis

For each customer, the system calculates:

- **Total contracts**: Number of previous contracts
- **Accepted deviations**: Count and types of deviations customer accepted before
- **Average negotiation rounds**: How many back-and-forth rounds typically required
- **Deviation acceptance rate**: % of contracts where customer accepted deviations

### 3. Recommendation Logic

The LLM provides one of three recommendations:

#### A. **Re-Negotiate** (Customer is difficult)
**Triggers when:**
- High escalation level required (BA President or CEO) **AND**
- Customer has LOW acceptance rate for deviations (< 30%) **AND/OR**
- Customer has HIGH average negotiation rounds (> 4 rounds)

**Example:**
```
💡 My Recommendation

Recommended Action: Re Negotiate

Given the CEO approval required and Zeus Fiction Oy's history of rejecting all
deviations across 3 previous contracts with an average of 6.3 negotiation rounds,
I recommend re-negotiating these terms with the customer before escalating internally.

Key Factors:
- Customer has 0% acceptance rate for policy deviations
- Average of 6.3 negotiation rounds indicates difficult negotiations
- CEO escalation should be reserved for accepted terms to maximize efficiency
```

#### B. **Escalate Directly** (Customer is flexible)
**Triggers when:**
- Customer has HIGH acceptance rate for deviations (> 50%) **AND**
- Customer has LOW average negotiation rounds (< 3 rounds) **AND**
- Similar deviations were accepted before

**Example:**
```
💡 My Recommendation

Recommended Action: Escalate Directly

Despite the CEO approval required, Metis Fiction Oy has previously accepted
similar liability cap deviations (500% in contract #4) with minimal negotiation
(average 1.3 rounds). I recommend escalating directly to CEO for approval to
expedite the process.

Key Factors:
- Customer previously accepted "Total liability cap >100%" deviation
- Low negotiation complexity (1.3 rounds average)
- High acceptance rate (100% of contracts had accepted deviations)
```

#### C. **Cautious Approach** (Mixed patterns)
**Triggers when:**
- Customer history shows mixed patterns
- Not enough data to make clear recommendation

**Example:**
```
💡 My Recommendation

Recommended Action: Cautious Approach

The customer has limited history with mixed acceptance patterns. I recommend
initial informal discussion with the customer to gauge their flexibility on
these specific terms before deciding on formal escalation.

Key Factors:
- Only 1 previous contract in history
- Current violations differ from previously accepted deviations
- Risk assessment needed before full escalation
```

## Implementation Details

### Files Modified

#### 1. **evaluate_contract.py**

Added new functions:
```python
def load_previous_contracts(file_path: str = PREVIOUS_CONTRACTS_FILE) -> List[Dict[str, Any]]
    """Load previous contracts from JSON file"""

def extract_customer_name(contract_text: str) -> Optional[str]
    """Extract customer/purchaser name from contract using regex patterns"""

def get_customer_history(customer_name: str, previous_contracts: List[Dict[str, Any]]) -> Dict[str, Any]
    """Calculate customer statistics: contracts, deviations, negotiation rounds"""
```

Updated methods:
- `analyze_contract()` - Now includes customer history context in LLM prompt
- `analyze_contract_streaming()` - Same historical context for streaming mode

#### 2. **streaming_assistant.py**

Added new section in output after "Highest Approval Level Required":
```python
# Stream recommendations section
if "recommendation" in analysis:
    yield "💡 **My Recommendation**\n\n"
    yield f"**Recommended Action:** {action}\n\n"
    # Stream reasoning in small chunks
    # Stream key factors
```

#### 3. **previous-contracts.json** (Data File)

Structure:
```json
{
    "contract_id": number,
    "purchaser": "Company Name Oy/Ltd/Inc",
    "contract_closing_date": "X months ago",
    "accepted_deviations": [
        {
            "condition": "Exact condition from approval matrix",
            "negotiated_term": "What was actually agreed"
        }
    ],
    "customer_negotiation_rounds": number
}
```

### Customer Name Extraction

The system extracts customer names using regex patterns:
```python
patterns = [
    r'PURCHASER[:\s]+([A-Z][a-zA-Z\s]+(?:Oy|Ltd|Inc|Corp|GmbH|AB))',
    r'Customer[:\s]+([A-Z][a-zA-Z\s]+(?:Oy|Ltd|Inc|Corp|GmbH|AB))',
    r'Buyer[:\s]+([A-Z][a-zA-Z\s]+(?:Oy|Ltd|Inc|Corp|GmbH|AB))',
    r'between[^a-zA-Z]+(?:the\s+)?SUPPLIER[^a-zA-Z]+and[^a-zA-Z]+([A-Z][a-zA-Z\s]+(?:Oy|Ltd|Inc|Corp|GmbH|AB))',
]
```

Supports common company suffixes: Oy, Ltd, Inc, Corp, GmbH, AB

## Example Output Flow

### Complete Evaluation with Recommendations

```
📄 Found Google Docs URL
🔍 Starting contract evaluation...

📖 Reading contract from Google Docs...
🤖 Analyzing with Claude AI (2847 chars)
............
✅ Analysis complete

📊 **Summary**
This is a 5 MEUR contract with Zeus Fiction Oy for supply of equipment...

⚠️ **Contract Terms Deviations from Policies**

Found **3** violation(s) that require escalation.

**Highest Approval Level Required:** CEO

💡 **My Recommendation**

**Recommended Action:** Re Negotiate

Given the CEO approval required and Zeus Fiction Oy's history of rejecting
all deviations across 3 previous contracts with an average of 6.3 negotiation
rounds, I strongly recommend re-negotiating these terms with the customer
before escalating internally. Focus on the liability cap (500%) and liquidated
damages (20%) as primary negotiation points.

**Key Factors:**
- Customer has 0% acceptance rate for policy deviations (0 out of 3 contracts)
- Average of 6.3 negotiation rounds indicates difficult negotiations
- CEO escalation should be reserved for accepted terms to maximize efficiency
- Previous contracts took 5, 6, and 8 rounds respectively

💬 Adding comments and highlights to document...
   ✓ Added comment 1/3
   ✓ Added comment 2/3
   ✓ Added comment 3/3

✅ Completed: 3/3 comments added

🎨 **Color Guide:**
- 🟡 Yellow = Head of BU approval
- 🟠 Orange = BA President approval
- 🔴 Red = CEO approval

📋 **Review the contract:** [Open in Google Docs](...)
```

## Data Requirements

### Adding New Historical Contracts

To add new contract history, update `previous-contracts.json`:

```json
{
    "contract_id": 7,
    "purchaser": "New Customer Ltd",
    "contract_closing_date": "1 month ago",
    "accepted_deviations": [
        {
            "condition": "Payment term longer than 60 days",
            "negotiated_term": "Payment term agreed 90 days"
        }
    ],
    "customer_negotiation_rounds": 3
}
```

**Guidelines:**
1. Use exact customer name as it appears in contracts
2. List accepted deviations using exact approval matrix conditions
3. Record actual negotiation rounds (initial proposal to signature)
4. Keep recent contracts (last 6-12 months most relevant)

### Customer Name Matching

The system performs **case-insensitive matching**:
- "Zeus Fiction Oy" matches "zeus fiction oy" in contract
- "Metis Fiction Oy" matches "METIS FICTION OY"

If customer not found:
- System still performs violation analysis
- Recommendation section shows: "No previous contract history available"
- LLM provides generic recommendation based on escalation level only

## Testing

### Test with Zeus Fiction Oy (Difficult Customer)

Expected recommendation: **Re-Negotiate**

Contract should contain: "PURCHASER: Zeus Fiction Oy"

Historical data shows:
- 3 contracts, 0 accepted deviations
- High negotiation rounds (5, 6, 8)
- 0% acceptance rate

### Test with Metis Fiction Oy (Flexible Customer)

Expected recommendation: **Escalate Directly**

Contract should contain: "PURCHASER: Metis Fiction Oy"

Historical data shows:
- 3 contracts, 5 total accepted deviations
- Low negotiation rounds (1, 1, 2)
- 100% acceptance rate

### Test Script

```bash
cd /Users/liamnguyen/Documents/Projects/ai-driven-contract-approval

# Start server
uvicorn app:app --reload --port 8000

# Test in another terminal
curl -N -X POST "http://localhost:8000/chat/stream" \
  -H "Content-Type: application/json" \
  -d '{"message": "Evaluate: https://docs.google.com/document/d/YOUR_DOC_ID/edit"}'
```

Check output for:
- ✅ Customer name extracted correctly
- ✅ Historical data loaded
- ✅ Recommendation section appears after "Highest Approval Level Required"
- ✅ Recommendation aligns with customer history

## Benefits

1. **Data-Driven Decisions**: Recommendations based on actual historical patterns
2. **Efficiency**: Avoid unnecessary escalations for customers likely to accept
3. **Strategic Approach**: Pre-negotiate with difficult customers to save time
4. **Learning System**: As more contracts are added, recommendations become more accurate
5. **Transparency**: Clear explanation of why each recommendation is made

## Future Enhancements

Potential improvements:
- [ ] Track success rate of recommendations
- [ ] Machine learning model for prediction
- [ ] Industry/sector-specific patterns
- [ ] Seasonal trends in customer behavior
- [ ] Contract value thresholds in recommendations
- [ ] Automatic update of previous-contracts.json after contract closure

## Troubleshooting

### Customer Name Not Extracted

**Symptoms:**
```
Warning: Could not identify customer name from contract
CUSTOMER HISTORY: No previous contract history available
```

**Solutions:**
1. Check contract contains "PURCHASER: Company Name Oy" or similar
2. Ensure company name has valid suffix (Oy, Ltd, Inc, Corp, GmbH, AB)
3. Add custom regex pattern if customer uses non-standard format

### Wrong Customer Matched

**Symptoms:**
- Shows history for different customer
- Recommendation doesn't make sense

**Solutions:**
1. Verify exact customer name spelling in previous-contracts.json
2. Check for multiple companies with similar names
3. Use full legal name including suffix

### No Recommendation Section

**Symptoms:**
- Output shows violations and escalation level
- No "💡 My Recommendation" section

**Solutions:**
1. Check LLM returned `recommendation` field in JSON
2. Verify `previous-contracts.json` is readable
3. Check logs for JSON parsing errors
4. Test with simpler contract first

## Summary

The customer history feature transforms the contract evaluator from a simple policy checker into an **intelligent assistant** that:

✅ Learns from past interactions with each customer
✅ Provides strategic recommendations based on data
✅ Helps prioritize escalations effectively
✅ Reduces unnecessary back-and-forth negotiations
✅ Improves overall contract closing efficiency

The system is now **context-aware** and **proactive**, not just reactive!
