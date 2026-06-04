# AdMind — 광고분석 인터페이스 명세서
### Simulator → Analyzer → Chat Agent 데이터 계약

| 항목 | 내용 |
|---|---|
| 문서 종류 | 인터페이스 명세서 / 데이터 계약서 (I/O Spec) |
| 버전 | **v1.4** |
| 작성일 | 2026-06-04 |
| 대상 발표 | 2026-07-14 |
| 상태 | 합의 전(draft) — 관련 owner 합의 후 `confirmed`로 변경 |

**변경 이력**
- v1.0 → v1.1: 파이프라인 책임 경계 추가 / `producer_id` 필드 추가 / 필드 타입·범위·null 규칙 강화 / 점수 채점 기준(Rubric) 추가 / 협업 방식 추가
- v1.1 → v1.2: **설계 원칙 3(임계값은 분석기가 소유) 추가** / **7장(필드 타입 & 임계값 소유권) 신설** / intent 타입 근거·마이그레이션 경로 명시 / 일부 장 번호·상호참조 정리
- v1.2 → v1.3: **페르소나 모집단 메타(`persona_set`, 3-C) 추가** / **정직한 표본 집계 규칙(요청 수 vs 수신 수) 추가** / **7-7(표본 수 N의 한계 — 분산 vs 편향, under-dispersion) 추가** / 가중(post-stratification) 명시
- v1.3 → v1.4: **12장(설계 근거 / References) 추가** — 본문에서 인용한 논문·자료 출처와 링크 정리

---

## 0. 이 문서를 읽는 사람에게

**왜 있나.** AdMind는 6명이 도메인을 나눠 개발한다. 도메인 사이의 경계가 곧 API 계약이고, 여기서 데이터 모양·의미가 어긋나면 두 도메인이 서로 묶여 나중에 고치기 어렵다. 이 문서는 **코드를 쓰기 전에** 그 경계를 못 박기 위한 것이다.

**누가 읽나.**
- 시뮬레이터 담당(4인) — 이 계약대로 **출력**해야 한다.
- 분석기 담당(1인) — 이 계약대로 **입력 받고**, 분석 결과를 **출력**한다.
- 채팅 agent 담당 — 분석기 **출력**을 소비한다.

**읽고 나서 할 일.** 자기 도메인이 생산/소비하는 필드를 확인하고, 의미·타입·범위에 이견이 있으면 **11장 TODO에 코멘트**를 남긴다. 합의되면 상태를 `confirmed`로 올린다.

---

## 1. 파이프라인과 책임 경계

```
[시뮬레이터 (4인)] --(페르소나 반응)--> [분석기 (1인)] --(분석 결과)--> [채팅 agent]
                                            ↑
                                  (캠페인 컨텍스트: 설정/요청)
```

| 역할 | 담당 | 생산(Produce) | 소비(Consume) |
|---|---|---|---|
| 시뮬레이터 | ___ (4인) | 페르소나 반응 (3장) | 캠페인 설정 |
| 분석기 | ___ (개발자A) | 분석 결과 (4장) | 페르소나 반응 + 캠페인 컨텍스트 |
| 채팅 agent | ___ | 사용자 대화·추천 | 분석 결과 |

**계약 소유권 (중요).** 입력 계약(3장)은 **소비자인 분석기 도메인이 소유**한다(소비자 주도 계약). 즉 "분석에 무엇이 필요한가"가 기준이며, 시뮬레이터 출력은 이 정의에 맞춘다. 계약이 생산자 편의대로 정해지면 분석 품질이 무너지기 때문이다. 변경은 **9장** 절차를 따른다.

---

## 2. 설계 대원칙

**원칙 1 — 마케팅 KPI를 시뮬레이터가 직접 출력하지 않는다.**
시뮬레이터는 *사람의 반응(signal)* 만 만들고, KPI(CTR·CVR·ROAS)는 분석기가 계산한다.
근거: LLM 페르소나에게 "CTR 몇 %?"를 물으면 환각으로 지어낸다. 실제로 LLM에 숫자 평점을 직접 요청하면 중간값으로 쏠린 비현실적 분포가 나온다는 실험 결과가 있다(SSR 논문, Maier et al. 2025). 그래서 의향만 모으고 `CTR = (클릭 신호) / (전체 페르소나 수)` 로 분석기가 산출한다 → 재현 가능 + 설명 가능.

