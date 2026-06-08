# AI_CONTEXT — ClickMe 프로젝트 (v1.1)

> IDE 및 AI 어시스턴트용 컨텍스트 파일. 이 프로젝트를 처음 접하는 경우 여기서 시작하세요.
> `docs/` 디렉토리 내 다른 문서들도 함께 읽으면 프로젝트 맥락을 완전히 이해할 수 있습니다.

| 버전 | v1.1 |
|---|---|
| 작성일 | 2026-06-08 |
| 베이스라인 | 2026-06-12 |
| 최종 목표 | 2026-07-08 |
| 발표 | 2026-07-14 |

---

## 1. 이 프로젝트는 무엇인가

**ClickMe**는 광고를 업로드하면 AI가 가상 소비자 페르소나의 반응을 시뮬레이션하고, CTR/CVR 등 성과를 예측하여 개선안까지 제공하는 **광고 효과 분석 플랫폼**이다.

핵심: **시뮬레이션** — 광고 분석 → 페르소나 생성 → 반응 시뮬레이션 → 집계 → 예측 → 개선안의 6단계 LangGraph 파이프라인.

---

## 2. 핵심 개념

| 개념 | 설명 |
|---|---|
| **시뮬레이션** | 6단계 LangGraph 파이프라인 1회 실행 |
| **페르소나** | AI가 생성한 가상 소비자. 20명 기본. 3계층 속성 (인구통계/심리/서사) |
| **Stage** | 파이프라인의 한 단계. 각 팀원이 독립 개발 |
| **Contract** | Stage 간 Input/Output Pydantic 스키마. 계약 먼저, 구현 나중 |
| **Producer ID** | 동일 Stage의 여러 구현체를 구분하는 식별자 |
| **LangSmith** | 모든 LLM 호출의 Input/Output/Cost/Latency 자동 추적 |
| **Harness** | 동일 입력으로 N회 반복 실행해 일관성/성능을 측정하는 테스트 방식 |

---

## 3. 기술 스택

| 레이어 | 기술 |
|---|---|
| Frontend | Next.js 15, React 19, TypeScript, Zustand, TanStack Query |
| Backend | FastAPI (Python 3.12), Uvicorn, Pydantic v2, SQLAlchemy Async |
| AI | LangGraph, LangChain, LangSmith |
| LLM | GPT-4o Vision / GPT-4o-mini / Claude Haiku / Claude Sonnet |
| DB | NeonDB (PostgreSQL 16 + pgvector) |
| Cloud | AWS S3, AWS SQS (Phase 2) |
| 패키지 관리 | uv (Python 전체), npm (Node.js) |
| 인증 | Phase 1: UI 역할 선택만 / Phase 2: OAuth2+JWT (미정) |

> Java / Spring Boot 없음. Backend + AI 모두 Python (FastAPI).

---

## 4. 서비스 구조

```
프로젝트 루트/
├── frontend/      Next.js — UI, 역할 선택 로그인, 시뮬레이션 결과 표시
└── ai-service/    FastAPI + LangGraph — API, 시뮬레이션 파이프라인, SSE
```

Phase 1: frontend ↔ ai-service 직접 통신. Java backend 미사용.

---

## 5. Phase 1 인증 (중요)

Phase 1 (6/12 베이스라인)에는 **실제 인증이 없다.**

```
로그인 페이지  →  [관리자로 진입] 클릭  →  /admin
               →  [사용자로 진입] 클릭  →  / (채팅창)
```

- Zustand store에 선택된 역할(`admin` | `user`) 저장
- 클라이언트 UI 접근 제어만 존재 (실제 보안 없음)
- 백엔드 인증 API 없음, JWT 없음

Phase 2 (7/8 목표)에서 OAuth2/JWT 실제 구현 여부는 **미정**.

---

## 6. 문서 인덱스

| 문서 | 파일 | 내용 |
|---|---|---|
| 기획서 | [기획서.md](기획서.md) | 프로젝트 목표, 기능, 일정, 기술 스택, 결정사항 |
| 아키텍처 | [아키텍처.md](아키텍처.md) | 시스템 구성, 데이터 흐름, Phase 1 인증, 환경 변수 |
| 요구사항 | [요구사항.md](요구사항.md) | 기능/비기능 요구사항, 역할 권한, 화면 목록 |
| API 명세 | [API명세서.md](API명세서.md) | 엔드포인트, 요청/응답 스키마 |
| 시뮬레이션 | [시뮬레이션.md](시뮬레이션.md) | 6단계 파이프라인, Stage별 Contract (Pydantic), LangGraph |
| AI 평가 체계 | [AI평가체계.md](AI평가체계.md) | LangSmith 설정, 평가 지표, Harness 테스트, Prompt 관리 |
| UI 설계 | [UI설계.md](UI설계.md) | 페이지 흐름, 화면별 레이아웃, 디자인 원칙 |

---

## 7. 주요 결정사항

| 항목 | 결정 |
|---|---|
| Java Spring Boot | 제거, FastAPI로 통합 |
| 인증 Phase 1 | UI 역할 선택만, 백엔드 없음 |
| 인증 Phase 2 | 구현 여부 미정 |
| Calibration, A/B 테스트 | 미구현 |
| 고객 문의 | mailto: 링크 |
| 이미지 생성 | GPT Image 2 |
| 영상 생성 | Gemini Omni (Phase 2) |
| 비동기 큐 Phase 1 | asyncio 인메모리 |
| 비동기 큐 Phase 2 | AWS SQS |
| intent 타입 | bool |
| 동영상 URL 입력 | 제거 (파일 업로드만) |
| PDF 리포트 | Phase 1 베이스라인에 포함 |

---

## 8. 코드 작업 가이드

| 작업 | 참고 문서 |
|---|---|
| API 엔드포인트 추가/수정 | [API명세서.md](API명세서.md) |
| 시뮬레이션 Stage 구현 | [시뮬레이션.md](시뮬레이션.md) — Contract 섹션 |
| LangSmith 추적 추가 | [AI평가체계.md](AI평가체계.md) — 섹션 2 |
| Harness 테스트 작성 | [AI평가체계.md](AI평가체계.md) — 섹션 5 |
| Prompt 수정 | [AI평가체계.md](AI평가체계.md) — 섹션 6 |
| 로그인/인증 관련 | [아키텍처.md](아키텍처.md) — 섹션 5 (Phase 1: UI만) |
| 화면 구현 | [UI설계.md](UI설계.md) |
| 전체 기능 범위 확인 | [요구사항.md](요구사항.md) |
