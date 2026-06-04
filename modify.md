# AdMind 시뮬레이터 수정 사항 목록

> 기준 문서: `AdMind_광고분석_IO명세서_v1.4.md`, `Input.md`

---

## 1. 페르소나 데이터 — null 필드 채우기 (즉시)

현재 DB의 5개 페르소나 전부 아래 3개 필드가 `null`이다.
`prompts.py`의 시스템 프롬프트가 이 필드들을 직접 참조하기 때문에
null이면 AI가 감정도, 플랫폼도, 관심 키워드도 모른 채 시뮬레이션한다.

| 필드 | 문제 | 채워야 할 값 예시 |
|---|---|---|
| `emotional_state` | 프롬프트에서 두 번 참조. null이면 감정 없는 로봇 반응 | "피곤함", "기분 좋음", "편안함", "무료함" |
| `platform` | `PLATFORM_BEHAVIOR` 분기 불가 → 항상 default(generic) | "인스타그램", "유튜브", "틱톡", "네이버" |
| `value_keywords` | Eye-catchers 항목이 비어서 AI가 무엇에 멈추는지 모름 | "가성비,무료배송,할인,스펙" |

**수정 방법:** Supabase에서 직접 업데이트 또는 `personas.json` 재삽입

---

## 2. 페르소나 엔티티 — IO Spec + Input.md 필드 추가

### 2-1. 즉시 추가 (시뮬레이션 품질에 직접 영향)

| 필드 | 타입 | 이유 |
|---|---|---|
| `segment` | string enum | IO Spec P0 필수. 분석기 세그먼트별 집계에 필요 |
| `pain_points` | string[] | `sentiment` 계산 근거. "광고가 내 결핍을 건드리는가" |
| `interest_keywords` | string[] | `attention` 계산 근거. 광고 내용과 관심사 매칭 |
| `price_threshold` | int (원) | `conversion_intent` 판단 기준. 없으면 AI가 임의로 결정 |

### 2-2. 이후 추가 (분석 고도화 단계)

| 필드 | 타입 | 이유 |
|---|---|---|
| `brand_loyalty` | float 0.0~1.0 | `recall`, `conversion_intent` 정확도 향상 |
| `media_preferences` | map(string→float) | 단일 platform → 플랫폼별 선호도 점수로 확장 |
| `active_time_windows` | string[] | 광고 노출 시각과 활성 시간대 비교 |

### 2-3. 페르소나별 권장 값