**원칙 2 — 신호(signal)와 지표(metric)를 분리한다.**

| 층 | 정의 | 생산 | 소비 |
|---|---|---|---|
| 신호 (signal) | 페르소나가 만드는 원자료 | 시뮬레이터 | 분석기 |
| 지표 (metric) | 신호를 집계·가공한 결과 | 분석기 | 고객 / 채팅 agent |

**원칙 3 — 임계값(threshold) 결정은 분석기가 소유하고, 최대한 늦게 한다.**
시뮬레이터는 신호를 가능한 한 가공 없이(raw) 넘기고, "클릭으로 칠지 말지" 같은 컷오프 판단은 소비자인 분석기에서 내린다. 생산자가 미리 yes/no로 깎아 보내면 분석기는 그 그래디언트(확신의 정도)를 **영영 복구할 수 없다(일방통행)**. 구체적 적용은 **7장** 참조.

---

## 3. 입력 명세 — 분석기 입력

### 3-A. 페르소나 반응 (시뮬레이터 출력, 반응 1건 = 페르소나 1명)

우선순위는 **퍼널 순서**를 따른다(앞이 막히면 뒤는 무의미). 이 순서는 광고학의 hierarchy-of-effects(인지→감정→행동의향) 시퀀스와 일치한다.

| 필드 | 의미 | 타입 / 범위 | 우선순위 | 필수 |
|---|---|---|---|---|
| `producer_id` | 이 반응을 만든 시뮬레이터 모듈 식별자 | string | P0 | ✅ |
| `persona_id` | 페르소나 식별자 | string | P0 | ✅ |
| `segment` | 세그먼트(예: `30s_female_urban`) | string(enum) | P0 | ✅ |
| `attention` | 주목도 | float 0.0~1.0 | P0 | ✅ |
| `sentiment` | 호감 | float −1.0~1.0 | P0 | ✅ |
| `click_intent` | 클릭 의향 → CTR 재료 | **bool (MVP, 7장 참조)** | P0 | ✅ |
| `conversion_intent` | 전환·구매 의향 → CVR 재료 | **bool (MVP, 7장 참조)** | P0 | ✅ |
| `comprehension` | 메시지 이해도 | float 0.0~1.0 | P1 | 권장 |
| `reasoning` | 그렇게 반응한 이유(텍스트) | string | P1 | 권장 |
| `recall` | 브랜드 기억 가능성 → 브랜드 리프트 | float 0.0~1.0 | P1 | 권장 |
| `emotions` | 감정 태그 | string[] | P2 | 선택 |
| `confidence` | 시뮬레이터의 반응 확신도 | float 0.0~1.0 | P2 | 선택 |

> `producer_id`는 v1.1에서 추가됐다. 시뮬레이터를 4명이 나눠 만들기 때문에, 어느 모듈이 만든 반응인지 표기하면 데이터 이상이 생겼을 때 추적·수정 위치를 즉시 알 수 있다.
> `click_intent`/`conversion_intent`의 타입(bool vs float/Likert)은 **7장에서 별도로 다룬다.** 현재는 MVP로 bool이며, 마이그레이션 경로가 정해져 있다.

### 3-B. 캠페인 컨텍스트 (설정/요청 출력)

| 필드 | 의미 | 타입 | 우선순위 | 필수 |
|---|---|---|---|---|
| `creative_id` / `variant_id` | 광고·변형 식별 | string | P0 | ✅ |
| `channel` | 노출 지면 | string(enum) | P0 | ✅ |
| `objective` | 캠페인 목적 | enum: `awareness`\|`conversion` | P0 | ✅ |
| `budget` | 예산 | number | P1 | 조건부 |
| `unit_price` / `margin` | 단가·마진 | number | P1 | 조건부 |
| `baseline` | 비교 벤치마크 | object | P1 | 권장 |

> `objective`에 따라 1등 지표가 바뀐다. `awareness`면 attention·recall, `conversion`이면 conversion_intent에 가중. 분석기는 이 값으로 종합 점수 가중치를 정한다. 비용 지표(ROAS·CPA)는 `budget`·`unit_price`가 들어온 경우에만 출력된다.

