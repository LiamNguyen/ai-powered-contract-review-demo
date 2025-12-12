# FastAPI Implementation - Complete Guide

## Overview

The FastAPI implementation provides a production-ready REST API with streaming support for contract evaluation. Users send natural language messages containing Google Docs URLs, and the system automatically evaluates the contracts.

## Key Features

✅ **Streaming Responses**: Real-time progress updates during evaluation
✅ **Automatic URL Extraction**: Parses Google Docs URLs from natural language messages
✅ **No URL Parameter Required**: Users don't need to know the API structure
✅ **CORS Enabled**: Ready for frontend integration
✅ **Error Handling**: Graceful error messages and fallbacks

## Architecture

```
User Message → FastAPI → StreamingAssistant → ContractEvaluator
                               ↓
                        Extract URL (regex)
                               ↓
                        Claude AI Analysis
                               ↓
                        Add Comments/Highlights
                               ↓
                        Stream Results → User
```

## Files Created

### 1. **app.py** - FastAPI Application

Main application file with endpoints:
- `GET /` - Root/health check
- `GET /health` - Health check endpoint
- `POST /chat` - Non-streaming chat endpoint
- `POST /chat/stream` - **Streaming chat endpoint** (primary)

Features:
- CORS middleware for frontend integration
- Request/response models with Pydantic
- Error handling with HTTP exceptions
- Swagger UI documentation at `/docs`

### 2. **streaming_assistant.py** - Streaming Assistant

Core logic for processing chat messages:
- `extract_google_docs_url()` - Extracts URLs using regex patterns
- `stream_agent()` - Main streaming workflow
- `invoke_streaming_claude()` - Helper for Claude streaming (unused currently)

Workflow:
1. Extract Google Docs URL from user message
2. Validate URL exists
3. Call ContractEvaluator
4. Stream progress updates
5. Add comments to document
6. Return formatted summary

### 3. **test_api.py** - Comprehensive Test Suite

Automated tests for:
- Health endpoint
- No URL handling
- Non-streaming endpoint
- Streaming endpoint

Run with: `python test_api.py`

### 4. **test_api_curl.sh** - Curl Test Script

Bash script with curl commands for manual testing.

Run with: `./test_api_curl.sh`

### 5. **API.md** - Complete Documentation

Full API documentation including:
- All endpoints
- Request/response formats
- Usage examples (Python, JavaScript, curl)
- Deployment guides
- Troubleshooting

## URL Extraction Logic

The system extracts Google Docs URLs from messages using regex patterns:

```python
patterns = [
    r'https://docs\.google\.com/document/d/([a-zA-Z0-9-_]+)',
    r'docs\.google\.com/document/d/([a-zA-Z0-9-_]+)',
]
```

**Supported formats:**
- ✅ `https://docs.google.com/document/d/ABC123/edit`
- ✅ `docs.google.com/document/d/ABC123`
- ✅ Embedded in natural language: "Please evaluate https://docs.google.com/..."

**Not supported:**
- ❌ Shortened URLs
- ❌ URLs without document ID
- ❌ Other Google services (Sheets, Slides, etc.)

## Streaming Response Format

The streaming endpoint returns text chunks with emojis for visual clarity:

```
📄 Found Google Docs URL
🔍 Starting contract evaluation...

Reading contract from Google Docs...
✅ Analysis complete

📊 **Summary**
{AI-generated summary}

⚠️ **Contract Terms Deviations from Policies**

Found **3** violation(s) that require escalation.

**Highest Approval Level Required:** CEO

💬 Adding comments and highlights to document...
✅ Added 3/3 comments

🎨 **Color Guide:**
- 🟡 Yellow = Head of BU approval
- 🟠 Orange = BA President approval
- 🔴 Red = CEO approval

📋 **Review the contract:** [Open in Google Docs](...)

The violations have been highlighted...
```

## Example Usage

### Python Client

```python
import requests

url = "http://localhost:8000/chat/stream"
payload = {
    "message": "Please evaluate: https://docs.google.com/document/d/..."
}

response = requests.post(url, json=payload, stream=True)

for chunk in response.iter_content(chunk_size=None, decode_unicode=True):
    if chunk:
        print(chunk, end='', flush=True)
```

### JavaScript/React Frontend

```javascript
async function evaluateContract(message) {
  const response = await fetch('http://localhost:8000/chat/stream', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ message })
  });

  const reader = response.body.getReader();
  const decoder = new TextDecoder();

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;

    const chunk = decoder.decode(value);
    // Update UI with chunk
    updateChatUI(chunk);
  }
}

// Usage
evaluateContract("Evaluate: https://docs.google.com/document/d/...");
```

### Curl

```bash
curl -X POST "http://localhost:8000/chat/stream" \
  -H "Content-Type: application/json" \
  -d '{"message": "Evaluate: https://docs.google.com/document/d/ABC123/edit"}' \
  --no-buffer
```

## Testing

### Automated Tests

```bash
# Run full test suite (requires API running)
python test_api.py
```

Test coverage:
- ✅ Health endpoint
- ✅ URL extraction from messages
- ✅ No URL handling
- ✅ Non-streaming response
- ✅ Streaming response

### Manual Testing

```bash
# Terminal 1: Start server
uvicorn app:app --reload --port 8000

# Terminal 2: Run tests
python test_api.py

# Or use curl
./test_api_curl.sh
```

### Swagger UI

Open http://localhost:8000/docs to:
- View all endpoints
- Test endpoints interactively
- See request/response schemas
- Try different payloads

## Error Handling

