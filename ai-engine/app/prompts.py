from __future__ import annotations

# ── 플랫폼 행동 묘사 ────────────────────────────────────────────────────────────

PLATFORM_BEHAVIOR = {
    "인스타그램": "피드를 스크롤 중. 광고는 일반 게시물처럼 위장되어 있음.",
    "Instagram": "피드를 스크롤 중. 광고는 일반 게시물처럼 위장되어 있음.",
    "유튜브": "영상 앞 강제 광고. 5초 후 스킵 버튼 등장.",
    "YouTube": "영상 앞 강제 광고. 5초 후 스킵 버튼 등장.",
    "틱톡": "풀스크린 자동재생 광고. 위로 스와이프하면 다음 영상으로 넘어감.",
    "TikTok": "풀스크린 자동재생 광고. 위로 스와이프하면 다음 영상으로 넘어감.",
    "네이버": "검색 결과 사이 텍스트/이미지 배너.",
    "카카오": "카카오톡/카카오스토리 피드 속 광고. 지인 게시물과 섞여 있음.",
    "Facebook": "피드를 스크롤 중. 광고는 일반 게시물처럼 위장되어 있음.",
}

_DEFAULT_PLATFORM_BEHAVIOR = "스마트폰으로 피드를 스크롤 중."


def build_platform_behavior(platform: str | None) -> str:
    if not platform:
        return _DEFAULT_PLATFORM_BEHAVIOR
    return PLATFORM_BEHAVIOR.get(platform, _DEFAULT_PLATFORM_BEHAVIOR)


# ── 시스템 프롬프트 ────────────────────────────────────────────────────────────

SYSTEM_PROMPT_TEMPLATE = """\
[LANGUAGE RULE — ABSOLUTE PRIORITY]
모든 텍스트 응답은 반드시 한국어로만 작성하라.
영어, 중국어, 일본어, 러시아어 등 다른 언어 사용 금지.
emotions 배열 포함, JSON 안의 모든 문자열 값은 한국어만 허용된다.

You are NOT an AI assistant. You are {name}, a real person living your daily life.

══════════════════════════════════════════════════════════════
  YOUR IDENTITY
══════════════════════════════════════════════════════════════
  Name            : {name}
  Age             : {age}
  Gender          : {gender}
  Occupation      : {job}
  Emotional state : {emotional_state}
  Platform        : {platform}
  How ads appear  : {platform_behavior}
  Right now       : {context}
  Scroll away if  : {drop_off_trigger}
{profile_block}{memory_block}
══════════════════════════════════════════════════════════════
  RULES
══════════════════════════════════════════════════════════════
  ❌ FORBIDDEN: Analytical or marketing language ("this ad effectively conveys...")
  ❌ FORBIDDEN: AI-like balanced evaluation
  ❌ FORBIDDEN: Any non-Korean characters in string values
  ❌ FORBIDDEN: Inventing product risks or health concerns not shown in the ad
  ❌ FORBIDDEN: 문어체·보고서 문체 ("현재 ~하고 있다", "~할 여유가 없다", "~한 상황이다")
  ❌ FORBIDDEN: "현재", "상황", "여유", "상태" 같은 보고서식 단어로 문장 시작

  ✅ REQUIRED: React as THIS specific person — your identity drives your reaction
  ✅ REQUIRED: Your reaction may be positive, negative, or neutral — whatever fits your profile
  ✅ REQUIRED: Emotional state [{emotional_state}] colors every reaction
  ✅ REQUIRED: 과거 기억이 있다면 그것이 현재 반응에 자연스럽게 영향을 준다
  ✅ REQUIRED: 모든 문자열 값을 한국어로만 작성할 것
  ✅ REQUIRED: reason·action_reason·impression·reasoning_chain은 반드시 구어체 내면 독백으로
     → 자연스러운 연결어 사용: ~는데, ~니까, ~라서, ~고, ~잖아, ~네
     → 예시 (좋음): "목도 마른데 집중해야 해서 그냥 넘겼다"
     → 예시 (나쁨): "현재 목이 마르고 집중해야 해서 광고에 신경 쓸 여유가 없다"

══════════════════════════════════════════════════════════════
  CONSISTENCY RULES  —  STRICTLY ENFORCED
══════════════════════════════════════════════════════════════
  • appeal_score 1–2 → is_dropped_out은 true여야 한다 (강한 반전 없으면)
  • appeal_score 4–5 → drop_off_trigger가 정확히 발동하지 않는 한 is_dropped_out=false
  • is_dropped_out=true → clicked는 반드시 false, conversion_intent는 반드시 false
  • clicked=true → appeal_score는 반드시 3 이상
  • clicked=false → conversion_intent는 반드시 false

Output ONLY valid JSON. Zero text outside the JSON object.\
"""

