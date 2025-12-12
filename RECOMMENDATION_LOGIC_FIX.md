# Recommendation Logic Fix - Clarification on "Accepted Deviations"

## Issue Identified

The LLM was confused about who accepts the deviations, leading to incorrect recommendations.

### Original Misunderstanding:
```
"Accepted deviations" = Customer accepted OUR proposed changes
```

### Correct Understanding:
```
"Accepted deviations" = WE (supplier) accepted CUSTOMER's non-standard terms that deviate from our policies
```

## The Confusion

**Example - Zeus Fiction Oy:**
- Historical data: 0 accepted deviations
- **Wrong interpretation**: "Customer never accepts changes, so let's re-negotiate"
- **Correct interpretation**: "We never accepted their deviations, so we're unlikely to accept now"

## Corrected Logic

### **Scenario 1: Zeus Fiction Oy (0 Accepted Deviations)**

**History:**
- 3 previous contracts
- 0 accepted deviations (we rejected all their non-standard terms)
- 6.3 avg negotiation rounds (difficult negotiations)

**What this means:**
- ✅ We have been **STRICT** with this customer
- ✅ We historically **DO NOT accept** their deviating terms
- ✅ Current violations are **UNLIKELY to be approved** even with escalation

**Recommendation: RE-NEGOTIATE**
> "Since we historically have NOT been flexible with Zeus Fiction Oy (0 accepted deviations across 3 contracts), these violations are UNLIKELY to be approved even with CEO escalation. Better to re-negotiate with the customer first to reduce/eliminate the violations before wasting executive time on an escalation that will likely be rejected."

### **Scenario 2: Metis Fiction Oy (5 Accepted Deviations)**

**History:**
- 3 previous contracts
- 5 accepted deviations (we accepted their non-standard terms)
- 1.3 avg negotiation rounds (smooth negotiations)

**What this means:**
- ✅ We have been **FLEXIBLE** with this customer
- ✅ We historically **DO accept** their deviating terms
- ✅ Current violations are **LIKELY to be approved** through escalation

**Recommendation: ESCALATE DIRECTLY**
> "Since we have historically been flexible with Metis Fiction Oy (5 accepted deviations including similar liability caps), these violations are LIKELY to be approved through CEO escalation. Skip re-negotiation and escalate directly to save time."

## Updated Prompt Sections

### Key Clarification Added:

```
IMPORTANT CLARIFICATION ON "ACCEPTED DEVIATIONS":
- "Accepted deviations" means WE (the supplier) accepted the customer's non-standard terms that deviate from OUR policies
- This is NOT about whether the customer accepted our proposed changes
- High accepted deviations = We have been FLEXIBLE with this customer in the past
- Low/zero accepted deviations = We have been STRICT with this customer in the past
```

### Updated Guidelines:

**1. RE-NEGOTIATE (for strict relationships):**
```
RECOMMEND RE-NEGOTIATION if:
- High escalation level required (BA President or CEO) AND
- WE have LOW/ZERO history of accepting this customer's deviations (< 30% or 0 deviations) AND/OR
- Customer has HIGH average negotiation rounds (> 4 rounds)

REASONING: Since we historically have NOT been flexible with this customer, these violations are UNLIKELY to be approved even with escalation. Better to re-negotiate with customer first to reduce/eliminate the violations before wasting executive time on escalation that will likely be rejected.
```

**2. ESCALATE DIRECTLY (for flexible relationships):**
```
RECOMMEND DIRECT ESCALATION if:
- WE have HIGH history of accepting this customer's deviations (> 50% or multiple accepted) AND
- Customer has LOW average negotiation rounds (< 3 rounds) AND
- Similar deviation types were accepted before

REASONING: Since we have historically been flexible with this customer and accepted their deviations, these violations are LIKELY to be approved through escalation. Skip re-negotiation and escalate directly to save time.
```

## Expected Output Changes

### Before (Incorrect):
```
💡 My Recommendation

Recommended Action: Re Negotiate

The customer has ZERO accepted deviations across 3 previous contracts, indicating
they are extremely difficult to negotiate with and unlikely to accept any deviations...
```
❌ Wrong focus - talking about customer accepting changes

### After (Correct):
```
💡 My Recommendation

Recommended Action: Re Negotiate

Our company has ZERO accepted deviations for Zeus Fiction Oy across 3 previous
contracts (0% acceptance rate), indicating we have historically been very strict
with this customer and rejected all their non-standard terms. Given this pattern,
these current violations (500% liability cap, 20% liquidated damages, 120-day
payment) are UNLIKELY to be approved even with CEO escalation. The 6.3 average
negotiation rounds show this is a difficult customer relationship.

I recommend re-negotiating with Zeus Fiction Oy first to reduce or eliminate these
violations before escalating to CEO level, as our historical stance suggests
internal approval will be denied, wasting executive time.

Key Factors:
- 0% supplier acceptance rate for this customer's deviations (0 out of 3 contracts)
- High negotiation complexity (6.3 rounds average)
- Current violations are severe and unprecedented for this customer
- CEO escalation should be reserved for terms we're actually willing to accept
```
✅ Correct focus - talking about OUR acceptance patterns

## Files Modified

1. **streaming_assistant.py** - Lines 162-185
   - Added clarification section
   - Updated recommendation guidelines with explicit "WE" language

2. **evaluate_contract.py** - Both `analyze_contract()` and `analyze_contract_streaming()` methods
   - Same clarifications added to maintain consistency

## Testing

### Test with Zeus Fiction Oy (Should recommend re-negotiate):

**Command:**
```bash
# Restart server first
uvicorn app:app --reload --port 8000

# Then test
curl -N -X POST "http://localhost:8000/chat/stream" \
  -H "Content-Type: application/json" \
  -d '{"message": "Evaluate: https://docs.google.com/document/d/1rHt_qNNnOEdVTS5q4fCMmUxotQNceUNYLjBhs1kqMfE/edit"}'
```

**Expected:**
- ✅ Shows: "👤 Customer: Zeus Fiction Oy"
- ✅ Shows: "📊 3 previous contracts, 0 accepted deviations"
- ✅ Recommendation: "Re Negotiate"
- ✅ Reasoning focuses on: "WE have not been flexible" and "unlikely to be approved internally"

### Test with Metis Fiction Oy (Should recommend escalate):

**Expected:**
- ✅ Shows: "👤 Customer: Metis Fiction Oy"
- ✅ Shows: "📊 3 previous contracts, 5 accepted deviations"
- ✅ Recommendation: "Escalate Directly"
- ✅ Reasoning focuses on: "WE have been flexible" and "likely to be approved internally"

## Key Takeaway

The recommendation logic is now correctly focused on **OUR internal approval likelihood** based on **OUR historical flexibility** with each customer, not on the customer's willingness to accept changes.

This makes the recommendations strategically valuable:
- **Strict history** → Don't waste time on internal escalation → Re-negotiate first
- **Flexible history** → Internal approval likely → Escalate directly to save time