### No URL in Message

```
Input: "Hello, can you help me?"

Output:
I couldn't find a Google Docs URL in your message.
Please provide a Google Docs contract URL to evaluate.

Example: Please evaluate this contract: https://docs.google.com/document/d/YOUR_DOC_ID/edit
```

### Evaluation Errors

```
❌ Error during evaluation: {error message}
Please check:
- The Google Docs URL is correct and accessible
- You have edit/comment permissions on the document
- AWS Bedrock credentials are configured
```

### HTTP Errors

Returns proper HTTP status codes:
- `200 OK` - Success
- `500 Internal Server Error` - Evaluation failed

## Configuration

### Environment Variables

```bash
# AWS Configuration
export AWS_REGION=us-west-2
export AWS_ACCESS_KEY_ID=your_key
export AWS_SECRET_ACCESS_KEY=your_secret

# Server Configuration
export PORT=8000
export HOST=0.0.0.0
export WORKERS=4
```

### CORS Settings

Edit `app.py` to restrict origins:

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://your-frontend.com",
        "http://localhost:3000"  # For development
    ],
    allow_credentials=True,
    allow_methods=["POST", "GET"],
    allow_headers=["Content-Type"],
)
```

## Deployment

### Development

```bash
uvicorn app:app --reload --port 8000
```

### Production (Simple)

```bash
uvicorn app:app --host 0.0.0.0 --port 8000 --workers 4
```

### Production (Docker)

```dockerfile
FROM python:3.12-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]
```

Build and run:
```bash
docker build -t contract-api .
docker run -p 8000:8000 \
  -e AWS_ACCESS_KEY_ID=... \
  -e AWS_SECRET_ACCESS_KEY=... \
  -v $(pwd)/credentials.json:/app/credentials.json \
  -v $(pwd)/token.json:/app/token.json \
  contract-api
```

### Production (with Gunicorn)

```bash
pip install gunicorn

gunicorn app:app \
  --workers 4 \
  --worker-class uvicorn.workers.UvicornWorker \
  --bind 0.0.0.0:8000 \
  --timeout 120 \
  --access-logfile - \
  --error-logfile -
```

## Performance

- **Request parsing**: <100ms
- **URL extraction**: <1ms
- **Contract analysis**: 10-30 seconds
- **Comment addition**: 1-3 seconds per violation
- **Total time**: 30-60 seconds

Streaming ensures users see progress immediately.

## Security Considerations

### Before Production

1. **Add Authentication**:
   ```python
   from fastapi.security import HTTPBearer

   security = HTTPBearer()

   @app.post("/chat/stream")
   async def chat_stream(request: ChatInput, token: str = Depends(security)):
       # Verify token
       pass
   ```

2. **Rate Limiting**:
   ```python
   from slowapi import Limiter
   from slowapi.util import get_remote_address

   limiter = Limiter(key_func=get_remote_address)

   @app.post("/chat/stream")
   @limiter.limit("5/minute")
   async def chat_stream(request: Request, ...):
       pass
   ```

3. **Input Validation**:
   - Validate URL format before processing
   - Limit message length
   - Sanitize user input

4. **CORS Restrictions**:
   - Set specific allowed origins
   - Don't use `allow_origins=["*"]` in production

5. **Logging**:
   ```python
   import logging

   logging.basicConfig(
       level=logging.INFO,
       format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
   )
   ```

## Troubleshooting

### API won't start
- Port already in use: `lsof -i :8000` and kill the process
- Missing dependencies: `pip install -r requirements.txt`

### Streaming not working
- Check client supports streaming
- Use `--no-buffer` with curl
- Verify network/firewall settings

### URL not extracted
- Check message contains valid Google Docs URL
- URL must include document ID
- Test with: `https://docs.google.com/document/d/1rHt...`

### Slow responses
- Normal for 30-60 seconds
- Check AWS Bedrock connectivity
- Verify Google API credentials

## Integration Examples

### React Frontend

```typescript
// contractService.ts
export async function streamContractEvaluation(
  message: string,
  onChunk: (chunk: string) => void
): Promise<void> {
  const response = await fetch('http://localhost:8000/chat/stream', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ message })
  });

  const reader = response.body!.getReader();
  const decoder = new TextDecoder();

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;
    onChunk(decoder.decode(value));
  }
}

// Usage in component
function ChatInterface() {
  const [response, setResponse] = useState('');

  const handleEvaluate = async (url: string) => {
    setResponse('');
    await streamContractEvaluation(
      `Evaluate: ${url}`,
      (chunk) => setResponse(prev => prev + chunk)
    );
  };

  return <div>{response}</div>;
}
```

### Node.js Backend

```javascript
const axios = require('axios');

async function evaluateContract(docUrl) {
  const response = await axios({
    method: 'post',
    url: 'http://localhost:8000/chat/stream',
    data: { message: `Evaluate: ${docUrl}` },
    responseType: 'stream'
  });

  response.data.on('data', (chunk) => {
    console.log(chunk.toString());
  });
}
```

## Next Steps

- [ ] Add authentication
- [ ] Implement rate limiting
- [ ] Add request logging
- [ ] Create frontend chat UI
- [ ] Add websocket support for better streaming
- [ ] Implement caching for repeated evaluations
- [ ] Add batch evaluation endpoint
- [ ] Create admin dashboard

## Resources

- [API.md](API.md) - Complete API documentation
- [README.md](README.md) - Project overview
- [TESTING.md](TESTING.md) - Testing guide
- [CLAUDE.md](CLAUDE.md) - Technical architecture