### 3-C. 페르소나 모집단 메타 (`persona_set`)

AdMind는 페르소나 1개가 아니라 **다수를 병렬로 돌려** 결과를 집계한다. 따라서 집계 결과의 타당성은 "어떤 페르소나를 몇 명, 어떤 비율로 돌렸나"에 달린다. 시뮬레이션 실행 1회마다 모집단 구성을 함께 전달한다.

| 필드 | 의미 | 타입 | 우선순위 | 필수 |
|---|---|---|---|---|
| `persona_set.id` | 페르소나 셋 버전 식별자 | string | P0 | ✅ |
| `persona_set.size` | 의도한 페르소나 수(= 요청 수) | int | P0 | ✅ |
| `persona_set.composition` | 세그먼트별 비율(예: `{"30s_female_urban":0.2, ...}`) | object | P1 | 권장 |

> **가중(post-stratification).** `composition`이 실제 타깃 인구 비율과 다르면, 분석기는 세그먼트별 결과를 실제 비율로 **재가중**해 전체 CTR·CVR을 보정한다. 가중하지 않으면 "많이 뽑힌 세그먼트"가 전체 수치를 끌고 간다. `composition`이 없으면 단순 평균(가중 없음)으로 처리하고, 그 사실을 출력에 표시한다.

---

## 4. 출력 명세 — 분석기 출력 (→ 채팅 agent)

| 필드 | 의미 | 우선순위 | 필수 |
|---|---|---|---|
| `ctr` | 예측 클릭률 | P0 | ✅ |
| `cvr` | 예측 전환율 | P0 | ✅ |
| `net_sentiment` | 순호감 / 감정 분포 | P0 | ✅ |
| `by_segment` | 세그먼트별 성과표 | P0 | ✅ |
| `effectiveness_score` | 종합 효과 점수(objective 가중) | P0 | ✅ |
| `funnel` | 단계별 이탈률 | P1 | 권장 |
| `top_drivers` | 핵심 긍정 동인 | P1 | 권장 |
| `top_objections` | 핵심 반대 사유 | P1 | 권장 |
| `variant_comparison` | 변형 비교 + 승자 | P1 | 권장 |
| `cost_metrics`(ROAS/CPA) | 비용 지표 | P1 | 조건부 |
| `recommendation` | 추천 액션 | P2 | 선택 |
| `confidence` | 예측 신뢰도(불확실성·신뢰구간) | P2 | 권장 |
| `requested_count` / `received_count` | 요청한 페르소나 수 / 실제 수신·검증 통과 수 | P1 | 권장 |
| `sample_size` | 집계에 실제 사용된 반응 수(= `received_count`) | P0 | ✅ |

> **책임 분리.** 분석기는 *구조화된 사실*만 낸다. `top_objections` 같은 사실을 사람 말 추천으로 바꾸는 건 채팅 agent의 일이다. `recommendation`을 분석기 출력에서 P2로 둔 이유다.
> **불확실성 보고.** 페르소나를 많이 돌려도 점 추정만 내지 않는다. `sample_size`와 `confidence`(신뢰구간 등)를 함께 내야 한다. 이유는 7-7 참조.

---

## 5. 데이터 계약 예시 (JSON)

### 입력: 페르소나 반응 1건 (현재 MVP, intent=bool)
```json
{
  "schema_version": "1.2",
  "creative_id": "ad_001",
  "variant_id": "A",
  "objective": "conversion",
  "producer_id": "sim_persona_genz",
  "persona_id": "p_1023",
  "segment": "30s_female_urban",
  "signals": {
    "attention": 0.8,
    "comprehension": 0.6,
    "sentiment": 0.3,
    "click_intent": true,
    "conversion_intent": false,
    "recall": 0.5
  },
  "reasoning": "혜택은 끌리는데 가격이 안 보여서 망설여짐",
  "confidence": 0.7
}
```

### 출력: 분석 결과
```json
{
  "schema_version": "1.2",
  "creative_id": "ad_001",
  "requested_count": 200,
  "received_count": 188,
  "sample_size": 188,
  "kpi": { "ctr": 0.32, "cvr": 0.11, "net_sentiment": 0.24 },
  "funnel": { "attention": 0.81, "comprehension": 0.55, "click": 0.32, "conversion": 0.11 },
  "by_segment": [
    { "segment": "30s_female_urban", "ctr": 0.41, "cvr": 0.18 }
  ],
  "top_drivers": ["혜택 강조 카피"],
  "top_objections": ["가격 미표기", "CTA 약함"],
  "effectiveness_score": 0.58,
  "cost_metrics": null
}
```

