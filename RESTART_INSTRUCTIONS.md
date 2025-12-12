# Complete Restart Instructions

## Issue Fixed
The backend was splitting HTML by words for streaming, which broke the HTML tags.

**Fix:** Changed to yield HTML as a single chunk without splitting.

---

## Critical Restart Steps

### 1. Stop Everything First

**Backend:**
```bash
# Find and kill the backend process
ps aux | grep uvicorn
# Note the PID, then:
kill <PID>
```

**Frontend:**
```bash
# Kill Next.js dev server
pkill -f "next dev"
```

### 2. Clear All Caches

**Frontend Cache:**
```bash
cd /Users/liamnguyen/Documents/Projects/ai-driven-contract-approval/chatbot-ui
rm -rf .next
rm -rf node_modules/.cache
```

**Browser Cache:**
- Open browser DevTools (F12)
- Right-click refresh button → "Empty Cache and Hard Reload"
- OR use Incognito/Private window (recommended!)

### 3. Start Backend

```bash
cd /Users/liamnguyen/Documents/Projects/ai-driven-contract-approval

# Start with explicit reload flag
uvicorn app:app --reload --port 8000 --log-level debug
```

**Wait for:** "Application startup complete"

### 4. Start Frontend

```bash
cd /Users/liamnguyen/Documents/Projects/ai-driven-contract-approval/chatbot-ui

# Start fresh
npm run dev
```

**Wait for:** "compiled successfully"

### 5. Test in Browser

**IMPORTANT: Use Incognito/Private Window** (this guarantees no cache)

1. Open Incognito window
2. Go to: http://localhost:3000/simple-chat
3. Open DevTools Console (F12 → Console tab)
4. Send evaluation request
5. Watch console for: "HTML detected, rendering with dangerouslySetInnerHTML"

---

## What to Look For

### In Console:
```javascript
HTML detected, rendering with dangerouslySetInnerHTML
```

If you see this, the HTML is being detected and rendered!

### In Browser:
```
💡 My Recommendation

Recommended Action: Re Negotiate

Recommend re-negotiating before escalation.

• Zero accepted deviations with this customer (0/3 contracts)
• High negotiation rounds (6.3 avg) shows difficult relationship
• Current violations unlikely to be approved
```

**Bullets should be on separate lines with proper list formatting.**

---

## If Still Not Working

### Check 1: Verify HTML in Response

Open DevTools → Network tab:
1. Send evaluation request
2. Find the `/api/chat/supervisor` request
3. Click it → Preview tab
4. Look for HTML tags in the response

Should see: `<p>...</p><ul><li>...</li></ul>`

### Check 2: Test Regex

In browser console:
```javascript
const test = "<p>Test</p><ul><li>Item</li></ul>"
const hasHTML = /<p>|<ul>|<li>|<div>/i.test(test)
console.log(hasHTML)  // Should be: true
```

### Check 3: Inspect Rendered Element

Right-click on the recommendation text → Inspect Element

**If working:** Should see:
```html
<div class="html-content">
  <p>Recommend re-negotiating...</p>
  <ul>
    <li>Zero accepted deviations...</li>
    <li>High negotiation rounds...</li>
  </ul>
</div>
```

**If not working:** Will see plain text or escaped HTML

---

## Changes Made

### Backend (`streaming_assistant.py:338-341`):
```python
# OLD (BROKEN):
reasoning = recommendation.get("reasoning", "")
words = reasoning.split()  # ❌ This breaks HTML!
for i in range(0, len(words), 3):
    chunk = " ".join(words[i:i+3]) + " "
    yield chunk

# NEW (FIXED):
reasoning = recommendation.get("reasoning", "")
yield reasoning  # ✅ HTML stays intact
yield "\n\n"
```

### Frontend (`chatbot-ui/app/simple-chat/page.tsx:10-13`):
```typescript
// More specific HTML detection
const hasHTML = /<p>|<ul>|<li>|<div>/i.test(content)

if (hasHTML) {
  console.log('HTML detected, rendering with dangerouslySetInnerHTML')
  return <div dangerouslySetInnerHTML={{ __html: content }} className="html-content" />
}
```

---

## Troubleshooting

### "HTML not detected" in console
- Frontend cache issue
- Try Incognito window
- Check HTML tags are actually in the content

### HTML shows as plain text
- React is escaping it
- `dangerouslySetInnerHTML` not being applied
- Check browser console for errors

### Bullets still on one line
- CSS not applied
- Check `.html-content` styles in DevTools

### Old JavaScript still running
- Kill frontend completely: `pkill -f "next dev"`
- Delete `.next`: `rm -rf .next`
- Use Incognito window

---

## Expected Behavior

1. **Backend sends:**
   ```json
   {
     "reasoning": "<p>Recommend re-negotiating before escalation.</p><ul><li>Zero accepted deviations</li><li>High negotiation rounds</li></ul>"
   }
   ```

2. **Frontend detects:** `/<p>|<ul>|<li>|<div>/.test(content)` → true

3. **Frontend renders:** `dangerouslySetInnerHTML={{ __html: content }}`

4. **Browser displays:** Proper HTML with bullets on separate lines

---

## Summary

✅ **Backend:** Fixed word-splitting that broke HTML
✅ **Frontend:** Improved HTML detection regex
✅ **Console log:** Added for debugging
✅ **CSS:** Already in place for styling

**Critical:** Must use Incognito window or completely clear cache!

The fix is solid - the issue is just getting the new code to load in your browser.