```json
[
  {
    "id": "01641cd0-7048-4c32-ac6b-aebad6d77d31",
    "name": "주부 박지영",
    "segment": "30s_female_homemaker",
    "emotional_state": "편안함",
    "platform": "네이버",
    "value_keywords": "안전인증,무료배송,후기많음,유아용,국내산",
    "pain_points": ["아이에게 안전한 제품 찾기 어려움", "배송비가 아깝다", "후기 없으면 믿기 어려움"],
    "interest_keywords": ["육아", "유아용품", "살림", "안전", "국내산", "요리"],
    "price_threshold": 50000,
    "brand_loyalty": 0.65,
    "media_preferences": {"naver_shopping": 0.9, "kakao": 0.7, "youtube": 0.5, "instagram": 0.3},
    "active_time_windows": ["13:00-15:00", "21:00-23:00"]
  },
  {
    "id": "2243f688-371f-42a3-bc50-a2ed5e4652bd",
    "name": "프리랜서 최준호",
    "segment": "30s_male_creative",
    "emotional_state": "집중 중 (약간 피로)",
    "platform": "인스타그램",
    "value_keywords": "감성적,세련됨,유니크,비주얼,디자인",
    "pain_points": ["수입 불규칙해 큰 지출이 부담", "클리셰 광고에 극도의 피로감", "작업 중 집중 방해가 짜증"],
    "interest_keywords": ["그래픽디자인", "타이포그래피", "브랜딩", "미니멀", "감성", "빈티지"],
    "price_threshold": 80000,
    "brand_loyalty": 0.25,
    "media_preferences": {"instagram": 0.9, "pinterest": 0.85, "youtube": 0.5, "behance": 0.7},
    "active_time_windows": ["12:00-13:00", "22:00-24:00"]
  },
  {
    "id": "71b63a70-06cd-4701-a41a-b1f2efd460db",
    "name": "직장인 김민준",
    "segment": "20s_male_urban",
    "emotional_state": "피곤함",
    "platform": "유튜브",
    "value_keywords": "가성비,스펙비교,가격표기,무료배송,실사용후기",
    "pain_points": ["피곤해서 광고 정보 처리 귀찮음", "가격 숨긴 광고 불신", "스펙 없이 감성만 파는 광고 거부감"],
    "interest_keywords": ["기술", "개발", "가성비", "스펙", "리뷰", "오픈소스", "생산성"],
    "price_threshold": 60000,
    "brand_loyalty": 0.15,
    "media_preferences": {"youtube": 0.75, "reddit": 0.8, "naver": 0.6, "instagram": 0.15},
    "active_time_windows": ["19:00-21:00", "23:00-01:00"]
  },
  {
    "id": "ce876523-2537-4e0d-b8e0-09661dcd0a6a",
    "name": "직장인 정다은",
    "segment": "20s_female_urban",
    "emotional_state": "기분 좋음",
    "platform": "인스타그램",
    "value_keywords": "트렌디,인스타감성,한정판,인플루언서추천,지금핫함",
    "pain_points": ["월급이 부족해 트렌드 따라가기 벅참", "너무 광고스러운 콘텐츠가 거슬림", "타겟이 나 아닌 광고는 박탈감"],
    "interest_keywords": ["패션", "뷰티", "카페", "릴스", "핫플레이스", "트렌드", "마케팅"],
    "price_threshold": 40000,
    "brand_loyalty": 0.3,
    "media_preferences": {"instagram": 0.95, "tiktok": 0.8, "youtube": 0.6, "naver": 0.25},
    "active_time_windows": ["12:00-13:00", "18:00-20:00", "22:00-24:00"]
  },
  {
    "id": "f4654409-0fe2-4128-b5d4-17ce2f4464d5",
    "name": "대학생 이수진",
    "segment": "20s_female_student",
    "emotional_state": "무료함 (집중력 저하)",
    "platform": "틱톡",
    "value_keywords": "할인,쿠폰,무료,이벤트,첫구매혜택,학생할인",
    "pain_points": ["항상 돈이 부족함", "비싼 광고 볼 때마다 박탈감", "회원가입 요구하는 광고 거부감"],
    "interest_keywords": ["할인정보", "대학생라이프", "뷰티", "카페", "자기계발", "취준"],
    "price_threshold": 15000,
    "brand_loyalty": 0.1,
    "media_preferences": {"tiktok": 0.9, "instagram": 0.8, "youtube": 0.7, "naver": 0.35},
    "active_time_windows": ["11:00-13:00", "15:00-17:00", "22:00-01:00"]
  }
]
```

---

## 3. `prompts.py` 수정

### 3-1. `build_profile_block` — 새 필드 추가

새 필드를 페르소나에 추가해도 이 함수에 반영하지 않으면 AI가 전혀 모른다.

```python
# 추가할 항목
if persona.pain_points:
    lines.append(f"  Pain points  : {', '.join(persona.pain_points)}")
if persona.interest_keywords:
    lines.append(f"  Interests    : {', '.join(persona.interest_keywords)}")
if persona.price_threshold:
    lines.append(f"  Max budget   : {persona.price_threshold:,}원")
if persona.brand_loyalty is not None:
    lines.append(f"  Brand loyalty: {persona.brand_loyalty} (0=무관심, 1=충성)")
```

### 3-2. Step 1 — `attention` float 출력 + 루브릭 추가