---

## 6. 필드 규칙 / 검증

계약을 안정적으로 유지하기 위한 공통 규칙이다.

1. **타입·범위 엄수.** P0 필드는 위 표의 타입·범위를 반드시 따른다. `0.0~1.0` 범위 필드에 범위 밖 값이나 `null`을 넣지 않는다.
2. **입력 검증(양쪽).** 시뮬레이터는 출력 전 자체 검증한다. 분석기는 입구에서 스키마를 한 번 더 검증하고, 계약을 위반한 데이터는 **명확한 에러로 거부**하며 `producer_id`와 함께 로그한다. — 누구를 탓하기 위함이 아니라, 문제를 **빠르고 정확한 위치**에서 잡기 위함이다. (Python: Pydantic / JSON Schema 권장)
3. **버저닝.** 모든 메시지에 `schema_version`을 포함한다. 필드 규칙: **추가는 자유, 삭제·의미 변경은 버전업.** 의미를 조용히 바꾸지 않는다.
4. **enum 고정.** `segment`, `channel`, `objective`, `emotions` 값은 합의된 목록(11장 TODO에서 확정)만 사용한다. 임의 문자열 금지.
5. **정직한 표본 집계.** 다수 페르소나를 병렬로 돌리므로, 분석기는 요청한 수(`requested_count`)와 실제 수신·검증 통과한 수(`received_count`)를 구분해 기록하고, 모든 비율은 `received_count` 기준으로 계산한다. 일부 호출이 실패해 **조용히 잘린 표본**으로 비율을 내지 않는다(예: 200개 요청 중 188개만 도착하면 `sample_size = 188`).

---

## 7. 필드 타입 & 임계값 소유권 (설계 결정)

`click_intent`·`conversion_intent`를 **어떤 타입으로 받을지**는 KPI 품질에 직접 영향을 주는 결정이라 따로 기록한다.

### 7-1. 선택지 비교

| 타입 | CTR 산출 방식 | 장점 | 약점 |
|---|---|---|---|
| `bool` (현재 MVP) | true 비율 = `mean(true)` | 단순·안정·설명 쉬움, 이진 실제 사건과 1:1 | 확신 그래디언트 소실(일방통행) |
| `float 0.0~1.0` | 임계값 θ 컷 후 비율, 또는 확률 합 / N(기대 클릭률) | 그래디언트 보존, 민감도 분석 가능 | LLM에 숫자 직접 요청 시 보정 안 됨(SSR가 지적한 함정) |
| `Likert 1~5` + 매핑 | **top-2-box 비율**(시장조사 표준 기법) | SSR 논문과 정합, 불확실성 보존 | 매핑·보정 단계 필요 |

### 7-2. 현재 결정: bool (MVP)

채택 이유:
1. **KPI와 1:1 매핑.** CTR·CVR은 본질적으로 "클릭함/안 함"이라는 이진 사건의 비율이다. yes/no를 받으면 중간 변환 없이 곧장 비율로 떨어진다.
2. **거친 신호일수록 안정적.** yes/no는 "0~1 확률"보다 LLM이 크게 틀리기 어렵다.
3. **집계가 단순.** true만 세면 된다.

### 7-3. 알려진 트레이드오프 (반드시 인지)

bool은 확신의 정도를 버린다. 클릭 확률 55%인 페르소나와 95%인 페르소나가 똑같이 `true`가 되고, **한번 버린 그래디언트는 분석기에서 복구할 수 없다(일방통행).** 이는 "불확실성을 분포로 보존하라"는 SSR 논문(Maier et al. 2025)의 권고와 상충한다. 따라서 bool은 **속도를 위한 MVP 선택**이며, 아래 마이그레이션 경로를 열어 둔다.

### 7-4. 비대칭 해명 (attention은 float인데 intent는 bool인 이유)