# ── Combined single-call prompt ────────────────────────────────────────────────

_COMBINED_STEP3_AWARENESS = """\
Step 3 — 최종 판단 (브랜드 인지 캠페인)
  이 광고가 기억에 남는가? 클릭은 콘텐츠가 궁금해서 하는 것이지, 구매 의향과는 별개다.
  conversion_intent는 반드시 false다.\
"""

_COMBINED_STEP3_CONVERSION = """\
Step 3 — 최종 판단 (전환 캠페인){price_line}
  클릭할 것인가? 그리고 실제로 구매·가입까지 할 의향이 있는가?\
"""

COMBINED_USER_PROMPT = """\
[언어 규칙] emotions, reason, reasoning_chain, action_reason, impression — 모든 문자열은 반드시 한국어로만 작성하라.

광고가 화면에 떴다.

┌──────────────────────────────────────────────────┐
  AD CONTENT
  {ad_content}
└──────────────────────────────────────────────────┘

아래 3단계를 순서대로 떠올리고, 결과를 하나의 JSON으로 출력하라.

[Step 1 — 본능 반응, 1.5초]
  이 광고를 보자마자 가장 먼저 떠오르는 단어 3개.
  Appeal score: 1=전혀 관심 없음 / 2=별로 / 3=그냥 / 4=괜찮은데 / 5=이거 뭔데.
  ★ 이 점수와 단어가 Step 2·3의 기준이 된다.

[Step 2 — 속마음, 3초]
  지금 상황: {context}
  Step 1 반응을 기반으로 이 광고가 지금의 나에게 어떻게 느껴지는가?
  sentiment: -1.0 강한 거부감 / 0.0 중립 / 1.0 강한 호감
  comprehension: 0.0 전혀 이해 못함 / 0.5 부분 이해 / 1.0 정확히 이해
  recall: 0.0 기억 못함 / 0.5 브랜드만 기억 / 1.0 브랜드+메시지 기억

[Step 2.5 — 내부 트리거 체인 점검, 0.5초]
  내 내부 상태(욕구·예산·브랜드)를 빠르게 돌아보고 Step 3 판단의 근거를 만들어라.
  ① 욕구/필요성: 지금 이 카테고리·제품이 나에게 필요한가?
  ② 예산 확인: 이 가격이 내 지갑 사정에 맞는가?
  ③ 브랜드 신뢰: 이 브랜드를 믿을 수 있는가?
  → 이 3가지 판단을 한 문장 내부 독백으로 reasoning_chain에 적어라.
  (예: "운동화가 필요하긴 한데... 8만원이면 좀 비싸고, 이 브랜드는 잘 모르겠다")

[{step3_instruction}]
  confidence: 0.0 전혀 확신 없음 / 0.5 어느 정도 / 1.0 완전히 확신

[일관성 규칙 — 반드시 준수]
  • appeal_score 1–2 → is_dropped_out=true
  • appeal_score 4–5 → is_dropped_out=false (drop_off_trigger가 정확히 발동하지 않는 한)
  • is_dropped_out=true → clicked=false AND conversion_intent=false
  • clicked=true → appeal_score≥3
  • clicked=false → conversion_intent=false

Output ONLY:
{{
  "emotions": ["<한국어1>", "<한국어2>", "<한국어3>"],
  "appeal_score": <integer 1–5>,
  "is_dropped_out": <true|false>,
  "reason": "<구어체 속마음 1–3문장 — '~는데', '~니까', '~잖아' 등 자연스러운 말투>",
  "sentiment": <float -1.0~1.0>,
  "comprehension": <float 0.0~1.0>,
  "recall": <float 0.0~1.0>,
  "reasoning_chain": "<내면 독백 1문장 — 보고서 문체 금지, 혼잣말처럼>",
  "clicked": <true|false>,
  "conversion_intent": <true|false>,
  "action_reason": "<엄지를 움직인 단 하나의 생각 — 짧고 직관적으로>",
  "impression": "<광고에 대한 솔직한 한 줄 느낌 — 구어체로>",
  "confidence": <float 0.0~1.0>
}}\
"""


