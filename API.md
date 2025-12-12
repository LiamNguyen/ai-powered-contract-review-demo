# FastAPI Contract Evaluation API

## Overview

The FastAPI application provides a RESTful API with streaming support for contract evaluation. Users send messages containing Google Docs URLs, and the API evaluates the contracts against the approval matrix.

## Features

- ✅ **Streaming Responses**: Real-time progress updates during evaluation
- ✅ **Automatic URL Extraction**: Extracts Google Docs URLs from natural language messages
- ✅ **Color-Coded Highlights**: Adds yellow/orange/red highlights based on escalation
- ✅ **Detailed Comments**: Adds comments with approval requirements
- ✅ **CORS Enabled**: Ready for frontend integration

## Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Start the Server

```bash
# Development mode (with auto-reload)
uvicorn app:app --reload --port 8000

# Production mode
uvicorn app:app --host 0.0.0.0 --port 8000 --workers 4
```

### 3. Test the API

```bash
# Using Python test script
python test_api.py

# Using curl
./test_api_curl.sh
```

## API Endpoints

### Health Check

```http
GET /health
```

**Response:**
```json
{
  "status": "healthy",
  "version": "1.0.0"
}
```

### Chat (Non-Streaming)

```http
POST /chat
Content-Type: application/json

{
  "message": "Please evaluate this contract: https://docs.google.com/document/d/YOUR_DOC_ID/edit"
}
```

**Response:**
```json
{
  "response": "📄 Found Google Docs URL\n🔍 Starting contract evaluation...\n\n..."
}
```

### Chat Stream (Streaming)

```http
POST /chat/stream
Content-Type: application/json

{
  "message": "Please evaluate this contract: https://docs.google.com/document/d/YOUR_DOC_ID/edit"
}
```

**Response:** Text stream with real-time updates

```
📄 Found Google Docs URL
🔍 Starting contract evaluation...

Reading contract from Google Docs...
✅ Analysis complete

📊 **Summary**
This is a 5 MEUR contract...

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
```

## Usage Examples

### Python

```python
import requests

# Streaming request
response = requests.post(
    "http://localhost:8000/chat/stream",
    json={
        "message": "Please evaluate this contract: https://docs.google.com/document/d/..."
    },
    stream=True
)

for chunk in response.iter_content(chunk_size=None, decode_unicode=True):
    if chunk:
        print(chunk, end='', flush=True)
```

### JavaScript (Fetch API)

```javascript
const response = await fetch('http://localhost:8000/chat/stream', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
  },
  body: JSON.stringify({
    message: 'Please evaluate this contract: https://docs.google.com/document/d/...'
  })
});

const reader = response.body.getReader();
const decoder = new TextDecoder();

while (true) {
  const { done, value } = await reader.read();
  if (done) break;

  const chunk = decoder.decode(value);
  console.log(chunk);
}
```

### cURL

```bash
# Streaming endpoint
curl -X POST "http://localhost:8000/chat/stream" \
  -H "Content-Type: application/json" \
  -d '{"message": "Please evaluate: https://docs.google.com/document/d/YOUR_DOC_ID/edit"}' \
  --no-buffer

# Non-streaming endpoint
curl -X POST "http://localhost:8000/chat" \
  -H "Content-Type: application/json" \
  -d '{"message": "Please evaluate: https://docs.google.com/document/d/YOUR_DOC_ID/edit"}'
```

## Message Format

The API accepts natural language messages. The URL can be anywhere in the message:

✅ **Valid messages:**
- `"Please evaluate this contract: https://docs.google.com/document/d/..."`
- `"Can you review https://docs.google.com/document/d/... for me?"`
- `"https://docs.google.com/document/d/..."`
- `"Analyze contract at docs.google.com/document/d/..."`

❌ **Invalid messages:**
- `"Hello"` (no URL)
- `"Review my contract"` (no URL)

## Response Format

### Streaming Response Structure

1. **URL Detection**: `📄 Found Google Docs URL`
2. **Progress Updates**: Real-time evaluation steps
3. **Summary**: AI-generated overview
4. **Violations Count**: Number of policy violations found
5. **Escalation Level**: Highest approval needed
6. **Comment Status**: Progress of adding comments
7. **Color Guide**: Legend for highlights
8. **Document Link**: Link to annotated document

### Error Handling

If no URL is found:
```
I couldn't find a Google Docs URL in your message.
Please provide a Google Docs contract URL to evaluate.

Example: Please evaluate this contract: https://docs.google.com/document/d/YOUR_DOC_ID/edit
```

If evaluation fails:
```
❌ Error during evaluation: {error message}
Please check:
- The Google Docs URL is correct and accessible
- You have edit/comment permissions on the document
- AWS Bedrock credentials are configured
```

## Configuration

### Environment Variables

```bash
# AWS Region for Bedrock
export AWS_REGION=us-west-2

# AWS Credentials (if not using instance role)
export AWS_ACCESS_KEY_ID=your_key
export AWS_SECRET_ACCESS_KEY=your_secret
```

### CORS Settings

Edit `app.py` to configure CORS for your frontend:

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://your-frontend.com"],  # Specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

## Architecture

```
User Message → FastAPI Endpoint → StreamingAssistant
                                          ↓
                                   Extract URL
                                          ↓
                                   ContractEvaluator
                                          ↓
                                   Claude AI Analysis
                                          ↓
                                   Add Comments/Highlights
                                          ↓
                                   Stream Results → User
```

### Components

1. **app.py**: FastAPI application with endpoints
2. **streaming_assistant.py**: Handles message processing and streaming
3. **evaluate_contract.py**: Core contract evaluation logic
4. **google_docs_tools/**: Google Docs/Drive API integration

## Deployment

### Development

```bash
uvicorn app:app --reload --port 8000
```

### Production (Docker)

```dockerfile
FROM python:3.12-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]
```

### Production (systemd service)

```ini
[Unit]
Description=Contract Evaluation API
After=network.target

[Service]
Type=simple
User=your-user
WorkingDirectory=/path/to/app
Environment="AWS_REGION=us-west-2"
ExecStart=/usr/local/bin/uvicorn app:app --host 0.0.0.0 --port 8000 --workers 4
Restart=always

[Install]
WantedBy=multi-user.target
```

## Testing

### Automated Tests

```bash
# Run full test suite
python test_api.py

# Run curl tests
./test_api_curl.sh
```

### Manual Testing

1. Start the server: `uvicorn app:app --reload`
2. Open http://localhost:8000/docs (Swagger UI)
3. Try the `/chat/stream` endpoint with a test message

## Performance

- **Analysis time**: 10-30 seconds (depends on contract length)
- **Comment addition**: 1-3 seconds per violation
- **Total time**: 30-60 seconds for typical contract with 3-5 violations

## Monitoring

### Logs

The API logs to stdout. In production, configure log aggregation:

```python
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
```

### Health Checks

Use `/health` endpoint for monitoring:

```bash
# Check if API is responsive
curl http://localhost:8000/health
```

## Troubleshooting

### API won't start
- Check port 8000 is not in use: `lsof -i :8000`
- Verify dependencies installed: `pip list | grep fastapi`

### Streaming not working
- Ensure client supports streaming responses
- Check firewall/proxy settings
- Use `--no-buffer` with curl

### Comments not appearing
- Verify Google OAuth credentials
- Check document permissions
- Ensure token.json is valid

## Next Steps

- [ ] Add authentication/API keys
- [ ] Implement rate limiting
- [ ] Add request logging
- [ ] Create frontend integration guide
- [ ] Add websocket support
- [ ] Implement caching for repeated evaluations
