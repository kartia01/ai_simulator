# ClickMe AI 평가 체계

| 버전 | v1.1 |
|---|---|
| 작성일 | 2026-06-08 |

---

## 1. 왜 평가 체계가 필요한가

ClickMe 시뮬레이션은 6명이 각자 다른 방식으로 구현한다. "어느 구현체가 더 좋은가"를 데이터로 증명하기 위해 추적 가능한 AI 평가 체계가 필요하다.

발표의 핵심 차별점:
- 단순히 "동작하는 AI"가 아닌, **측정하고 개선하는 AI**
- LangSmith에서 단계별 Prompt/Model/Cost/Latency 실시간 비교
- 로그 분석 → Prompt 수정 → 결과 개선 사이클 실증

---

## 2. LangSmith 설정

### 환경 변수

```bash
LANGCHAIN_TRACING_V2=true
LANGCHAIN_API_KEY=lsv2_...
LANGCHAIN_PROJECT=clickme-simulation
```

### 추적 데코레이터

```python
from langsmith import traceable

class AdAnalysisAgent:
    @traceable(name="ad_analysis", run_type="chain")
    async def run(self, input: AdInput) -> AdAnalysisResult:
        ...
```

### 추적 메타데이터

```python
metadata = {
    "simulation_id": simulation_id,
    "stage": "reaction_sim",
    "producer_id": "member_c_v2",
    "prompt_version": "v1.2",
    "model": "gpt-4o-mini",
    "persona_count": 20,
}
```

---

## 3. 단계별 추적 항목

| Stage | 추적 항목 |
|---|---|
| 광고 분석 | Input: ad URL/text, Output: JSON, Model, Latency, Cost, Confidence |
| 페르소나 생성 | Input: count+segment, Output: Persona JSON×N, Model, Latency, Cost/persona |
| 반응 시뮬레이션 | Input: ad+persona, Output: ReactionSignals, Model, Latency, Cost |
| 결과 집계 | Input: N개 응답, Output: stats+outliers_removed, Latency |
| 성과 예측 | Input: AggregationResult, Output: KPI JSON, Model, Latency, Cost |
| 개선안 생성 | Input: AdAnalysis+KPI, Output: ImprovementReport, Model, Latency, Cost |

---

## 4. 평가 지표

### 품질 지표

| 지표 | 측정 방법 | 목표값 |
|---|---|---|
| 분석 신뢰도 | `analysis_confidence` 평균 | ≥ 0.80 |
| 페르소나 다양성 | 세그먼트별 분포 편차 | CV < 0.3 |
| 반응 확신도 | `confidence` 평균 | ≥ 0.70 |
| 이상치 비율 | outliers / total | ≤ 10% |

### 성능 지표

| 지표 | 목표값 |
|---|---|
| 전체 파이프라인 (20명) | ≤ 60초 |
| SSE 첫 이벤트 수신 | ≤ 3초 |

### 비용 지표

| 지표 | 목표값 |
|---|---|
| 시뮬레이션 1회 (20명) | ≤ $0.10 |

---

## 5. 하네스 기반 테스트

### 단위 하네스 (일관성 검증)

```python
async def test_harness_reaction_sim():
    input = load_fixture("sample_image_ad_analysis")
    personas = load_fixture("sample_personas_20")

    results = []
    for i in range(10):
        response = await ReactionSimulationAgent().run(
            ReactionSimRequest(simulation_id=f"harness_{i}", ...)
        )
        results.append(response)

    click_rates = [
        sum(r.signals.click_intent for r in res.responses) / len(res.responses)
        for res in results
    ]
    # 10회 실행 간 CTR 변동 ±10% 이내
    assert max(click_rates) - min(click_rates) < 0.10
```

### 비교 하네스 (구현체 비교)

```python
async def compare_reaction_sim_producers():
    from stages.reaction_sim.member_c_v1 import ReactionSimV1
    from stages.reaction_sim.member_c_v2 import ReactionSimV2

    input = load_standard_fixture()
    result_v1 = await ReactionSimV1().run(input)
    result_v2 = await ReactionSimV2().run(input)

    print(f"V1 CTR: {calc_ctr(result_v1):.2%}, Cost: ${result_v1.total_cost:.4f}")
    print(f"V2 CTR: {calc_ctr(result_v2):.2%}, Cost: ${result_v2.total_cost:.4f}")
```

### 회귀 테스트

```python
BASELINE_SCORES = {"ctr": 0.42, "cvr": 0.18, "effectiveness": 0.63}

async def test_pipeline_regression():
    result = await run_full_pipeline(load_standard_fixture())
    assert abs(result.kpi.ctr - BASELINE_SCORES["ctr"]) < 0.05
```

---

## 6. Prompt 관리

### 버저닝

```python
# stages/ad_analysis/prompts.py
PROMPTS = {
    "v1.0": "당신은 광고 분석 전문가입니다...",
    "v1.1": "당신은 광고 분석 전문가입니다. 특히 CTA 문구 식별에 집중하세요...",
}
CURRENT_VERSION = "v1.1"
```

### 개선 워크플로우

```
1. LangSmith에서 낮은 confidence 또는 파싱 실패 케이스 식별
2. 실패 사례 Input/Output 분석
3. 프롬프트 수정 (버전 올리기)
4. 동일 fixture로 하네스 재실행
5. LangSmith에서 구버전 vs 신버전 비교
6. 개선 확인 후 CURRENT_VERSION 업데이트
```

### 프롬프트 원칙

| 원칙 | 내용 |
|---|---|
| 출력 형식 명시 | JSON 형식 지정, 예시 포함 |
| 실패 처리 | 분석 불가 필드는 `null` 반환 |
| 언어 통일 | 한국어 응답 기본 |
| 길이 제어 | `reasoning` 3문장 이내 |
| 역할 설정 | system 프롬프트에 전문가 역할 명시 |

---

## 7. 멀티 LLM 비교 (발표 포인트)

```
Stage 3 반응 시뮬레이션 비교 예시:
┌──────────────────┬─────────┬──────────┬──────────┬────────┐
│ 구현체            │ CTR 예측 │ 레이턴시  │ 비용/20명 │ 다양성 │
├──────────────────┼─────────┼──────────┼──────────┼────────┤
│ GPT-4o-mini 전용 │ 42%     │ 18.2s    │ $0.03    │ 낮음   │
│ Claude Haiku 전용│ 39%     │ 15.4s    │ $0.02    │ 중간   │
│ 혼합 (50/50)      │ 41%     │ 19.8s    │ $0.025   │ 높음   │
└──────────────────┴─────────┴──────────┴──────────┴────────┘
```

---

## 8. 로그 분석 → 개선 사례 (발표 포인트)

```
문제:   LangSmith에서 페르소나 20명의 sentiment가 0.6~0.8에 집중
        → 다양성 부족, CTR 편향 의심

원인:   Prompt v1.0: "소비자 페르소나를 생성하세요" (너무 단순)
        → LLM이 "평균적 소비자"를 반복 생성

개선:   Prompt v1.1: "세그먼트 전형 + 브랜드 회의적 소비자 포함"
        + Temperature 0.4~1.1 분산 적용

결과:   sentiment 분포: 0.6~0.8 → -0.3~0.9
        다양성 CV: 0.41 → 0.18
```

LangSmith 화면과 함께 발표한다.
