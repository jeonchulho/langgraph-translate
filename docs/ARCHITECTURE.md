# Architecture Documentation

System architecture and design decisions for LangGraph Translation Service.

## System Overview

The LangGraph Translation Service is a full-stack application that provides AI-powered translation between English and Korean with quality validation and automatic retry mechanisms.

## High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         Client Layer                            │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐         │
│  │ Web Browser  │  │ Discord Bot  │  │  Slack Bot   │         │
│  └──────────────┘  └──────────────┘  └──────────────┘         │
└────────────┬────────────────┬────────────────┬─────────────────┘
             │                │                │
             ▼                ▼                ▼
┌─────────────────────────────────────────────────────────────────┐
│                      Nginx Reverse Proxy                        │
│                  (Load Balancing & Routing)                     │
└────────────┬────────────────────────────────┬─────────────────┘
             │                                │
             ▼                                ▼
┌──────────────────────────┐    ┌──────────────────────────────┐
│   Frontend Service       │    │    Backend Service           │
│   (React + Vite)         │    │    (FastAPI + LangGraph)     │
│                          │    │                              │
│   - Text Translation UI  │    │   - REST API Endpoints       │
│   - Document Upload      │    │   - WebSocket Server         │
│   - Real-time WebSocket  │    │   - Translation Engine       │
│   - Dark Mode            │    │   - Document Processor       │
└──────────────────────────┘    │   - Cache Manager            │
                                └────────┬─────────────────────┘
                                         │
                    ┌────────────────────┼────────────────────┐
                    ▼                    ▼                    ▼
          ┌──────────────────┐  ┌──────────────┐  ┌──────────────────┐
          │ Redis Cache      │  │ OpenAI API   │  │ Document Storage │
          │ (24h TTL)        │  │ (GPT-4)      │  │ (Temporary)      │
          └──────────────────┘  └──────────────┘  └──────────────────┘
```

## Core Components

### 1. LangGraph Translation Engine

The heart of the system, implementing a state machine workflow for translation with quality validation.

**Workflow Graph:**

```
                     ┌──────────────────┐
                     │   Start          │
                     └────────┬─────────┘
                              │
                              ▼
                     ┌──────────────────┐
                     │ Detect Language  │
                     │ (en/ko)          │
                     └────────┬─────────┘
                              │
                              ▼
                     ┌──────────────────┐
                     │   Translate      │
                     │   (GPT-4)        │
                     └────────┬─────────┘
                              │
                              ▼
                     ┌──────────────────┐
                     │ Validate Quality │
                     │ (0.0 - 1.0)      │
                     └────────┬─────────┘
                              │
                    ┌─────────┴──────────┐
                    │                    │
           Score < 0.7 AND              Score >= 0.7 OR
           Retries < 2                  Retries >= 2
                    │                    │
                    ▼                    ▼
          ┌──────────────────┐  ┌──────────────────┐
          │   Retranslate    │  │    Finalize      │
          │  (Retry Logic)   │  │  (Return Result) │
          └────────┬─────────┘  └──────────────────┘
                   │                     │
                   └──────────┬──────────┘
                              ▼
                     ┌──────────────────┐
                     │      End         │
                     └──────────────────┘
```

**State Structure:**
```python
{
    "original_text": str,
    "detected_language": "en" | "ko",
    "translation": str,
    "quality_score": float,
    "retry_count": int,
    "max_retries": int,
    "final_result": dict
}
```

### 2. FastAPI Backend

RESTful API server with WebSocket support.

**Key Features:**
- Async/await for concurrent requests
- Pydantic models for validation
- Automatic OpenAPI documentation
- CORS middleware for development
- Structured logging

**Endpoints:**
- `GET /api/health` - Health check
- `GET /api/stats` - Statistics
- `POST /api/translate` - Text translation
- `POST /api/translate/document` - Document translation
- `WebSocket /ws/translate` - Real-time translation

### 3. Redis Caching Layer

**Purpose:** Reduce API costs and improve response times

**Cache Strategy:**
- Key: SHA-256 hash of input text
- Value: JSON-serialized translation result
- TTL: 86400 seconds (24 hours)
- Eviction: LRU (Redis default)

**Cache Statistics:**
- Hit/miss counters
- Hit rate percentage
- Total request count

### 4. Document Processing Pipeline

**Flow:**
```
Upload → Validate → Extract Text → Chunk → Translate → Combine → Download
```

**Chunking Strategy:**
- Max chunk size: 4000 characters
- Split by paragraphs first
- Fall back to sentences if needed
- Maintain context between chunks

**Supported Formats:**
- PDF: PyPDF2 (text extraction)
- DOCX: python-docx (paragraph extraction)
- TXT: Direct read with encoding detection

### 5. React Frontend

**Component Hierarchy:**
```
App (Main Container)
├── Header (Title + Dark Mode Toggle)
├── TabNavigation
│   ├── Text Translation Tab
│   │   └── TranslatorUI
│   │       ├── Input Textarea
│   │       ├── Output Display
│   │       ├── Translate Button
│   │       ├── Quality Score Bar
│   │       └── History Sidebar
│   ├── Document Translation Tab
│   │   └── DocumentUpload
│   │       ├── Drag & Drop Area
│   │       ├── File Selector
│   │       ├── Preview
│   │       ├── Progress Bar
│   │       └── Download Button
│   └── Real-time Translation Tab
│       └── RealtimeTranslator
│           ├── Connection Status
│           ├── Input Textarea (Debounced)
│           └── Output Display
└── Footer
```

**State Management:**
- Local React state (useState)
- No global state library needed (simple app)
- WebSocket state in RealtimeTranslator

### 6. Bot Integration

**Discord Bot:**
- discord.py 2.0+ with slash commands
- Async message handling
- Embed formatting for results

**Slack Bot:**
- slack-bolt framework
- Slash commands + mentions
- Block Kit for rich formatting
- Socket Mode for development

## Data Flow

### Text Translation Request

```
1. User inputs text in UI
2. Frontend sends POST /api/translate
3. Backend checks Redis cache
4. If cache miss:
   a. Initialize LangGraph workflow
   b. Detect language
   c. Call OpenAI GPT-4 for translation
   d. Validate quality
   e. Retry if quality < 0.7 (max 2 times)
   f. Cache result
