# AI 광고 시뮬레이터 필수 Input 스키마

## 1. 광고 및 상품 데이터 (Ad & Product Context)

attention(주목도), sentiment(호감), comprehension(이해도)을 측정하기 위해 AI가 읽어야 할 핵심 크리에이티브 데이터

| 필드 | 의미 | 타입 / 범위 | 필수 여부 | 연결되는 Output 지표 |
|---|---|---|---|---|
| ad_id | 광고 에셋 식별자 | string | ✅ | - |
| ad_copy_main | 메인 카피 (헤드라인) | string | ✅ | attention, sentiment |
| ad_copy_sub | 서브 카피 / 바디 카피 | string | ✅ | comprehension, reasoning |
| ad_visual_desc | 이미지/영상 키워드 및 분위기 설명 | string | ✅ | attention, emotions |
| tone_and_manner | 광고의 톤앤매너 (예: rational, emotional, funny) | string (enum) | ✅ | sentiment |
| product_category | 상품 카테고리 (대/중/소분류) | string | ✅ | recall |
| product_price | 시뮬레이션 대상 상품의 가격 | int | 조건부 | conversion_intent, cost_metrics (ROAS/CPA) |

## 2. 매체 및 가상 환경 데이터 (Media & Environment Context)

특정 매체나 노출 타이밍에 따라 click_intent와 광고 스킵 여부가 달라지므로, 시뮬레이션 환경을 통제하는 변수입니다.

| 필드 | 의미 | 타입 / 범위 | 필수 여부 | 연결되는 Output 지표 |
|---|---|---|---|---|
| media_channel | 광고가 집행되는 매체 (예: instagram_feed, youtube_pre_roll, naver_search) | string (enum) | ✅ | click_intent, attention |
| exposure_timestamp | 가상의 노출 시간대 (예: 2026-06-04T22:00:00) | datetime | ✅ | attention (퇴근 후 vs 업무 시간) |
| ad_format | 광고 형태 (예: image_single, video_5s_skip, text_link) | string (enum) | ✅ | attention, click_intent |

## 3. 페르소나 데이터 (Persona Context)

가장 중요한 주체 데이터입니다. 앞서 정의한 페르소나 지표들을 AI가 프롬프트나 연산식에 가중치로 반영할 수 있도록 구조화한 형태입니다.

| 필드 | 의미 | 타입 / 범위 | 필수 여부 | 연결되는 Output 지표 |
|---|---|---|---|---|
| persona_id | 페르소나 식별자 | string | ✅ | persona_id (1:1 매핑) |
| segment | 세그먼트 (예: 30s_female_urban) | string (enum) | ✅ | segment (1:1 매핑) |
| pain_points | 이 페르소나가 해결하고 싶어 하는 결핍 리스트 | string[] | ✅ | sentiment, reasoning |
| interest_keywords | 관심사 키워드 벡터 (Embedding 값 또는 대표 키워드 어레이) | string[] / float[] | ✅ | attention, sentiment |
| media_preferences | 매체별 선호도 점수 (예: {"instagram": 0.9, "youtube": 0.7}) | map (string → float) | ✅ | click_intent |
| active_time_windows | 주로 미디어를 소비하는 시간대 분할 (예: ["21:00-23:00", "08:00-09:00"]) | string[] | 권장 | attention |
| price_threshold | 이 카테고리 상품에 지출 가능한 최대 예산 저항선 | int | ✅ | conversion_intent |
| brand_loyalty | 기존 주류 브랜드에 대한 충성도 (전환 장벽 높이) | float 0.0~1.0 | 권장 | conversion_intent, recall |