현재 `appeal_score`(int 1-5)만 출력하고 `attention`(float 0.0-1.0)이 없다.
IO Spec 8장 루브릭을 프롬프트에 명시해야 4명 모두 같은 기준으로 채점한다.

```
# 추가할 루브릭
attention 기준:
  0.0 = 광고가 있는지조차 인지 못함
  0.5 = 잠깐 시선이 머묾
  1.0 = 명확히 주목·인식

# 출력 형식 변경
{
  "emotions": ["<한국어단어1>", "<한국어단어2>", "<한국어단어3>"],
  "attention": <float 0.0-1.0>,
  "appeal_score": <integer 1-5>
}
```

### 3-3. Step 2 — `sentiment`, `comprehension`, `recall` 출력 추가

현재 `is_dropped_out`, `reason` 2개만 출력한다. IO Spec 3-A에서 요구하는
신호 3개가 완전히 누락되어 있다.

```
# 루브릭 추가
sentiment 기준: -1.0 강한 거부감 / 0.0 중립 / 1.0 강한 호감
comprehension 기준: 0.0 전혀 이해 못함 / 0.5 부분 이해 / 1.0 의도한 메시지 정확히 이해
recall 기준: 0.0 기억 못함 / 1.0 브랜드·메시지를 확실히 기억

# 출력 형식 변경
{
  "is_dropped_out": <true | false>,
  "reason": "<속마음 1~3문장>",
  "sentiment": <float -1.0~1.0>,
  "comprehension": <float 0.0~1.0>,
  "recall": <float 0.0~1.0>
}
```

### 3-4. Step 3 — `objective` 기반 분기 (가장 중요한 설계 변경)

**문제:** `price_threshold`를 무조건 Step 3에 넣으면 브랜드 인지도 광고·앱 광고·공익광고 등
모든 광고를 "지금 당장 살 것인가"로만 평가하게 된다 → 극과 극 반응 발생.

**해결:** `objective` 값에 따라 Step 3를 두 버전으로 분기한다.

```python
# objective = "awareness" 버전
STEP3_AWARENESS_PROMPT = """
이 광고가 기억에 남는가? 나중에 이 브랜드를 다시 떠올릴 것 같은가?
클릭은 콘텐츠가 궁금해서 하는 것이지, 구매 의향과는 별개다.

{
  "clicked": <true | false>,
  "conversion_intent": false,  # awareness 캠페인은 항상 false
  "action_reason": "<엄지를 움직인 단 하나의 생각>",
  "confidence": <float 0.0~1.0>
}
"""

# objective = "conversion" 버전
STEP3_CONVERSION_PROMPT = """
상품 가격: {product_price}원
내 지출 한도: {price_threshold}원

클릭할 것인가? 그리고 실제로 구매·가입까지 할 의향이 있는가?

{
  "clicked": <true | false>,
  "conversion_intent": <true | false>,
  "action_reason": "<엄지를 움직인 단 하나의 생각>",
  "confidence": <float 0.0~1.0>
}
"""
```

---

## 4. `agent.py` 수정

### 4-1. `_simulate_one` 리턴 타입 변경

```python
# 현재
CognitiveLoopResult → {persona_id, step1, step2, step3}

# 변경 후 (IO Spec 3-A 완성 신호)
PersonaReactionSignal → {
    schema_version, producer_id, creative_id, objective,
    persona_id, segment,
    attention, sentiment, click_intent, conversion_intent,  # P0
    comprehension, reasoning, recall,                        # P1
    emotions, confidence                                     # P2
}
```

### 4-2. `_fix_logic_errors` 규칙 추가

```python
# 기존 규칙 유지 + 추가
if is_dropped_out and conversion_intent:
    conversion_intent = False   # 이탈했으면 전환 의향 없음
if not clicked and conversion_intent:
    conversion_intent = False   # 클릭 없이 전환 의향 없음
if objective == "awareness":
    conversion_intent = False   # awareness 캠페인은 conversion_intent 무효
```

### 4-3. Step 1 `appeal_score` → `attention` 변환

