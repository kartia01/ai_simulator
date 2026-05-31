# Ad Simulator — 팀 아키텍처 가이드

> "광고 소재를 입력하면, AI 페르소나들이 실제 사람처럼 반응해 CTR/VTR/ROAS를 예측한다"

---

## 목차

1. [전체 시스템 구조](#1-전체-시스템-구조)
2. [데이터 흐름 (요청 → 응답)](#2-데이터-흐름-요청--응답)
3. [레이어별 역할과 파일](#3-레이어별-역할과-파일)
4. [핵심 설계 결정 3가지](#4-핵심-설계-결정-3가지)
5. [JSON 스키마 — 레이어 간 계약](#5-json-스키마--레이어-간-계약)
6. [로컬 실행 방법](#6-로컬-실행-방법)

---

## 1. 전체 시스템 구조

```
┌─────────────────────────────────────────────────────────┐
│  Browser  :3000                                         │
│  React Dashboard  (Tailwind CSS)                        │
│  - 광고 소재 입력 폼                                     │
│  - KPI 메트릭 카드 (VTR / CTR / Dropout / Appeal)       │
│  - 3단계 인지 퍼널 시각화                                │
│  - 페르소나별 반응 카드                                  │
└────────────────────┬────────────────────────────────────┘
                     │  POST /api/simulate (camelCase JSON)
                     ▼
┌─────────────────────────────────────────────────────────┐
│  Spring Boot  :8080  (Control Tower)                    │
│  - PostgreSQL에서 페르소나 데이터 조회                   │
│  - FastAPI 호출 (WebClient, 비동기)                      │
│  - 결과를 React에 반환                                   │
└────────────────────┬────────────────────────────────────┘
                     │  POST /simulate (snake_case JSON)
                     ▼
┌─────────────────────────────────────────────────────────┐
│  Python FastAPI  :8000  (AI Agent Engine)               │
│  - 각 페르소나에 시스템 프롬프트 주입                    │
│  - OpenAI gpt-4o-mini 병렬 호출                         │
│  - 3단계 인지 루프 결과 반환                             │
└────────────────────┬────────────────────────────────────┘
                     │  Chat Completions API
                     ▼
              OpenAI / Anthropic
```

---

## 2. 데이터 흐름 (요청 → 응답)

```
[1] 마케터가 광고 소재를 입력하고 "Run Simulation" 클릭
        ↓
[2] React → Spring Boot
    POST /api/simulate
    { adId, adContent, adType: "IMAGE", personaIds: [] }

[3] Spring Boot → PostgreSQL
    personas 테이블에서 대상 페르소나 목록 조회

[4] Spring Boot → FastAPI  (내부 서버 간 통신)
    POST /simulate
    { ad_id, ad_content, ad_type, personas: [...30명...] }

[5] FastAPI → OpenAI  (페르소나마다 병렬 호출)
    ┌ Stage 1: 대표 3명 먼저 스크리닝 (비용 최적화)
    └ Stage 2: 나머지 27명 asyncio.gather로 병렬 실행

[6] OpenAI → FastAPI
    각 페르소나마다 3단계 인지 루프 JSON 반환

[7] FastAPI → Spring Boot
    집계 완료된 SimulationResponse (metrics 포함) 반환

[8] Spring Boot → React
    동일 구조를 camelCase로 변환해 전달

[9] React가 결과 시각화
    - KPI 메트릭 카드
    - 3단계 인지 퍼널 바
    - 키워드 빈도 차트
    - 페르소나별 상세 카드
```

---

## 3. 레이어별 역할과 파일

### Layer 1 — React 대시보드 (`frontend/src/`)

| 파일 | 역할 |
|------|------|
| `api/simulationApi.js` | Spring Boot REST 호출 (fetch wrapper) |
| `hooks/useSimulation.js` | 시뮬레이션 상태 관리 (loading / result / error) |
| `components/SimulationDashboard.jsx` | 메인 페이지 — 입력 폼 + 결과 전체 조율 |
| `components/MetricsPanel.jsx` | VTR·CTR·Dropout·Appeal 4개 KPI 카드 |
| `components/CognitiveTimeline.jsx` | 3단계 퍼널 바 시각화 |
| `components/PersonaFeedbackCard.jsx` | 페르소나 1명의 3단계 반응 카드 |

---

### Layer 2 — Spring Boot 백엔드 (`backend/src/main/java/com/adsimulator/`)

| 디렉터리 | 파일 | 역할 |
|----------|------|------|
| `controller/` | `SimulationController.java` | `POST /api/simulate` 엔드포인트 |
| `service/` | `SimulationService.java` | DB 조회 → FastAPI 호출 → 결과 반환 오케스트레이션 |
| `client/` | `FastApiClient.java` | WebClient로 FastAPI 비동기 HTTP 호출 |
| `entity/` | `Persona.java` | PostgreSQL `personas` 테이블 JPA 엔티티 |
| `repository/` | `PersonaRepository.java` | JPA 쿼리 인터페이스 |
| `dto/fastapi/` | `SimulationPayload.java`, `PersonaPayload.java` | FastAPI로 **보내는** DTO (snake_case 직렬화) |
| `dto/response/` | `SimulationResultDto.java` 외 5개 | FastAPI에서 **받는** DTO (snake_case → camelCase 역직렬화) |
| `dto/request/` | `AdSimulationRequest.java` | React에서 받는 요청 DTO |
| `config/` | `WebClientConfig.java` | WebClient 타임아웃 설정 |

---

### Layer 3 — FastAPI AI 엔진 (`ai-engine/`)

| 파일 | 역할 |
|------|------|
| `app/schemas.py` | Pydantic 입출력 스키마 정의 (3단계 인지 루프 구조 강제) |
| `app/prompts.py` | 시스템 프롬프트 템플릿 — "AI 기업 말투" 차단 규칙 포함 |
| `app/agent.py` | Cascade 파이프라인 + OpenAI 병렬 호출 + 메트릭 계산 |
| `main.py` | FastAPI 앱 진입점, `/simulate` `/health` 엔드포인트 |

---

## 4. 핵심 설계 결정 3가지

### ① 3단계 인지 루프 — AI 기업 말투 차단

LLM에게 "광고를 평가해줘"라고 하면 정중하고 분석적인 답변만 나옵니다.
이를 막기 위해 프롬프트를 **금지 규칙 + 행동 제약** 형식으로 구성했습니다.

```
❌ FORBIDDEN: "This ad effectively conveys..."
❌ FORBIDDEN: "The visual hierarchy suggests..."
✅ REQUIRED: Your only question is "Does this help ME, RIGHT NOW?"
✅ REQUIRED: If a scroll trigger fires → you ARE gone. No second chances.
```

그리고 반응을 3단계로 분리해 **순서대로 강제** 합니다:

```
Step 1 (1.5초): 무의식 반응 → 키워드 3개 + 직감 점수
Step 2 (3초):   자기중심 필터 → 이탈 여부(boolean) + 독백
Step 3 (결정):  최종 행동 → 클릭 여부(boolean) + 이유
```

---

### ② Cascade 파이프라인 — 토큰 비용 절감

30명 전원에게 바로 API를 날리면 **토큰 수십만 개가 한 번에 소모**됩니다.

```
[Stage 1]  대표 페르소나 3명 먼저 실행  (스크리닝)
                ↓
[Stage 2]  나머지 27명 asyncio.gather 병렬 실행
```

`agent.py`의 `run_cascade_simulation` 함수가 이 구조를 구현합니다.
필요하면 Stage 1 결과가 낮을 경우 Stage 2를 건너뛰는 조기 종료 로직도 추가할 수 있습니다.

---

### ③ JSON 필드명 변환 전략 — 전역 설정 없이 DTO별 관리

세 레이어가 서로 다른 케이스 컨벤션을 씁니다:

| 레이어 | 컨벤션 | 이유 |
|--------|--------|------|
| Python (FastAPI) | `snake_case` | Pydantic 기본값 |
| Java (Spring Boot) | `camelCase` | Java 컨벤션 |
| React | `camelCase` | JavaScript 컨벤션 |

Spring Boot의 Jackson 전역 설정을 `SNAKE_CASE`로 바꾸면 다른 API까지 영향을 받습니다.
대신 **FastAPI 전용 DTO에만 `@JsonProperty`를 붙이는 방식**으로 격리했습니다:

```java
// FastAPI로 보낼 때: Java camelCase → JSON snake_case
public record PersonaPayload(
    @JsonProperty("drop_off_trigger") String dropOffTrigger, ...
)

// FastAPI에서 받을 때: JSON snake_case → Java camelCase
public record CognitiveLoopResultDto(
    @JsonProperty("step1_unconscious_reaction") UnconsciousReactionDto step1UnconsciousReaction, ...
)
```

React에는 Spring Boot가 Jackson 기본값(camelCase)으로 재직렬화해서 보냅니다.

---

## 5. JSON 스키마 — 레이어 간 계약

### FastAPI → Spring Boot (snake_case)

```json
{
  "ad_id": "ad-1234",
  "total_personas": 30,
  "results": [
    {
      "persona_id": "uuid-...",
      "step1_unconscious_reaction": {
        "keywords": ["촌스럽다", "뭔가비싸", "일단궁금"],
        "appeal_score": 3
      },
      "step2_selfish_filtering": {
        "is_dropped_out": false,
        "reason": "나 요즘 이거 찾고 있었는데? 잠깐 봐야겠다"
      },
      "step3_final_action": {
        "clicked": true,
        "action_reason": "가격이 보여서 눌렀음"
      }
    }
  ],
  "metrics": {
    "vtr": 73.3,
    "ctr": 23.3,
    "dropout_rate": 26.7,
    "avg_appeal_score": 2.87
  }
}
```

### Spring Boot → React (camelCase)

```json
{
  "adId": "ad-1234",
  "totalPersonas": 30,
  "results": [
    {
      "personaId": "uuid-...",
      "step1UnconsciousReaction": {
        "keywords": ["촌스럽다", "뭔가비싸", "일단궁금"],
        "appealScore": 3
      },
      "step2SelfishFiltering": {
        "isDroppedOut": false,
        "reason": "나 요즘 이거 찾고 있었는데? 잠깐 봐야겠다"
      },
      "step3FinalAction": {
        "clicked": true,
        "actionReason": "가격이 보여서 눌렀음"
      }
    }
  ],
  "metrics": {
    "vtr": 73.3,
    "ctr": 23.3,
    "dropoutRate": 26.7,
    "avgAppealScore": 2.87
  }
}
```

---

## 6. 로컬 실행 방법

### 사전 준비

- Python 3.11+
- Java 21 + Maven
- Node.js 20+
- PostgreSQL (또는 Docker)
- OpenAI API Key

### PostgreSQL (Docker)

```bash
docker run -d \
  --name ad-simulator-db \
  -e POSTGRES_DB=ad_simulator \
  -e POSTGRES_USER=postgres \
  -e POSTGRES_PASSWORD=postgres \
  -p 5432:5432 \
  postgres:16
```

### AI Engine (Python FastAPI)

```bash
cd ai-engine
pip install -r requirements.txt
OPENAI_API_KEY=sk-... uvicorn main:app --reload --port 8000
```

### Spring Boot 백엔드

```bash
cd backend
./mvnw spring-boot:run
# 기본 포트: 8080
# application.yml의 DB 설정 확인 필요
```

### React 프론트엔드

```bash
cd frontend
npm install
npm start
# 브라우저 자동 오픈: http://localhost:3000
# package.json의 "proxy": "http://localhost:8080" 으로 CORS 우회
```

---

## 도메인별 담당 파일 가이드

| 도메인 (AdProject.md 기준) | 담당 파일 |
|---------------------------|-----------|
| **1. Persona Management** | `entity/Persona.java`, `repository/PersonaRepository.java`, `schemas.py:PersonaInput` |
| **2. Core Agent Engine** | `app/agent.py`, `app/prompts.py`, `client/FastApiClient.java` |
| **3. Cost & Performance Optimizer** | `agent.py:run_cascade_simulation` (Cascade), `app/schemas.py:AdMetrics` |
| **4. Insight Analytics** | `components/MetricsPanel.jsx`, `components/CognitiveTimeline.jsx`, `KeywordFrequency` in Dashboard |
| **5. Platform Automation** | 현재 미구현 — FastAPI에 `/automate` 엔드포인트로 확장 예정 |
| **6. Content Generation Fallback** | 현재 미구현 — Step-3 결과 기반 카피 생성 추가 예정 |
