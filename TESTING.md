# Testing Guide

## Test Results Summary

### ✅ Issue #1 Fixed: LLM Now Strictly Follows Approval Matrix

**Problem**: LLM was using built-in knowledge to flag issues beyond the approval matrix.

**Solution**: Updated system prompt with explicit instructions to ONLY flag violations matching the approval matrix.

**Results**:
- Before: 8 violations (including issues not in matrix)
- After: 3 violations (only those matching approval matrix exactly)

The 3 violations found:
1. Payment term longer than 60 days → Head of BU
2. Liquidated damages/penalties for delay >15% → BA President
3. Total liability cap >100% → CEO

### ✅ Issue #2 Fixed: Comments and Highlights Working

**Problem**: User reported not seeing comments/highlights in Google Docs.

**Solution**:
- Improved error handling and debugging output
- Added fallback for text not found (tries shorter substring)
- Verified comment functionality works correctly

**Test Results**:
```
Test: Adding single comment
✓ Text found at index: 745
✓ Comment ID created: AAABugyTqlA
✓ Text highlighted: True
✓ Status: SUCCESS
```

**Important**: Comments appear in Google Docs but may not be immediately visible. Check:
1. Open the document in a web browser (not mobile app)
2. Look for yellow highlighted text
3. Click on highlighted text to see the comment
4. Check the comments panel (right side of document)

## Available Test Scripts

### 1. Test Analysis Only (No Modification)
```bash
python test_evaluate_contract.py
```
- Analyzes contract with Claude
- Shows violations found
- Does NOT modify the document
- Safe to run anytime

### 2. Test Single Comment (Minimal Modification)
```bash
python test_single_comment.py
```
- Adds ONE test comment to verify functionality
- Highlights one piece of text
- Useful for debugging

### 3. Test Full Workflow (Complete Modification)
```bash
python test_with_comments.py
```
- Requires manual confirmation
- Adds ALL comments for violations found
- Highlights all problematic text
- Production-like test

### 4. Run Main Application
```bash
python evaluate_contract.py
```
- Full production workflow
- Analyzes + comments + summary
- Use this for real contract reviews

## Verification Steps

After running a test that adds comments:

1. **Open Google Docs in Browser**
   ```
   https://docs.google.com/document/d/YOUR_DOC_ID/edit
   ```

2. **Look for Highlights**
   - Yellow highlighted text indicates flagged clauses
   - Multiple highlights = multiple violations

3. **Open Comments Panel**
   - Click "Show comments" button (top right)
   - Or click on any highlighted text

4. **Verify Comment Content**
   - Each comment starts with `[Re: '...']` prefix
   - Comment body explains the violation
   - References the approval matrix rule

5. **Check Comment Metadata**
   - Comment author should be your Google account
   - Timestamp shows when comment was added

## Troubleshooting

### Comments Not Visible

**Symptom**: Script reports success but no comments in doc.

**Possible Causes**:
1. Browser cache - hard refresh (Cmd+Shift+R / Ctrl+Shift+F5)
2. Using mobile app - try desktop browser
3. Document permissions - ensure you have edit access
4. Comments panel hidden - click "Show comments" button

**Solution**:
```bash
# Re-run single comment test
python test_single_comment.py

# Check the comment ID in output
# Search for that ID in Google Docs comments
```

### Text Not Found

**Symptom**: Output shows "WARNING: Could not find text in document"

**Possible Causes**:
1. LLM returned paraphrased text instead of exact quote
2. Document was edited since analysis
3. Text contains special characters/formatting

**Solution**: The script now has fallback logic:
- Tries exact text first
- If not found, tries shorter substring (first 100 chars)
- Reports which method worked

### AWS/Google Auth Errors

See main documentation for setup instructions.

## Expected Output Examples

### Successful Comment Addition
```
[1/3] Processing: Payment term longer than 60 days
     Searching for text (length: 74 chars)
     Preview: The invoices are due for payment 120 days net from the date of invoice...
     Adding comment and highlighting text at index 745...
     ✓ Comment added successfully (ID: AAABugyTqlA)
     ✓ Text highlighted: True
```

### Text Not Found (with Fallback)
```
[2/3] Processing: Liquidated damages >15%
     Searching for text (length: 250 chars)
     Preview: If the equipment included in the DELIVERY are not ready for shipment...
     ✗ WARNING: Could not find exact text in document
     Trying to find a shorter substring...
     ✓ Found using shorter text
     Adding comment and highlighting text at index 1234...
     ✓ Comment added successfully (ID: AAABugyTqlB)
     ✓ Text highlighted: True
```

### Complete Failure
```
[3/3] Processing: Some policy
     Searching for text (length: 150 chars)
     Preview: This is some text that doesn't exist...
     ✗ WARNING: Could not find exact text in document
     Trying to find a shorter substring...
     ✗ Still not found. Skipping this violation.
```

## Performance

Typical timing:
- Reading document: 1-2 seconds
- Claude analysis: 10-30 seconds
- Adding comments (per violation): 1-3 seconds

Total for 3 violations: ~30-45 seconds

## Document State

The test document after successful run will have:
- 3 yellow highlighted sections
- 3 comments (one per violation)
- No changes to actual text content
- All modifications are annotations only