```python
# agent.py에서 변환 처리 (프롬프트 외부에서)
attention = (appeal_score - 1) / 4  # 1→0.0, 3→0.5, 5→1.0
```

---

## 5. `schemas.py` 수정

### 5-1. `PersonaInput` 필드 추가

```python
class PersonaInput(BaseModel):
    # 기존 필드 유지
    ...
    # 추가
    segment: str
    pain_points: list[str]
    interest_keywords: list[str]
    price_threshold: int
    brand_loyalty: float = Field(ge=0.0, le=1.0, default=0.5)
    media_preferences: dict[str, float] | None = None
    active_time_windows: list[str] | None = None
```

### 5-2. 새 출력 모델 추가

```python
class PersonaReactionSignal(BaseModel):
    """IO Spec 3-A — 분석기로 전달되는 완성 신호"""
    schema_version: str = "1.4"
    producer_id: str = "sim_cognitive_loop_v2"
    creative_id: str
    objective: str

    persona_id: str
    segment: str

    # P0 필수
    attention: float        # 0.0~1.0
    sentiment: float        # -1.0~1.0
    click_intent: bool
    conversion_intent: bool

    # P1 권장
    comprehension: float | None
    reasoning: str | None
    recall: float | None

    # P2 선택
    emotions: list[str] | None
    confidence: float | None
```

---

## 6. `prompts.py` — MBTI 기반 자기중심 필터 분리

### 문제

현재 `ABSOLUTE LAWS`가 모든 페르소나를 동일한 방식으로 "이기적"으로 만든다.
MBTI와 성격을 공들여 설정해놨지만 Step 2에서 **모두 INTP처럼 행동**한다.

```
ENFJ 최준호 → 감성 울림에 반응해야 하는데 → "당장 나한테 이득인가?"로 강제
ISFJ 박지영 → 가족 안전·신뢰로 판단해야 하는데 → "당장 나한테 이득인가?"로 강제
ESFP 정다은 → 트렌드·사회적 시선으로 판단해야 하는데 → "당장 나한테 이득인가?"로 강제
INTP 김민준 → "당장 나한테 이득인가?" → 이 페르소나만 현재 설계가 맞음 ✅
```

"자기중심적"이라는 특성은 유지하되, **이기심의 기준이 MBTI마다 달라야 한다.**

### 해결 방향

#### 1) `PERSONA_FILTER_TYPE` 딕셔너리 추가

```python
# prompts.py에 추가
PERSONA_FILTER_TYPE = {
    "ISFJ": "가족·안전·신뢰 — 내 사람들에게 안전하고 믿을 수 있는가?",
    "ENFJ": "감성·울림·아름다움 — 나를 감동시키거나 영감을 주는가?",
    "INTP": "효율·스펙·가성비 — 데이터가 납득되는가?",
    "ESFP": "트렌드·사회적 시선·즐거움 — 이게 나를 더 쿨하게 만드는가?",
    "ENFP": "새로움·가치관·설렘 — 내 가치관과 공명하는가?",
    # 필요 시 추가
}

def build_filter_type(mbti: str | None) -> str:
    return PERSONA_FILTER_TYPE.get(mbti or "", "나에게 지금 당장 필요한가?")
```

#### 2) 시스템 프롬프트 `ABSOLUTE LAWS` 수정

```
# 현재 (삭제)
❌ FORBIDDEN: Being fair or objective — you are SELFISH
✅ REQUIRED: Your only question is "Does this help ME, RIGHT NOW?"

# 변경 후
❌ FORBIDDEN: Being analytical, balanced, or objective
✅ REQUIRED: Filter everything through YOUR personality.
             Your personal judgment lens: {filter_type}
             Fast. Gut. No second-guessing.
```

#### 3) `SYSTEM_PROMPT_TEMPLATE` 변수 추가

```python
# build_system_prompt() 또는 템플릿에 filter_type 변수 추가
SYSTEM_PROMPT_TEMPLATE = """
...
  Your filter lens  : {filter_type}
...
"""
```