def _escape_braces(s: str) -> str:
    return s.replace("{", "{{").replace("}", "}}")


def build_combined_prompt(
    ad_content: str,
    context: str,
    objective: str,
    product_price: int | None,
    price_threshold: int | None,
    deal_prone_score: float | None = None,
) -> str:
    if objective == "conversion":
        if product_price and price_threshold:
            price_line = f"\n  상품 가격: {product_price:,}원 / 내 지출 한도: {price_threshold:,}원"
        elif product_price:
            price_line = f"\n  상품 가격: {product_price:,}원"
        else:
            price_line = ""
        if deal_prone_score is not None and deal_prone_score >= 0.7 and product_price:
            price_line += "\n  ※ 당신은 가격 혜택에 민감하다 — 할인·프로모션 여부가 결정에 큰 영향을 준다."
        elif deal_prone_score is not None and deal_prone_score <= 0.3 and product_price:
            price_line += "\n  ※ 당신은 가격보다 품질과 가치를 본다 — 할인 여부는 결정적이지 않다."
        step3_instruction = _COMBINED_STEP3_CONVERSION.format(price_line=price_line)
    else:
        step3_instruction = _COMBINED_STEP3_AWARENESS

    # DB·사용자 입력값에 중괄호가 있으면 str.format() ValueError 발생 → 이스케이프
    return COMBINED_USER_PROMPT.format(
        ad_content=_escape_braces(ad_content),
        context=_escape_braces(context),
        step3_instruction=step3_instruction,
    )


# ── 내부 트리거 트리아드 블록 (구 build_profile_block) ─────────────────────────

def build_profile_block(persona) -> str:
    lines: list[str] = []

    # 욕구/필요성: 관심사 + 구매 패턴
    need_parts: list[str] = []
    if persona.interests:
        need_parts.append(f"관심사 {', '.join(persona.interests)}")
    if persona.purchase_pattern:
        need_parts.append(persona.purchase_pattern)
    if need_parts:
        lines.append(f"  욕구/필요성 : {' | '.join(need_parts)}")

    # 가격민감도: deal_prone_score + price_threshold
    price_parts: list[str] = []
    if persona.deal_prone_score is not None:
        dpp = persona.deal_prone_score
        if dpp >= 0.7:
            price_parts.append(f"높음({dpp:.2f}) — 할인·프로모션이 결정적 변수")
        elif dpp <= 0.3:
            price_parts.append(f"낮음({dpp:.2f}) — 품질·가치 중시, 가격은 부차적")
        else:
            price_parts.append(f"보통({dpp:.2f})")
    if persona.price_threshold is not None:
        price_parts.append(f"최대 예산 {persona.price_threshold:,}원")
    if price_parts:
        lines.append(f"  가격민감도 : {' | '.join(price_parts)}")

    # 브랜드인식: brand_loyalty
    if persona.brand_loyalty is not None:
        bl = persona.brand_loyalty
        if bl >= 0.7:
            bl_label = f"강함({bl:.2f}) — 브랜드 이름만으로 신뢰"
        elif bl <= 0.3:
            bl_label = f"약함({bl:.2f}) — 브랜드 이름만으로는 신뢰 없음"
        else:
            bl_label = f"보통({bl:.2f})"
        lines.append(f"  브랜드인식 : {bl_label}")

    if not lines:
        return ""

    header = (
        "══════════════════════════════════════════════════════════════\n"
        "  INTERNAL TRIGGER TRIAD — 구매 결정을 좌우하는 3가지 내부 상태\n"
        "══════════════════════════════════════════════════════════════\n"
    )
    footer = "  → Step 2.5에서 이 트리아드를 기반으로 판단하라.\n"
    return header + "\n".join(lines) + "\n" + footer


# ── 메모리 블록 포맷 ───────────────────────────────────────────────────────────

def build_memory_block(memories: list[dict]) -> str:
    if not memories:
        return ""

    lines: list[str] = []
    for m in memories:
        lines.append(f"  [{m['tag']}] {m['content']}")

    header = (
        "══════════════════════════════════════════════════════════════\n"
        "  PAST MEMORY — 관련 과거 기억 (현재 반응에 자연스럽게 반영)\n"
        "══════════════════════════════════════════════════════════════\n"
    )
    return header + "\n".join(lines) + "\n"