- `attention`·`comprehension`·`sentiment`·`recall` = 본질적으로 **연속적인 지각·감정 상태** → float가 자연스럽다.
- `click_intent`·`conversion_intent` = **이진 실제 사건**(클릭이 발생했나)을 모델링 → bool이 사건에 직접 매핑된다.
- 단, 신호 차원에서는 graded 포착이 더 우월함을 인정하며, 7-5 경로에 따라 전환할 수 있다.

### 7-5. 결정은 elicitation 방법에 종속 (시뮬레이터 4인과 합의 필요)

타입은 단독으로 정하지 않는다. **시뮬레이터가 페르소나 응답을 어떻게 받아내느냐**에 따라 갈린다.
- 단순 "클릭할래? 예/아니오" 프롬프트 → **bool로 충분.** float로 받아도 보정 안 된 값이라 이득 없음.
- SSR식(텍스트/Likert → 임베딩 유사도로 분포 매핑) → **Likert 1~5로 받고 분석기가 top-2-box로 CTR 산출**하는 것이 전략적으로 우월. 발표 시 논문 근거로 방어 가능.

### 7-6. 임계값·매핑 규칙은 분석기가 소유

CTR/CVR 도출 규칙(θ 값, top-box 정의)은 **분석기 도메인이 정의·문서화·버전 관리**한다. 시뮬레이터는 신호만 넘기고 컷오프에 관여하지 않는다(원칙 3).

### 7-7. 표본 수(N)에 대한 주의 — 많이 돌린다고 정확해지지 않는다

페르소나를 대량 병렬로 돌려 비율을 내면, 그래디언트는 페르소나 *사이의* 분산에서 자연스럽게 복구된다(실제 CTR이 모집단 비율인 것과 동일). 그래서 bool도 대량 집계에서는 충분히 쓸 만하다. 단, 두 가지를 혼동하면 안 된다.

- **N은 분산(variance)만 줄인다, 편향(bias)은 못 줄인다.** elicitation이 한쪽으로 쏠린 답을 만들면(7-5의 "숫자 직접 요청" 문제), N을 키울수록 *편향된 값을 더 정밀하게* 알게 될 뿐이다. 편향은 표본 수가 아니라 7-5 elicitation 방법에서 잡는다.
- **유효 표본 수 < N일 수 있다(under-dispersion).** LLM 페르소나는 실제 사람보다 응답 다양성이 낮은 경향이 있다(여러 합성표본 연구의 공통 지적). 비슷한 페르소나를 많이 돌리면 "N=200"이라는 **가짜 정밀도**가 생긴다. 따라서 점 추정만 내지 말고 `sample_size`와 불확실성(신뢰구간 등)을 함께 보고하고(4장), 페르소나가 실제로 다양하도록 모집단을 설계한다(3-C).

> 발표 대비: "페르소나를 많이 돌리니 정확하다"는 주장은 위 두 한계와 함께 제시해야 방어된다. 우리 설계는 *절대값 예측*이 아니라 *상대 비교·방향성*(A안 vs B안, 세그먼트 간 비교)에 초점을 둔다는 프레이밍을 함께 쓴다.

---

## 8. 점수 채점 기준 (Rubric) — 시뮬레이터 4인 통일

> 같은 `0.8`이 사람마다 다른 뜻이 되면 분석이 무의미해진다. 4명이 아래 기준으로 채점을 맞춘다.

| 필드 | 척도 | 기준점 |
|---|---|---|
| `attention` | 0.0~1.0 | 0.0 인지 못함 / 0.5 잠깐 시선 머묾 / 1.0 명확히 주목·인식 |
| `sentiment` | −1.0~1.0 | −1.0 강한 거부감 / 0.0 중립 / 1.0 강한 호감 |
| `comprehension` | 0.0~1.0 | 0.0 전혀 이해 못함 / 0.5 부분 이해 / 1.0 의도한 메시지 정확히 이해 |
| `recall` | 0.0~1.0 | 0.0 기억 못함 / 1.0 브랜드·메시지를 확실히 기억 |
| `click_intent` | bool | 이 노출에서 클릭·상호작용 의향 있으면 true |
| `conversion_intent` | bool | 광고가 유도하는 행동(구매·가입 등) 의향 있으면 true |
| `confidence` | 0.0~1.0 | 시뮬레이터가 이 반응에 가진 확신도(집계 시 가중·필터로 활용) |

