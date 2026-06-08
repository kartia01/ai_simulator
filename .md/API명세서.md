# ClickMe API 명세서

| 버전 | v1.1 |
|---|---|
| 작성일 | 2026-06-08 |
| Base URL | `http://localhost:8000/api` (개발) |

> **Phase 1 (베이스라인)**: 인증 없이 모든 API 사용 가능. `Authorization` 헤더 불필요.  
> Auth API 전체는 `[Phase 2, 구현 여부 미정]`으로 분류된다.

---

## 공통

### 공통 응답 형식

```json
// 성공
{ "data": {...}, "message": "ok" }

// 오류
{ "detail": "error message" }
```

### 공통 헤더 (Phase 2 이후)
```
Authorization: Bearer {accessToken}
Content-Type: application/json
```

---

## 1. 인증 [Phase 2, 구현 여부 미정]

> Phase 1에서는 아래 엔드포인트들이 존재하지 않거나 동작하지 않는다.

### POST /auth/register
회원 가입

**Request**
```json
{
  "email": "user@example.com",
  "password": "password123",
  "name": "홍길동"
}
```

**Response** `201`
```json
{
  "user_id": "uuid",
  "email": "user@example.com",
  "name": "홍길동",
  "role": "user"
}
```

---

### POST /auth/login
로그인

**Request**
```json
{ "email": "user@example.com", "password": "password123" }
```

**Response** `200`
```json
{
  "access_token": "eyJ...",
  "refresh_token": "eyJ...",
  "token_type": "bearer",
  "user": { "user_id": "uuid", "email": "...", "role": "user" }
}
```

---

### POST /auth/refresh
토큰 갱신 (Token Rotation: Access + Refresh 동시 재발급)

---

### POST /auth/logout
로그아웃 (Refresh Token 무효화)

---

## 2. 시뮬레이션

### POST /simulations
새 시뮬레이션 생성

**Request** `multipart/form-data`
```
ad_type: "image" | "text" | "video"
file: (이미지/영상 파일, ad_type이 image/video일 때)
text_content: JSON string (ad_type이 text일 때)
  {
    "headline": "...",
    "sub_headline": "...",
    "body": "...",
    "cta": "...",
    "target_url": "..."
  }
persona_count: 20  (선택, 기본 20)
objective: "awareness" | "conversion"  (선택, 기본 "conversion")
```

**Response** `202`
```json
{
  "simulation_id": "sim_abc123",
  "status": "pending",
  "created_at": "2026-06-08T12:00:00Z"
}
```

---

### GET /simulations/{simulation_id}/stream
SSE 실시간 진행률 스트리밍

**Response** `text/event-stream`
```
data: {"event":"stage_complete","stage":"ad_analysis","durationMs":1240}
data: {"event":"progress","stage":"reaction_sim","completed":5,"total":20,"percent":25}
data: {"event":"completed","simulation_id":"sim_abc123"}
```

---

### GET /simulations/{simulation_id}
시뮬레이션 결과 조회

**Response** `200`
```json
{
  "simulation_id": "sim_abc123",
  "status": "completed",
  "ad_analysis": { "confidence": 0.92, "text_analysis": {...}, "strategic_analysis": {...} },
  "persona_count": 20,
  "kpi": {
    "ctr": 0.42,
    "cvr": 0.18,
    "audience_fit": 0.75,
    "trust_score": 0.68,
    "rejection_rate": 0.12,
    "net_sentiment": 0.34
  },
  "funnel": { "attention": 0.78, "comprehension": 0.65, "click": 0.42, "conversion": 0.18 },
  "improvement_report": {
    "issues": [{ "severity": "HIGH", "issue": "...", "suggested_action": "..." }],
    "copy_suggestions": ["...", "...", "..."],
    "cta_suggestions": ["..."]
  },
  "created_at": "2026-06-08T12:00:00Z",
  "completed_at": "2026-06-08T12:00:52Z"
}
```

---

### GET /simulations
시뮬레이션 목록 조회

**Query Parameters**
```
page: 1
page_size: 20
status: "pending" | "running" | "completed" | "failed"
```

---

### GET /simulations/{simulation_id}/report/pdf
PDF 리포트 다운로드

**Response** `application/pdf`

---

## 3. 광고

### POST /ads
광고 업로드 (시뮬레이션 없이 저장만)

**Request** `multipart/form-data`
```
file: 광고 파일
type: "image" | "video"
title: "광고 제목"
```

**Response** `201`
```json
{ "ad_id": "ad_abc123", "storage_url": "https://s3.../...", "type": "image" }
```

---

### GET /ads
광고 목록

---

### DELETE /ads/{ad_id}
광고 삭제

---

## 4. 채팅

### POST /chat/sessions
새 채팅 세션 생성

**Response** `201`
```json
{ "session_id": "sess_abc123", "created_at": "..." }
```

---

### POST /chat/sessions/{session_id}/messages
메시지 전송 (스트리밍)

**Request**
```json
{
  "content": "이 광고의 CTR을 높이려면 어떻게 해야 하나요?",
  "simulation_id": "sim_abc123"  // 선택, 시뮬레이션 결과 컨텍스트 활용
}
```

**Response** `text/event-stream`
```
data: {"delta": "CTA 문구를"}
data: {"delta": " 더 구체적으로"}
data: {"delta": " 바꾸는 것이 효과적입니다."}
data: {"done": true}
```

---

### GET /chat/sessions
채팅 세션 목록

---

### GET /chat/sessions/{session_id}/messages
채팅 메시지 목록

---

## 5. 광고 생성 [Phase 2, 7/8 목표]

### POST /generate/image
이미지 광고 생성 (GPT Image 2)

**Request**
```json
{ "prompt": "스포츠 음료 광고, 역동적인 느낌", "size": "1024x1024" }
```

**Response** `200`
```json
{ "generated_ad_id": "gen_abc123", "output_url": "https://s3.../...", "type": "image" }
```

---

### POST /generate/video
영상 광고 생성 (Gemini Omni) [Phase 2]

---

## 6. 프로젝트

### POST /projects
프로젝트 생성

**Request**
```json
{ "name": "2026 여름 캠페인", "description": "..." }
```

---

### GET /projects
프로젝트 목록

---

### GET /projects/{project_id}
프로젝트 상세

---

### DELETE /projects/{project_id}
프로젝트 삭제

---

## 7. 관리자 [Admin 권한]

### GET /admin/users
전체 사용자 목록

---

### DELETE /admin/users/{user_id}
사용자 삭제

---

### GET /admin/stats
전체 사용량 통계

**Response** `200`
```json
{
  "total_users": 42,
  "total_simulations": 318,
  "active_simulations": 3,
  "total_llm_cost_usd": 12.45
}
```

---

### GET /admin/chats
모든 사용자 채팅 기록 열람

---

## 8. 헬스체크

### GET /health
서버 상태 확인

**Response** `200`
```json
{ "status": "ok", "version": "1.1.0" }
```