5. Return translation to frontend
6. Display result with quality score
```

### Document Translation Request

```
1. User uploads document
2. Frontend validates format and size
3. POST /api/translate/document with multipart/form-data
4. Backend extracts text from document
5. Split text into chunks (4000 chars)
6. For each chunk:
   a. Check cache
   b. Translate if cache miss
   c. Cache result
7. Combine all translated chunks
8. Return as downloadable file
9. Frontend triggers download
```

### Real-time WebSocket Translation

```
1. User connects to WebSocket
2. User types in textarea
3. Frontend debounces input (500ms)
4. Send text via WebSocket
5. Backend receives text
6. Check cache or translate
7. Send result back via WebSocket
8. Frontend displays immediately
9. Repeat for each input change
```

## Technology Stack Decisions

### Why LangGraph?

**Pros:**
- Explicit workflow definition
- Easy to understand and modify
- Built-in state management
- Conditional routing
- Integration with LangChain/OpenAI

**Alternatives Considered:**
- Plain LangChain: Less explicit workflow
- Custom state machine: More code to maintain

### Why FastAPI?

**Pros:**
- Async/await support
- Automatic validation with Pydantic
- Built-in OpenAPI docs
- High performance
- Easy WebSocket support

**Alternatives Considered:**
- Flask: No async, less modern
- Django: Too heavy for this use case

### Why Redis?

**Pros:**
- Fast in-memory storage
- Simple key-value model
- TTL support
- Easy to scale

**Alternatives Considered:**
- Memcached: Less features
- Database: Slower, overkill

### Why React + TypeScript?

**Pros:**
- Type safety
- Component reusability
- Large ecosystem
- Excellent tooling

**Alternatives Considered:**
- Vue: Less ecosystem
- Plain JavaScript: No type safety
- Svelte: Smaller ecosystem

## Scalability Considerations

### Current Limitations

1. **Single OpenAI API Key**: Sequential requests
2. **No Load Balancing**: Single backend instance
3. **No Persistence**: Cache lost on restart
4. **No Authentication**: Open to all users

### Scaling Strategies

**Horizontal Scaling:**
```
Load Balancer
    ├── Backend Instance 1
    ├── Backend Instance 2
    └── Backend Instance 3
         ↓
    Redis Cluster
```

**Performance Optimizations:**
1. Redis cluster for high availability
2. Multiple OpenAI API keys with round-robin
3. CDN for frontend assets
4. Request queuing for rate limiting
5. Database for persistent analytics

**Estimated Capacity (Current):**
- Concurrent users: ~100
- Requests per second: ~10
- Cache hit rate: 70-80%
- Average response time: 2-3 seconds

## Security Considerations

### Current Implementation

1. **API Key Management**: Environment variables only
2. **CORS**: Open for development (needs restriction)
3. **Input Validation**: Pydantic models
4. **File Size Limits**: 10MB maximum
5. **No Rate Limiting**: Needs implementation

### Production Recommendations

1. **Authentication**: API key or OAuth
2. **Rate Limiting**: Per user/IP
3. **HTTPS**: TLS encryption
4. **Redis Auth**: Password protection
5. **Input Sanitization**: XSS prevention
6. **File Scanning**: Virus checking
7. **Audit Logging**: Track all requests

## Monitoring and Observability

### Metrics to Track

1. **Performance:**
   - Request latency (p50, p95, p99)
   - Cache hit rate
   - OpenAI API response time
   - Error rate

2. **Business:**
   - Total translations
   - Language distribution
   - Popular translation pairs
   - Document vs text ratio

3. **Infrastructure:**
   - CPU/Memory usage
   - Redis memory usage
   - Network bandwidth
   - Disk I/O

### Recommended Tools

- **Logging**: Structured logging with ELK stack
- **Metrics**: Prometheus + Grafana
- **Tracing**: OpenTelemetry
- **Alerting**: PagerDuty or Opsgenie

## Future Enhancements

### Planned Features

1. **More Languages**: Extend beyond EN/KO
2. **Batch Translation**: API for multiple texts
3. **Custom Models**: Fine-tuned models
4. **User Accounts**: Save history, preferences
5. **API Authentication**: Secure access
6. **Analytics Dashboard**: Usage insights

### Technical Improvements

1. **Background Jobs**: Celery for long tasks
2. **Database**: PostgreSQL for persistence
3. **Message Queue**: RabbitMQ for async processing
4. **Kubernetes**: Container orchestration
5. **CI/CD**: Automated testing and deployment

## Conclusion

The LangGraph Translation Service demonstrates a modern, scalable architecture for AI-powered translation. The use of LangGraph provides a clear, maintainable workflow that can be easily extended with additional quality checks or translation steps.

Key strengths:
- Clear separation of concerns
- Stateful workflow with quality validation
- Efficient caching strategy
- Modern tech stack
- Multiple integration options

Areas for improvement:
- Authentication and authorization
- Horizontal scaling support
- Persistent storage
- Comprehensive monitoring
- Production-grade security