> intent를 Likert로 전환할 경우(7-5), 위 bool 행은 5점 척도 기준점으로 교체한다(예: 1 절대 안 함 … 5 반드시 함).

---

## 9. 협업 방식 (병렬로 일하기 위한 합의)

1. **양방향 mock 제공.**
   - 분석기 담당은 계약대로 JSON을 뱉는 **가짜 시뮬레이터 출력 생성기**로 시뮬레이터 완성 전에 개발·테스트한다.
   - 동시에 **분석 결과 mock**을 채팅 agent 담당에게 제공해, 채팅 agent도 분석기 완성을 기다리지 않고 병렬로 개발한다.
2. **골든 샘플(golden sample).** 합의된 예시 입력·출력 JSON 파일 세트를 저장소에 둔다. 양쪽이 이 샘플로 자기 코드를 검증한다.
3. **계약 변경 절차.** 변경 제안 → 영향받는 도메인 owner 합의 → `schema_version` 올림 → 골든 샘플·mock 갱신. 구두 변경 금지.

---

## 10. 보안 · 성능 메모

- **보안.** 페르소나는 합성 데이터라 PII 위험은 낮으나, `budget`·`targeting`·`creative`는 **고객사 기밀**이다. 도메인 경계를 넘으므로 평문 로그 금지, 접근 범위 최소화.
- **성능.** `reasoning` 텍스트를 집계 payload에 전부 끌고 다니지 않는다. 점수(숫자)만 빠르게 집계하고, 텍스트는 `persona_id` 키로 별도 저장해 필요 시 조회한다.

---

## 11. 미해결 / 다음 합의 (TODO)

| # | 항목 | 담당 | 기한 | 비고 |
|---|---|---|---|---|
| 1 | `effectiveness_score` 산식 (objective별 가중치) | 분석기 | | **분석기의 핵심 로직** |
| 2 | intent 응답 elicitation 방법 + 최종 타입(bool / Likert) 확정 | 시뮬레이터 + 분석기 | | **7-5 결정 필요** |
| 3 | `segment` enum 목록 확정 | | | 누가 정의·어디까지 쪼개나 |
| 4 | `channel` / `emotions` enum 목록 확정 | | | |
| 5 | `baseline` 출처(어떤 벤치마크와 비교) | | | |
| 6 | 골든 샘플 1차 세트 작성 | 분석기 + 시뮬레이터 | | 9장 |
| 7 | 페르소나 모집단 설계(수·세그먼트 비율) + 가중(post-stratification) 방식 확정 | 시뮬레이터 + 분석기 | | 3-C, 7-7 |

---

## 12. 설계 근거 / References

본문 설계 결정을 뒷받침하는 출처. 발표 Q&A 대비용으로 "어떤 결정을 뒷받침하는가"를 함께 표기한다. (원전이 유료/구간행물인 경우 정식 공개본 링크를 우선했다.)

### 기둥 1 — LLM 페르소나로 소비자 반응을 시뮬레이션하는 것의 타당성 (시뮬레이터 존재 근거 / 원칙 1·2)

- **Maier, B. F., et al. (2025).** *LLMs Reproduce Human Purchase Intent via Semantic Similarity Elicitation of Likert Ratings.* PyMC Labs & Colgate-Palmolive. arXiv:2510.08338.
  - 논문: https://arxiv.org/abs/2510.08338
  - 구현 코드: https://github.com/pymc-labs/semantic-similarity-rating
  - → **이 프로젝트와 가장 가까운 키스톤.** 합성 소비자로 구매의향을 재현(사람 재검사 신뢰도의 약 90%). 특히 "숫자를 직접 물으면 분포가 쏠린다"는 발견이 **원칙 1과 7장(타입·elicitation)**의 직접 근거.
- **Argyle, L. P., et al. (2023).** *Out of One, Many: Using Language Models to Simulate Human Samples.* Political Analysis, 31(3), 337–351. DOI:10.1017/pan.2023.2.
  - arXiv: https://arxiv.org/abs/2209.06899
  - 게재본: https://www.cambridge.org/core/journals/political-analysis/article/out-of-one-many-using-language-models-to-simulate-human-samples/035D7C8A55B237942FB6DBAD7CAA4E49
  - → "silicon sample"·algorithmic fidelity 개념의 원조. **인구통계 조건부 페르소나(segment, 3-C)**의 이론적 근거이자, 개별이 아니라 **집계 수준에서 근사**된다는 점(7-7)의 출처.
