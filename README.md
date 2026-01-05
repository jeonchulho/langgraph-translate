# LangGraph Translator - 영한 번역 서비스

AI 기반의 고품질 영문↔한글 번역 서비스

## 🚀 주요 기능

- ✅ 자동 언어 감지
- ✅ AI 품질 검증 및 자동 재번역
- ✅ 문서 번역 (PDF, DOCX, TXT)
- ✅ 실시간 WebSocket 번역
- ✅ Discord/Slack 봇 통합
- ✅ Redis 캐싱
- ✅ 반응형 웹 인터페이스

## 🛠 기술 스택

### Backend
- Python 3.11
- LangGraph - 워크플로우 오케스트레이션
- FastAPI - RESTful API 서버
- OpenAI GPT-4 - 번역 엔진
- Redis - 결과 캐싱
- PyPDF2, python-docx - 문서 처리

### Frontend
- React 18 + TypeScript
- Vite - 빌드 도구
- TailwindCSS - 스타일링
- Axios - HTTP 클라이언트

### Infrastructure
- Docker & Docker Compose
- Nginx - 리버스 프록시
- Redis - 캐시 저장소

## 📦 설치 및 실행

### Docker로 실행 (권장)

1. 저장소 클론
```bash
git clone https://github.com/jeonchulho/langgraph-translate.git
cd langgraph-translate
```

2. 환경 변수 설정
```bash
cp .env.example .env
# .env 파일을 열어 OPENAI_API_KEY를 설정하세요
```

3. Docker Compose로 실행
```bash
docker-compose up --build
```

4. 브라우저에서 접속
- 웹 인터페이스: http://localhost:8080
- API 문서: http://localhost:8000/docs
- Redis: localhost:6379

### 로컬 개발

#### 백엔드

```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt

# 환경 변수 설정
export OPENAI_API_KEY=your_api_key
export REDIS_URL=redis://localhost:6379

# 서버 실행
uvicorn api.main:app --reload
```

#### 프론트엔드

```bash
cd frontend
npm install
npm run dev
```

서버가 http://localhost:5173 에서 실행됩니다.

#### Redis (로컬)

```bash
# Docker로 Redis 실행
docker run -d -p 6379:6379 redis:7-alpine

# 또는 로컬에 설치된 Redis 사용
redis-server
```

## 🔑 환경 변수

### 필수

- `OPENAI_API_KEY`: OpenAI API 키 (GPT-4 액세스 필요)

### 선택

- `REDIS_URL`: Redis 연결 URL (기본값: redis://localhost:6379)
- `LOG_LEVEL`: 로그 레벨 (기본값: INFO)
- `DISCORD_BOT_TOKEN`: Discord 봇 토큰
- `SLACK_BOT_TOKEN`: Slack 봇 토큰
- `SLACK_APP_TOKEN`: Slack 앱 토큰 (Socket Mode용)
- `BACKEND_URL`: 봇에서 사용할 백엔드 URL (기본값: http://backend:8000)

## 📚 문서

- [API 문서](docs/API.md) - 모든 엔드포인트 상세 설명
- [아키텍처](docs/ARCHITECTURE.md) - 시스템 구조 및 설계

## 🧪 테스트

### 백엔드 테스트

```bash
cd backend
pytest

# 커버리지와 함께
pytest --cov=. --cov-report=html
```

### 프론트엔드 테스트

```bash
cd frontend
npm test

# 커버리지와 함께
npm test -- --coverage
```

## 🤖 봇 사용

### Discord 봇

1. Discord Developer Portal에서 봇 생성
2. 환경 변수에 토큰 설정
3. 봇 실행:
```bash
cd bots
pip install -r requirements.txt
python discord_bot.py
```

사용 가능한 명령어:
- `/translate <text>` - 텍스트 번역
- `/help` - 도움말 표시

### Slack 봇

1. Slack App 생성 및 설정
2. 환경 변수에 토큰 설정
3. 봇 실행:
```bash
cd bots
pip install -r requirements.txt
python slack_bot.py
```

사용 방법:
- `/translate [텍스트]` - 슬래시 커맨드
- `@번역봇 [텍스트]` - 멘션

## 🏗 프로젝트 구조

```
langgraph-translate/
├── backend/              # Python 백엔드
│   ├── api/             # FastAPI 엔드포인트
│   ├── translator/      # 번역 엔진 및 로직
│   └── tests/           # 테스트 코드
├── frontend/            # React 프론트엔드
│   └── src/
│       ├── components/  # React 컴포넌트
│       └── api/         # API 클라이언트
├── bots/                # Discord/Slack 봇
├── nginx/               # Nginx 설정
├── docs/                # 문서
└── docker-compose.yml   # Docker Compose 설정
```

## 🔧 개발 가이드

### 코드 스타일

- Python: PEP 8, 타입 힌트 필수
- TypeScript: Strict 모드, ESLint
- 커밋: Conventional Commits

### 새 기능 추가

1. 이슈 생성 및 논의
2. Feature 브랜치 생성
3. 코드 작성 및 테스트
4. Pull Request 생성
5. 코드 리뷰 후 머지

## 📊 성능

- 캐시 히트 시: < 50ms
- 첫 번역: 2-5초 (GPT-4 호출 포함)
- 재번역 (품질 낮을 경우): 추가 2-5초
- 문서 번역: 크기에 따라 가변

## 🛡 보안

- API 키는 환경 변수로만 관리
- CORS는 프로덕션에서 제한 필요
- Redis는 인증 설정 권장
- HTTPS 사용 권장 (프로덕션)

## 🤝 기여

기여를 환영합니다! 다음 방법으로 기여할 수 있습니다:

1. 버그 리포트
2. 기능 제안
3. 코드 기여
4. 문서 개선

## 📄 라이선스

MIT License - 자세한 내용은 [LICENSE](LICENSE) 파일 참조

## 🙏 감사의 글

- OpenAI - GPT-4 API
- LangGraph - 워크플로우 프레임워크
- FastAPI - 웹 프레임워크
- React - UI 라이브러리

## 📞 문의

이슈 트래커: https://github.com/jeonchulho/langgraph-translate/issues

---

Made with ❤️ using LangGraph and OpenAI