### 기대 효과

| 페르소나 | 변경 전 Step 2 판단 | 변경 후 Step 2 판단 |
|---|---|---|
| ENFJ 최준호 | "나한테 이득 없음" | "감성적 울림이 없어서 넘김" |
| ISFJ 박지영 | "나한테 이득 없음" | "후기·안전 인증 안 보여서 믿기 어려움" |
| ESFP 정다은 | "나한테 이득 없음" | "친구한테 보여주기 창피한 비주얼" |
| INTP 김민준 | "나한테 이득 없음" | "가격·스펙 안 보임" (변화 없음) |

---

## 9. NeonDB + Spring Boot (HikariCP) 연동 설정

### 문제

NeonDB는 서버리스 PostgreSQL로, idle 연결을 강제 종료한다.
Spring Boot의 HikariCP는 커넥션 풀을 지속 유지하려 하기 때문에
설정 없이 쓰면 간헐적 `Connection closed` 에러가 발생한다.

추가로 NeonDB PgBouncer는 **Transaction 모드**로 동작하는데,
Hibernate의 기본 Prepared Statements와 충돌해
`prepared statement "S_x" already exists` 에러가 난다.

### 해결: `application.properties` 설정

```properties
# NeonDB pooler 엔드포인트 사용 (일반 엔드포인트 대신)
spring.datasource.url=jdbc:postgresql://<project>-pooler.neon.tech/neondb?sslmode=require

# HikariCP 연결 안정성
spring.datasource.hikari.connection-timeout=30000
spring.datasource.hikari.idle-timeout=600000
spring.datasource.hikari.max-lifetime=1800000
spring.datasource.hikari.keepalive-time=300000
spring.datasource.hikari.maximum-pool-size=10

# PgBouncer Transaction 모드 호환 — 필수
spring.datasource.hikari.data-source-properties.prepareThreshold=0
spring.jpa.properties.hibernate.jdbc.lob.non_contextual_creation=true
```

### 체크리스트

| 항목 | 설명 |
|---|---|
| URL에 `-pooler.neon.tech` | 일반 엔드포인트가 아닌 PgBouncer 풀링 엔드포인트 사용 |
| `sslmode=require` | NeonDB 필수 |
| HikariCP timeout 튜닝 | idle 연결 강제 종료 대응 |
| `prepareThreshold=0` | PgBouncer Transaction 모드 호환. **이게 없으면 에러 남** |

---

## 수정 우선순위 요약

| 순위 | 대상 | 내용 | 이유 |
|---|---|---|---|
| 1 | DB 페르소나 데이터 | `emotional_state`, `platform`, `value_keywords` null 채우기 | 지금 당장 시뮬레이션 결과 신뢰도에 영향 |
| 2 | `prompts.py` | `build_profile_block`에 `pain_points`, `interest_keywords`, `price_threshold` 추가 | 새 필드가 AI에게 전달되게 |
| 3 | `prompts.py` | Step 3를 `objective` 기반 두 버전으로 분기 | awareness/conversion 혼용 시 극단 반응 방지 |
| 4 | `prompts.py` | Step 2 출력에 `sentiment`, `comprehension`, `recall` 추가 + 루브릭 | IO Spec P0 신호 확보 |
| 5 | `schemas.py` | `PersonaInput` 필드 추가, `PersonaReactionSignal` 모델 생성 | 타입 안전성 |
| 6 | `agent.py` | 새 신호 처리 로직, `_fix_logic_errors` 규칙 추가 | IO Spec 완성 |
| 7 | `Persona.java` / DTO | 백엔드 엔티티·페이로드 필드 동기화 | 프론트 → FastAPI 연동 |
| 8 | `prompts.py` | `PERSONA_FILTER_TYPE` 딕셔너리 추가 + ABSOLUTE LAWS 수정 | MBTI별 자기중심 필터 분리, 획일적 반응 방지 |