- **Sarstedt, M., et al. (2024).** *Using large language models to generate silicon samples in consumer and marketing research.* Psychology & Marketing.
  - https://onlinelibrary.wiley.com/doi/10.1002/mar.21982
  - → 마케팅 연구에서 합성표본 사용의 기회·한계·가이드라인. 방법론 정당화 인용.

### 기둥 2 — 지표 선택과 퍼널 순서 (3-A 우선순위 / 8장 Rubric)

- **Lavidge, R. J., & Steiner, G. A. (1961).** *A Model for Predictive Measurements of Advertising Effectiveness.* Journal of Marketing, 25(6), 59–62. DOI:10.1177/002224296102500611.
  - https://journals.sagepub.com/doi/10.1177/002224296102500611
  - → hierarchy-of-effects의 정전. **인지(attention·comprehension) → 감정(sentiment) → 행동의향(intent)** 퍼널 순서의 출처.
- **Wijaya, B. S. (2012).** *The Development of Hierarchy of Effects Model in Advertising.* International Research Journal of Business Studies, 5(1), 73–85.
  - https://doaj.org/article/4ff22924ec0d4e20ac9a24b7eb34ba35
  - → AIDA부터 현대 모델까지 hierarchy 계열 정리(공개본). 퍼널 구조 보조 근거.
- **(보조) ARF/MSI Report (20-139).** *Is There a Hierarchy of Effects in Advertising? Empirical …*
  - https://thearf-org-unified-admin.s3.amazonaws.com/MSI/2020/12/MSI_Report_20-139.pdf
  - → "attention, comprehension, attitude, intention, purchase" 반응 시퀀스를 명시. 3-A 필드 순서와 거의 1:1 대응.

### 기둥 3 — 의향(intent)에서 행동·KPI를 도출하는 것의 근거 (3-A intent → 4장 CTR/CVR)

- **Morwitz, V. G., Steckel, J. H., & Gupta, A. (2007).** *When do purchase intentions predict sales?* International Journal of Forecasting.
  - https://www.sciencedirect.com/science/article/abs/pii/S0169207007000799
  - → 구매의향이 실제 판매를 예측하되 **조건에 따라 다르고 완벽하지 않다**는 점. 우리 한계 인정(7-7) 근거.
- **Ajzen, I. (1991).** *The Theory of Planned Behavior.* Organizational Behavior and Human Decision Processes, 50(2), 179–211. DOI:10.1016/0749-5978(91)90020-T.
  - → 의향이 행동의 핵심 선행변수라는 이론적 토대(원전 인용).
- **(보조, 메타분석 근거)** TPB가 의향·행동 분산의 27~39%를 설명한다는 Armitage & Conner 메타분석을 정리한 공개 논문:
  - https://pmc.ncbi.nlm.nih.gov/articles/PMC12098389/

### 한계 / 반론 (발표 시 함께 제시 — 7-7 프레이밍)

- **Bisbee, J., et al. (2024).** *Synthetic Replacements for Human Survey Data? The Perils of Large Language Models.* Political Analysis.
  - https://www.cambridge.org/core/journals/political-analysis/article/synthetic-replacements-for-human-survey-data-the-perils-of-large-language-models/B92267DC26195C7F36E63EA04A47D2FE
  - → 합성표본이 인간 응답과 유의하게 어긋날 수 있다는 경고(편향 문제).
- **Verasight (2026).** *Can Large Language Models Replicate Survey Data Across Topics?* (산업 리포트)
  - https://www.verasight.io/reports/synthetic-omnibus-survey
  - → 강한 인구통계 상관이 없는 주제의 시장조사에서는 합성표본을 신중히 쓰라는 권고.

> **인용 원칙.** 위 출처는 *우리 설계의 방향성*을 뒷받침하는 것이지, AdMind 수치의 정확성을 보증하지 않는다. 발표에서는 "절대값 예측이 아니라 상대 비교에 쓴다 + 실제 캠페인 데이터로 보정(calibration) 예정"이라는 프레이밍과 함께 인용한다.
