# ClickMe API 명세서

| 항목 | 내용 |
|---|---|
| 서비스명 | ClickMe |
| 버전 | v1.0 |
| 작성일 | 2026-06-04 |
| Base URL (Spring) | `https://api.clickme.io/api/v1` |
| Base URL (Python AI) | `http://ai-service:8000/api` (내부 통신) |

---

## 목차

1. [공통 규칙](#1-공통-규칙)
2. [인증 API (Spring)](#2-인증-api)
3. [사용자 API (Spring)](#3-사용자-api)
4. [조직 API (Spring)](#4-조직-api)
5. [프로젝트 API (Spring)](#5-프로젝트-api)
6. [광고 API (Spring)](#6-광고-api)
7. [시뮬레이션 API (Spring)](#7-시뮬레이션-api)
8. [채팅 API (Spring)](#8-채팅-api)
9. [리포트 API (Spring)](#9-리포트-api)
10. [광고 생성 API (Spring)](#10-광고-생성-api)
11. [관리자 API (Spring)](#11-관리자-api)
12. [Python AI 서비스 API (내부)](#12-python-ai-서비스-api-내부)
13. [SSE 이벤트 명세](#13-sse-이벤트-명세)
14. [에러 코드](#14-에러-코드)

---

## 1. 공통 규칙

### 1-1. 인증

모든 API (로그인 제외)는 요청 헤더에 JWT Access Token이 필요하다.

```
Authorization: Bearer {accessToken}
```

### 1-2. 응답 형식

**성공 응답**
```json
{
  "success": true,
  "data": { ... },
  "message": "성공 메시지 (선택)"
}
```

**실패 응답**
```json
{
  "success": false,
  "error": {
    "code": "ERROR_CODE",
    "message": "에러 메시지"
  }
}
```

### 1-3. 페이지네이션

목록 조회 API는 커서 기반 페이지네이션을 사용한다.

**요청 파라미터**
```
?limit=20&cursor={lastItemId}
```

**응답**
```json
{
  "success": true,
  "data": {
    "items": [ ... ],
    "nextCursor": "uuid-or-null",
    "hasMore": true
  }
}
```

### 1-4. 날짜 형식

모든 날짜/시간은 ISO 8601 UTC 형식 사용: `2026-06-04T12:00:00Z`

### 1-5. 버저닝

URL 경로에 버전 포함: `/api/v1/...`

---

## 2. 인증 API

### POST /auth/login

로그인 후 JWT 토큰 발급.

**Request Body**
```json
{
  "email": "user@example.com",
  "password": "password123"
}
```

**Response 200**
```json
{
  "success": true,
  "data": {
    "accessToken": "eyJhbGci...",
    "refreshToken": "eyJhbGci...",
    "expiresIn": 3600,
    "user": {
      "id": "uuid",
      "email": "user@example.com",
      "name": "홍길동",
      "role": "user"
    }
  }
}
```

**Response 401** — 이메일 또는 비밀번호 불일치

---

### POST /auth/logout

로그아웃 및 Refresh Token 무효화.

**Request Body**
```json
{
  "refreshToken": "eyJhbGci..."
}
```

**Response 200**
```json
{ "success": true }
```

---

### POST /auth/refresh

Access Token 재발급.

**Request Body**
```json
{
  "refreshToken": "eyJhbGci..."
}
```

**Response 200**
```json
{
  "success": true,
  "data": {
    "accessToken": "eyJhbGci...",
    "expiresIn": 3600
  }
}
```

---

### GET /auth/me

현재 로그인한 사용자 정보 조회.

**Response 200**
```json
{
  "success": true,
  "data": {
    "id": "uuid",
    "email": "user@example.com",
    "name": "홍길동",
    "role": "user",
    "organizationId": "uuid"
  }
}
```

---

### PUT /auth/password

비밀번호 변경.

**Request Body**
```json
{
  "currentPassword": "oldPassword",
  "newPassword": "newPassword123"
}
```

**Response 200**
```json
{ "success": true }
```

---

## 3. 사용자 API

### GET /users

사용자 목록 조회. **Admin 전용.**

**Query Parameters**
```
?limit=20&cursor={lastId}&keyword={검색어}
```

**Response 200**
```json
{
  "success": true,
  "data": {
    "items": [
      {
        "id": "uuid",
        "email": "user@example.com",
        "name": "홍길동",
        "role": "user",
        "isActive": true,
        "lastLoginAt": "2026-06-04T10:00:00Z",
        "createdAt": "2026-01-01T00:00:00Z"
      }
    ],
    "nextCursor": null,
    "hasMore": false
  }
}
```

---

### POST /users

사용자 계정 생성. **Admin 전용.**

**Request Body**
```json
{
  "email": "newuser@example.com",
  "name": "김철수",
  "password": "initialPassword123",
  "role": "user",
  "organizationId": "uuid"
}
```

**Response 201**
```json
{
  "success": true,
  "data": {
    "id": "uuid",
    "email": "newuser@example.com",
    "name": "김철수",
    "role": "user",
    "createdAt": "2026-06-04T12:00:00Z"
  }
}
```

---

### GET /users/{userId}

특정 사용자 조회. **Admin 전용.**

**Response 200** — 사용자 상세 정보

---

### PUT /users/{userId}

사용자 정보 수정. **Admin 전용.**

**Request Body**
```json
{
  "name": "수정된 이름",
  "isActive": false
}
```

---

### DELETE /users/{userId}

사용자 계정 삭제. **Admin 전용.**

**Response 200**
```json
{ "success": true }
```

---

## 4. 조직 API

### GET /organizations/me

내 조직 정보 조회.

**Response 200**
```json
{
  "success": true,
  "data": {
    "id": "uuid",
    "name": "주식회사 예시",
    "planType": "professional",
    "memberCount": 5,
    "createdAt": "2026-01-01T00:00:00Z"
  }
}
```

---

### PUT /organizations/me

조직 정보 수정.

**Request Body**
```json
{
  "name": "수정된 회사명"
}
```

---

### GET /organizations/me/members

조직 멤버 목록 조회.

**Response 200**
```json
{
  "success": true,
  "data": {
    "items": [
      {
        "id": "uuid",
        "name": "홍길동",
        "email": "user@example.com",
        "role": "user"
      }
    ]
  }
}
```

---

## 5. 프로젝트 API

### GET /projects

내 프로젝트 목록 조회 (소속된 모든 프로젝트).

**Query Parameters**
```
?limit=20&cursor={lastId}&status=active
```

**Response 200**
```json
{
  "success": true,
  "data": {
    "items": [
      {
        "id": "uuid",
        "name": "2026 여름 캠페인",
        "description": "쿨링 셔츠 광고 캠페인",
        "status": "active",
        "adCount": 3,
        "simulationCount": 7,
        "myRole": "owner",
        "createdAt": "2026-05-01T00:00:00Z"
      }
    ],
    "nextCursor": null,
    "hasMore": false
  }
}
```

---

### POST /projects

프로젝트 생성.

**Request Body**
```json
{
  "name": "2026 여름 캠페인",
  "description": "쿨링 셔츠 광고 캠페인"
}
```

**Response 201**
```json
{
  "success": true,
  "data": {
    "id": "uuid",
    "name": "2026 여름 캠페인",
    "createdAt": "2026-06-04T12:00:00Z"
  }
}
```

---

### GET /projects/{projectId}

프로젝트 상세 조회.

**Response 200** — 프로젝트 상세 + 광고 목록 + 시뮬레이션 목록

---

### PUT /projects/{projectId}

프로젝트 수정. **Owner만.**

---

### DELETE /projects/{projectId}

프로젝트 삭제. **Owner만.**

---

### GET /projects/{projectId}/members

프로젝트 멤버 목록.

**Response 200**
```json
{
  "success": true,
  "data": {
    "items": [
      {
        "userId": "uuid",
        "name": "홍길동",
        "email": "user@example.com",
        "role": "owner",
        "joinedAt": "2026-05-01T00:00:00Z"
      }
    ]
  }
}
```

---

### POST /projects/{projectId}/members

프로젝트 멤버 추가. **Owner / Editor만. [7/8 목표]**

**Request Body**
```json
{
  "userId": "uuid",
  "role": "editor"
}
```

---

### PUT /projects/{projectId}/members/{userId}

멤버 역할 변경. **Owner만. [7/8 목표]**

**Request Body**
```json
{
  "role": "viewer"
}
```

---

### DELETE /projects/{projectId}/members/{userId}

멤버 제거. **Owner만. [7/8 목표]**

---

## 6. 광고 API

### GET /ads

광고 목록 조회.

**Query Parameters**
```
?projectId={uuid}&limit=20&cursor={lastId}&inputType=image
```

**Response 200**
```json
{
  "success": true,
  "data": {
    "items": [
      {
        "id": "uuid",
        "projectId": "uuid",
        "name": "여름 쿨링 배너",
        "inputType": "image",
        "storageUrl": "https://s3.amazonaws.com/...",
        "analysisStatus": "completed",
        "analysisConfidence": 0.92,
        "createdAt": "2026-06-01T10:00:00Z"
      }
    ]
  }
}
```

---

### POST /ads

광고 업로드.

**Request** — `multipart/form-data`

| 필드 | 타입 | 설명 |
|---|---|---|
| `projectId` | string | 프로젝트 ID |
| `name` | string | 광고 이름 |
| `inputType` | string | `image` \| `text` \| `video` \| `url` |
| `file` | File | 이미지/영상 파일 (inputType이 image/video일 때) |
| `textContent` | string | 광고 텍스트 (inputType이 text일 때) |
| `url` | string | 랜딩페이지 URL (inputType이 url일 때) |

**Response 202** — 분석 비동기 시작

```json
{
  "success": true,
  "data": {
    "id": "uuid",
    "status": "analyzing",
    "message": "광고 분석이 시작되었습니다."
  }
}
```

---

### GET /ads/{adId}

광고 상세 조회 (분석 결과 포함).

**Response 200**
```json
{
  "success": true,
  "data": {
    "id": "uuid",
    "name": "여름 쿨링 배너",
    "inputType": "image",
    "storageUrl": "https://s3.amazonaws.com/...",
    "analysisStatus": "completed",
    "analysisResult": {
      "textAnalysis": {
        "headline": "여름을 이기는 쿨링 셔츠",
        "cta": "지금 구매하기",
        "uspExtracted": ["흡습속건", "자외선 차단 UPF50+"]
      },
      "visualAnalysis": {
        "dominantColors": ["#E8F4FD", "#1976D2"],
        "emotionalTone": "cool_refreshing",
        "layoutType": "product_focus"
      },
      "strategicAnalysis": {
        "targetDemographic": "25-40 male office worker",
        "purchaseStagetarget": "consideration"
      }
    },
    "analysisConfidence": 0.92,
    "createdAt": "2026-06-01T10:00:00Z"
  }
}
```

---

### DELETE /ads/{adId}

광고 삭제.

---

## 7. 시뮬레이션 API

### POST /simulations

시뮬레이션 실행 요청.

**Request Body**
```json
{
  "adId": "uuid",
  "projectId": "uuid",
  "simulationType": "ad_reaction",
  "personaConfig": {
    "count": 20,
    "segmentDistribution": {
      "20s_male_student": 0.15,
      "30s_male_office": 0.25,
      "30s_female_working": 0.20,
      "40s_female_homemaker": 0.15,
      "50s_male_manager": 0.15,
      "20s_female_student": 0.10
    },
    "enableDebateAgent": false
  },
  "objective": "conversion"
}
```

**Response 202**
```json
{
  "success": true,
  "data": {
    "id": "uuid",
    "status": "pending",
    "estimatedSeconds": 45,
    "streamUrl": "/api/v1/simulations/{id}/stream"
  }
}
```

---

### GET /simulations/{simulationId}

시뮬레이션 상태 및 결과 조회.

**Response 200**
```json
{
  "success": true,
  "data": {
    "id": "uuid",
    "status": "completed",
    "personaCount": 20,
    "requestedCount": 20,
    "receivedCount": 19,
    "sampleSize": 19,
    "resultsSummary": {
      "kpi": {
        "ctr": 0.42,
        "cvr": 0.18,
        "netSentiment": 0.31
      },
      "funnel": {
        "attention": 0.85,
        "comprehension": 0.62,
        "click": 0.42,
        "conversion": 0.18
      },
      "effectivenessScore": 0.63,
      "topDrivers": ["혜택 강조 카피", "시각적 임팩트"],
      "topObjections": ["가격 미표기", "CTA 약함"],
      "bySegment": [
        { "segment": "30s_female_working", "ctr": 0.55, "cvr": 0.24 }
      ]
    },
    "llmCostUsd": 0.048,
    "startedAt": "2026-06-04T12:00:00Z",
    "completedAt": "2026-06-04T12:00:45Z"
  }
}
```

---

### GET /simulations/{simulationId}/stream

시뮬레이션 진행률 실시간 SSE 스트리밍.

- Content-Type: `text/event-stream`
- Spring이 Python FastAPI의 SSE를 프록시하여 클라이언트에 전달
- 자세한 이벤트 형식은 [13장 SSE 이벤트 명세](#13-sse-이벤트-명세) 참조

---

### GET /projects/{projectId}/simulations

프로젝트 내 시뮬레이션 목록.

**Query Parameters**
```
?limit=20&cursor={lastId}
```

---

## 8. 채팅 API

### GET /chat/sessions

채팅 세션 목록 조회.

**Response 200**
```json
{
  "success": true,
  "data": {
    "items": [
      {
        "id": "uuid",
        "title": "여름 쿨링 셔츠 광고 분석",
        "lastMessageAt": "2026-06-04T11:30:00Z",
        "createdAt": "2026-06-04T10:00:00Z"
      }
    ]
  }
}
```

---

### POST /chat/sessions

채팅 세션 생성.

**Request Body**
```json
{
  "projectId": "uuid",
  "title": "새 채팅"
}
```

**Response 201**
```json
{
  "success": true,
  "data": {
    "id": "uuid",
    "title": "새 채팅",
    "createdAt": "2026-06-04T12:00:00Z"
  }
}
```

---

### GET /chat/sessions/{sessionId}

채팅 세션 상세 + 메시지 목록.

**Response 200**
```json
{
  "success": true,
  "data": {
    "id": "uuid",
    "title": "여름 쿨링 셔츠 광고 분석",
    "messages": [
      {
        "id": "uuid",
        "role": "user",
        "content": "이 광고의 CTR이 좋을까요?",
        "createdAt": "2026-06-04T10:05:00Z"
      },
      {
        "id": "uuid",
        "role": "assistant",
        "content": "시뮬레이션 결과에 따르면...",
        "metadata": { "simulationId": "uuid" },
        "createdAt": "2026-06-04T10:05:10Z"
      }
    ]
  }
}
```

---

### DELETE /chat/sessions/{sessionId}

채팅 세션 삭제.

---

### POST /chat/sessions/{sessionId}/messages

메시지 전송 (스트리밍 응답).

**Request Body**
```json
{
  "content": "이 광고 카피를 개선해줘",
  "contextAdId": "uuid"
}
```

**Response** — SSE 스트리밍 (`text/event-stream`)

자세한 이벤트 형식은 [13장](#13-sse-이벤트-명세) 참조.

---

## 9. 리포트 API

### GET /reports/{reportId}

리포트 상세 조회.

**Response 200**
```json
{
  "success": true,
  "data": {
    "id": "uuid",
    "simulationId": "uuid",
    "reportData": {
      "executiveSummary": {
        "overallScore": 72,
        "verdict": "평균 이상",
        "topPriority": "가격 정보 추가 필요"
      },
      "detailedAnalysis": { ... },
      "actionItems": { ... }
    },
    "disclaimer": "본 결과는 AI 시뮬레이션 기반 예측입니다. 실제 광고 성과와 ±20~30% 오차가 있을 수 있습니다.",
    "createdAt": "2026-06-04T12:01:00Z"
  }
}
```

---

### GET /simulations/{simulationId}/report

시뮬레이션에 연결된 리포트 조회.

---

## 10. 광고 생성 API

**[7/8 목표]**

### POST /generated-ads

AI 광고 이미지 생성 요청.

**Request Body**
```json
{
  "projectId": "uuid",
  "prompt": "여름 쿨링 셔츠, 시원한 느낌, 남성 30대 타깃",
  "style": "clean_modern",
  "aspectRatio": "1:1"
}
```

**Response 202**
```json
{
  "success": true,
  "data": {
    "id": "uuid",
    "status": "generating"
  }
}
```

---

### GET /generated-ads

생성 광고 목록 조회.

**Query Parameters**
```
?projectId={uuid}&isSaved=true&limit=20&cursor={lastId}
```

---

### GET /generated-ads/{adId}

생성 광고 상세.

**Response 200**
```json
{
  "success": true,
  "data": {
    "id": "uuid",
    "imageUrl": "https://s3.amazonaws.com/...",
    "prompt": "여름 쿨링 셔츠...",
    "isSaved": false,
    "generationModel": "dall-e-3",
    "createdAt": "2026-06-04T12:00:00Z"
  }
}
```

---

### PUT /generated-ads/{adId}/save

생성 광고 보관함 저장 (UI 구현, 과금 로직 추후).

**Response 200**
```json
{
  "success": true,
  "data": { "isSaved": true }
}
```

---

### DELETE /generated-ads/{adId}

생성 광고 삭제.

---

## 11. 관리자 API

### GET /admin/stats

전체 사용량 통계. **Admin 전용.**

**Response 200**
```json
{
  "success": true,
  "data": {
    "totalUsers": 42,
    "activeUsers": 38,
    "totalSimulations": 317,
    "totalLlmCostUsd": 15.24,
    "simulationsToday": 12
  }
}
```

---

### GET /admin/users/{userId}/chat-sessions

특정 사용자 채팅 기록 열람. **Admin 전용.**

**Response 200** — 해당 사용자의 채팅 세션 목록

---

### GET /admin/chat-sessions

전체 채팅 세션 목록. **Admin 전용.**

**Query Parameters**
```
?userId={uuid}&limit=20&cursor={lastId}
```

---

## 12. Python AI 서비스 API (내부)

Spring Boot에서 내부적으로 호출하는 Python FastAPI 엔드포인트. 외부에 직접 노출하지 않는다.

**Base URL**: `http://ai-service:8000/api`

---

### POST /analyze/image

이미지 광고 분석.

**Request Body**
```json
{
  "adId": "uuid",
  "imageUrl": "https://s3.amazonaws.com/...",
  "promptVersion": "v1.0"
}
```

**Response 200**
```json
{
  "adId": "uuid",
  "confidence": 0.92,
  "textAnalysis": {
    "headline": "여름을 이기는 쿨링 셔츠",
    "cta": "지금 구매하기",
    "uspExtracted": ["흡습속건", "자외선 차단 UPF50+"],
    "emotionalKeywords": ["시원함", "자신감"]
  },
  "visualAnalysis": {
    "dominantColors": ["#E8F4FD", "#1976D2"],
    "emotionalTone": "cool_refreshing",
    "layoutType": "product_focus"
  },
  "strategicAnalysis": {
    "targetDemographic": "25-40 male office worker",
    "purchaseStageTarget": "consideration"
  }
}
```

---

### POST /analyze/text

텍스트 광고 분석.

**Request Body**
```json
{
  "adId": "uuid",
  "textContent": {
    "headline": "여름을 이기는 쿨링 셔츠",
    "body": "흡습속건 소재로 하루 종일 쾌적하게",
    "cta": "지금 구매하기"
  }
}
```

---

### POST /analyze/video

영상 광고 분석. **[7/8 목표]**

**Request Body**
```json
{
  "adId": "uuid",
  "videoUrl": "https://s3.amazonaws.com/..."
}
```

---

### POST /analyze/url

랜딩페이지 URL 분석. **[7/8 목표]**

**Request Body**
```json
{
  "adId": "uuid",
  "url": "https://example.com/product"
}
```

---

### POST /personas/generate

페르소나 생성.

**Request Body**
```json
{
  "simulationId": "uuid",
  "count": 20,
  "segmentDistribution": {
    "30s_female_urban": 0.20,
    "20s_male_student": 0.15
  },
  "adCategory": "fashion"
}
```

**Response 200**
```json
{
  "simulationId": "uuid",
  "personas": [
    {
      "personaId": "P_0001",
      "segment": "30s_female_urban",
      "attributes": { ... },
      "temperature": 0.82,
      "seed": 4829
    }
  ]
}
```

---

### POST /simulate/reactions

페르소나 반응 시뮬레이션 실행. 비동기 태스크 시작.

**Request Body**
```json
{
  "simulationId": "uuid",
  "adAnalysis": { ... },
  "personas": [ ... ],
  "objective": "conversion",
  "personaSet": {
    "id": "ps_uuid",
    "size": 20,
    "composition": { "30s_female_urban": 0.20 }
  }
}
```

**Response 202**
```json
{
  "taskId": "uuid",
  "streamUrl": "/api/simulate/uuid/stream"
}
```

---

### GET /simulate/{taskId}/stream

시뮬레이션 진행률 SSE 스트리밍 (Python 서버 측).

Spring이 이 엔드포인트를 구독하고 클라이언트에 프록시한다.

---

### POST /simulate/debate

Debate Agent 실행. **[7/8 목표]**

**Request Body**
```json
{
  "simulationId": "uuid",
  "adAnalysis": { ... },
  "positivePersoanId": "P_0001",
  "negativePersonaId": "P_0042"
}
```

**Response 200**
```json
{
  "positiveArguments": { ... },
  "counterArguments": { ... },
  "synthesis": { ... },
  "adjustedScores": {
    "clickIntentAdjustment": -8.3
  }
}
```

---

### POST /analyze/performance

성과 지표 산출.

**Request Body**
```json
{
  "simulationId": "uuid",
  "personaResponses": [ ... ],
  "debateResult": { ... },
  "objective": "conversion",
  "personaSet": { ... }
}
```

**Response 200**
```json
{
  "schemaVersion": "1.2",
  "creativeId": "uuid",
  "requestedCount": 20,
  "receivedCount": 19,
  "sampleSize": 19,
  "kpi": {
    "ctr": 0.42,
    "cvr": 0.18,
    "netSentiment": 0.31
  },
  "funnel": {
    "attention": 0.85,
    "comprehension": 0.62,
    "click": 0.42,
    "conversion": 0.18
  },
  "bySegment": [ ... ],
  "topDrivers": ["혜택 강조 카피"],
  "topObjections": ["가격 미표기", "CTA 약함"],
  "effectivenessScore": 0.63,
  "confidence": 0.78
}
```

---

### POST /recommend/improvements

광고 개선안 생성.

**Request Body**
```json
{
  "simulationId": "uuid",
  "adAnalysis": { ... },
  "performanceResult": { ... }
}
```

**Response 200**
```json
{
  "issues": [
    {
      "severity": "HIGH",
      "issue": "가격 정보 없음",
      "suggestedAction": "가격 또는 할인율 명시"
    }
  ],
  "copySuggestions": [
    "여름 최강 쿨링 — 단돈 29,900원",
    "하루 종일 시원함 보장, 무료 반품"
  ],
  "ctaSuggestions": ["지금 구매하기 →", "30일 무료 체험"],
  "nextABTestElements": ["가격 표시 여부", "CTA 문구 3가지"]
}
```

---

### POST /chat/complete

채팅 메시지 응답 생성 (SSE 스트리밍).

**Request Body**
```json
{
  "sessionId": "uuid",
  "messages": [
    { "role": "user", "content": "이 광고 어때?" }
  ],
  "contextAdId": "uuid",
  "contextSimulationId": "uuid"
}
```

**Response** — SSE 스트리밍

---

### POST /generate/ad

AI 광고 이미지 생성. **[7/8 목표]**

**Request Body**
```json
{
  "generatedAdId": "uuid",
  "prompt": "여름 쿨링 셔츠, 시원한 느낌",
  "style": "clean_modern",
  "aspectRatio": "1:1"
}
```

---

## 13. SSE 이벤트 명세

### 13-1. 시뮬레이션 진행률 이벤트

**Content-Type**: `text/event-stream`

#### 진행률 이벤트 (progress)
```
data: {"event":"progress","completed":5,"total":20,"percent":25,"latestPersona":{"age":34,"gender":"female","clickIntent":true,"sentiment":0.3}}
```

#### 중간 집계 이벤트 (milestone)
```
data: {"event":"milestone","percent":50,"interimCtr":0.38,"interimCvr":0.15}
```

#### 완료 이벤트 (completed)
```
data: {"event":"completed","simulationId":"uuid","reportUrl":"/api/v1/reports/uuid","summary":{"ctr":0.42,"cvr":0.18,"effectivenessScore":0.63}}
```

#### 에러 이벤트 (error)
```
data: {"event":"error","message":"시뮬레이션 중 오류가 발생했습니다.","code":"SIMULATION_FAILED"}
```

---

### 13-2. 채팅 스트리밍 이벤트

#### 텍스트 청크 (chunk)
```
data: {"event":"chunk","content":"시뮬레이션 결과에 따르면 "}
data: {"event":"chunk","content":"이 광고의 CTR은 "}
data: {"event":"chunk","content":"42%로 예측됩니다."}
```

#### 완료 (done)
```
data: {"event":"done","messageId":"uuid","tokensUsed":342}
```

---

## 14. 에러 코드

| 코드 | HTTP | 설명 |
|---|---|---|
| `UNAUTHORIZED` | 401 | 인증 토큰 없음 또는 만료 |
| `FORBIDDEN` | 403 | 권한 없음 |
| `NOT_FOUND` | 404 | 리소스 없음 |
| `VALIDATION_ERROR` | 400 | 요청 파라미터 유효성 오류 |
| `FILE_TOO_LARGE` | 413 | 파일 크기 초과 |
| `UNSUPPORTED_FILE_TYPE` | 415 | 지원하지 않는 파일 형식 |
| `SIMULATION_FAILED` | 500 | 시뮬레이션 실행 오류 |
| `AI_SERVICE_UNAVAILABLE` | 503 | AI 서비스 연결 불가 |
| `LLM_API_ERROR` | 502 | LLM API 호출 오류 |
| `RATE_LIMIT_EXCEEDED` | 429 | LLM API Rate Limit 초과 |
| `INTERNAL_SERVER_ERROR` | 500 | 서버 내부 오류 |
