# API Documentation

Complete API reference for LangGraph Translation Service.

## Base URL

```
http://localhost:8000/api
```

## Authentication

Currently, no authentication is required for API access. In production, consider implementing API key authentication.

## Common Response Codes

- `200 OK` - Request successful
- `400 Bad Request` - Invalid request parameters
- `422 Unprocessable Entity` - Validation error
- `500 Internal Server Error` - Server error

---

## Endpoints

### 1. Health Check

Check if the service is running.

**Endpoint:** `GET /api/health`

**Request:**
```bash
curl http://localhost:8000/api/health
```

**Response:**
```json
{
  "status": "healthy",
  "version": "1.0.0"
}
```

---

### 2. Get Statistics

Get translation statistics and cache information.

**Endpoint:** `GET /api/stats`

**Request:**
```bash
curl http://localhost:8000/api/stats
```

**Response:**
```json
{
  "cache_stats": {
    "hits": 150,
    "misses": 50,
    "total_requests": 200,
    "hit_rate_percent": 75.0,
    "connected": true
  },
  "total_translations": 200
}
```

---

### 3. Translate Text

Translate text between English and Korean with automatic language detection.

**Endpoint:** `POST /api/translate`

**Request Body:**
```json
{
  "text": "Hello, how are you?"
}
```

**Request (curl):**
```bash
curl -X POST http://localhost:8000/api/translate \
  -H "Content-Type: application/json" \
  -d '{"text": "Hello, how are you?"}'
```

**Request (JavaScript):**
```javascript
const response = await fetch('http://localhost:8000/api/translate', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ text: 'Hello, how are you?' })
});
const data = await response.json();
```

**Response:**
```json
{
  "original": "Hello, how are you?",
  "detected_language": "en",
  "translation": "안녕하세요, 어떻게 지내세요?",
  "quality_score": 0.92
}
```

**Fields:**
- `original` (string): Original input text
- `detected_language` (string): Detected language code ("en" or "ko")
- `translation` (string): Translated text
- `quality_score` (float): Quality score from 0.0 to 1.0

**Error Responses:**

400 Bad Request:
```json
{
  "detail": "Text cannot be empty"
}
```

500 Internal Server Error:
```json
{
  "detail": "Translation failed: [error message]"
}
```

---

### 4. Translate Document

Upload and translate documents in PDF, DOCX, or TXT format.

**Endpoint:** `POST /api/translate/document`

**Request:**
- Content-Type: `multipart/form-data`
- Field: `file` (file upload)

**Request (curl):**
```bash
curl -X POST http://localhost:8000/api/translate/document \
  -F "file=@document.pdf"
```

**Request (JavaScript):**
```javascript
const formData = new FormData();
formData.append('file', fileInput.files[0]);

const response = await fetch('http://localhost:8000/api/translate/document', {
  method: 'POST',
  body: formData
});

// Response is a downloadable file
const blob = await response.blob();
const url = window.URL.createObjectURL(blob);
const a = document.createElement('a');
a.href = url;
a.download = 'translated.txt';
a.click();
```

**Response:**
- Content-Type: `text/plain`
- Content-Disposition: `attachment; filename=document_translated.txt`
- Body: Translated text content

**Supported Formats:**
- PDF (`.pdf`)
- Microsoft Word (`.docx`)
- Plain Text (`.txt`)

**File Size Limit:** 10MB

**Error Responses:**

400 Bad Request (unsupported format):
```json
{
  "detail": "Unsupported file format. Supported: ['.pdf', '.docx', '.txt']"
}
```

400 Bad Request (file too large):
```json
{
  "detail": "File too large. Maximum size: 10MB"
}
```

---

### 5. WebSocket Real-time Translation

WebSocket endpoint for real-time translation as you type.

**Endpoint:** `ws://localhost:8000/ws/translate`

**Connection (JavaScript):**
```javascript
const ws = new WebSocket('ws://localhost:8000/ws/translate');

ws.onopen = () => {
  console.log('Connected to translation WebSocket');
};

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log('Translation:', data);
};

ws.onerror = (error) => {
  console.error('WebSocket error:', error);
};

// Send text to translate
ws.send('Hello, world!');
```

**Message Format (Send):**
```
Plain text string
```

**Message Format (Receive):**
```json
{
  "original": "Hello, world!",
  "detected_language": "en",
  "translation": "안녕하세요, 세계!",
  "quality_score": 0.95
}
```

**Error Message:**
```json
{
  "error": "Error message"
}
```

**Best Practices:**
- Implement debouncing on the client side (500ms recommended)
- Handle reconnection on disconnect
- Close connection when not in use

---

## Rate Limiting

Currently, no rate limiting is implemented. Consider implementing rate limiting in production:
- Per IP: 100 requests per minute
- Per API key: 1000 requests per hour

## Caching

- Translations are automatically cached for 24 hours
- Cache key is based on text hash
- Cached responses are returned in < 50ms
- Check cache statistics with `/api/stats`

## Error Handling

All errors follow this format:

```json
{
  "detail": "Human-readable error message"
}
```

Common error scenarios:
1. Empty text input → 400 Bad Request
2. Invalid file format → 400 Bad Request
3. File too large → 400 Bad Request
4. Translation service error → 500 Internal Server Error
5. OpenAI API error → 500 Internal Server Error

## Best Practices

1. **Text Translation:**
   - Keep text length under 4000 characters for best performance
   - Longer texts are automatically chunked in document translation

2. **Document Translation:**
   - Supported formats: PDF, DOCX, TXT
   - Maximum file size: 10MB
   - Large documents may take several minutes

3. **WebSocket:**
   - Implement client-side debouncing
   - Handle reconnection gracefully
   - Close connection when done

4. **Caching:**
   - Identical text returns cached results
   - Cache hit rate shown in statistics
   - 24-hour cache expiration

## Examples

### Python Example

```python
import requests

# Text translation
response = requests.post(
    'http://localhost:8000/api/translate',
    json={'text': 'Hello, world!'}
)
result = response.json()
print(f"Translation: {result['translation']}")
print(f"Quality: {result['quality_score']}")

# Document translation
with open('document.pdf', 'rb') as f:
    response = requests.post(
        'http://localhost:8000/api/translate/document',
        files={'file': f}
    )
    with open('translated.txt', 'wb') as out:
        out.write(response.content)
```

### TypeScript Example

```typescript
interface TranslateRequest {
  text: string;
}

interface TranslateResponse {
  original: string;
  detected_language: string;
  translation: string;
  quality_score: number;
}

async function translateText(text: string): Promise<TranslateResponse> {
  const response = await fetch('http://localhost:8000/api/translate', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ text })
  });
  
  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail);
  }
  
  return response.json();
}

// Usage
try {
  const result = await translateText('Hello!');
  console.log(result.translation);
} catch (error) {
  console.error('Translation failed:', error);
}
```

---

## OpenAPI Documentation

Interactive API documentation is available at:

**Swagger UI:** http://localhost:8000/docs

**ReDoc:** http://localhost:8000/redoc

These provide interactive testing and detailed schema information.
