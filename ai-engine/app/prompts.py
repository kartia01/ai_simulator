from __future__ import annotations

# ── 플랫폼 행동 묘사 ────────────────────────────────────────────────────────────

PLATFORM_BEHAVIOR = {
    "인스타그램": "피드를 스크롤 중. 광고는 일반 게시물처럼 위장되어 있음.",
    "유튜브": "영상 앞 강제 광고. 5초 후 스킵 버튼 등장.",
    "틱톡": "풀스크린 자동재생 광고. 위로 스와이프하면 다음 영상으로 넘어감.",
    "네이버": "검색 결과 사이 텍스트/이미지 배너.",
    "카카오": "카카오톡/카카오스토리 피드 속 광고. 지인 게시물과 섞여 있음.",
}

_DEFAULT_PLATFORM_BEHAVIOR = "스마트폰으로 피드를 스크롤 중."


def build_platform_behavior(platform: str | None) -> str:
    if not platform:
        return _DEFAULT_PLATFORM_BEHAVIOR
    return PLATFORM_BEHAVIOR.get(platform, _DEFAULT_PLATFORM_BEHAVIOR)


# ── MBTI 기반 자기중심 필터 ────────────────────────────────────────────────────

PERSONA_FILTER_TYPE: dict[str, str] = {
    "ISFJ": "가족·신뢰·배려 — 이 브랜드가 진심으로 느껴지는가? 우리 가족 생활에 어울리는가?",
    "ENFJ": "감성·울림·아름다움 — 나를 감동시키거나 영감을 주는가?",
    "INTP": "효율·스펙·가성비 — 데이터가 납득되는가?",
    "ESFP": "트렌드·사회적 시선·즐거움 — 이게 나를 더 쿨하게 만드는가?",
    "ENFP": "새로움·가치관·설렘 — 내 가치관과 공명하는가?",
    "INTJ": "효율·전략·결과 — 이게 진짜 효과가 있는가?",
    "INFJ": "의미·가치·진정성 — 이 브랜드가 진심인가?",
    "ESTP": "즉각적 자극·재미·혜택 — 지금 당장 뭔가 이득이 있는가?",
    "ISTJ": "신뢰성·검증·안정 — 검증된 제품인가?",
    "ESFJ": "관계·조화·사회적 인정 — 주변 사람들도 좋아할 것인가?",
}

_DEFAULT_FILTER = "나에게 지금 당장 필요한가?"


def build_filter_type(mbti: str | None) -> str:
    if not mbti:
        return _DEFAULT_FILTER
    return PERSONA_FILTER_TYPE.get(mbti.upper(), _DEFAULT_FILTER)


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
  Occupation      : {job}
  Emotional state : {emotional_state}
  Platform        : {platform}
  How ads appear  : {platform_behavior}
  Right now       : {context}
  Scroll away if  : {drop_off_trigger}
  Personal lens   : {filter_type}
{profile_block}
══════════════════════════════════════════════════════════════
  RULES
══════════════════════════════════════════════════════════════
  ❌ FORBIDDEN: Analytical or marketing language ("this ad effectively conveys...")
  ❌ FORBIDDEN: AI-like balanced evaluation
  ❌ FORBIDDEN: Any non-Korean characters in string values
  ❌ FORBIDDEN: Inventing product risks or health concerns not shown in the ad

  ✅ REQUIRED: React as THIS specific person — your identity drives your reaction
  ✅ REQUIRED: Your reaction may be positive, negative, or neutral — whatever fits your profile
  ✅ REQUIRED: Filter through YOUR personality lens: {filter_type}
  ✅ REQUIRED: Emotional state [{emotional_state}] colors every reaction
  ✅ REQUIRED: 모든 문자열 값을 한국어로만 작성할 것

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
[언어 규칙] emotions, reason, action_reason, impression — 모든 문자열은 반드시 한국어로만 작성하라.

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
  넘기는 조건: {drop_off_trigger}
  Step 1 반응을 기반으로 이 광고가 지금의 나에게 어떻게 느껴지는가?
  sentiment: -1.0 강한 거부감 / 0.0 중립 / 1.0 강한 호감
  comprehension: 0.0 전혀 이해 못함 / 0.5 부분 이해 / 1.0 정확히 이해
  recall: 0.0 기억 못함 / 0.5 브랜드만 기억 / 1.0 브랜드+메시지 기억

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
  "reason": "<솔직한 속마음 1–3문장>",
  "sentiment": <float -1.0~1.0>,
  "comprehension": <float 0.0~1.0>,
  "recall": <float 0.0~1.0>,
  "clicked": <true|false>,
  "conversion_intent": <true|false>,
  "action_reason": "<엄지를 움직인 단 하나의 생각>",
  "impression": "<이 광고에 대한 솔직한 한 줄 느낌>",
  "confidence": <float 0.0~1.0>
}}\
"""


def _escape_braces(s: str) -> str:
    return s.replace("{", "{{").replace("}", "}}")


def build_combined_prompt(
    ad_content: str,
    context: str,
    drop_off_trigger: str,
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
        drop_off_trigger=_escape_braces(drop_off_trigger),
        step3_instruction=step3_instruction,
    )


# ── 프로필 블록 ────────────────────────────────────────────────────────────────

def build_profile_block(persona) -> str:
    lines: list[str] = []

    if persona.income_level:
        lines.append(f"  Income level : {persona.income_level}")
    if persona.purchase_pattern:
        lines.append(f"  Buying habit : {persona.purchase_pattern}")
    if persona.brand_sensitivity:
        lines.append(f"  Brand stance : {persona.brand_sensitivity}")
    if persona.typical_ad_behavior:
        lines.append(f"  Ad behavior  : {persona.typical_ad_behavior}")
    if persona.value_keywords:
        lines.append(f"  Eye-catchers : {persona.value_keywords}")
    if persona.mbti:
        lines.append(f"  MBTI         : {persona.mbti}")
    if persona.interests:
        lines.append(f"  Interests    : {', '.join(persona.interests)}")
    if persona.pain_points:
        lines.append(f"  Pain points  : {', '.join(persona.pain_points)}")
    if persona.interest_keywords:
        lines.append(f"  Int.Keywords : {', '.join(persona.interest_keywords)}")
    if persona.price_threshold is not None:
        lines.append(f"  Max budget   : {persona.price_threshold:,}원")
    if persona.brand_loyalty is not None:
        lines.append(f"  Brand loyalty: {persona.brand_loyalty:.2f} (0=무관심, 1=충성)")
    if persona.deal_prone_score is not None:
        dpp = persona.deal_prone_score
        if dpp >= 0.7:
            dpp_label = "높음 — 할인·혜택 광고에 즉각 반응, 가격 혜택이 결정적"
        elif dpp <= 0.3:
            dpp_label = "낮음 — 가격보다 품질·가치 중시, 할인에 큰 흔들림 없음"
        else:
            dpp_label = "보통 — 할인은 참고하지만 결정적이진 않음"
        lines.append(f"  Deal proneness: {dpp:.2f} — {dpp_label}")
    if persona.ad_repellent_words:
        lines.append(f"  Hates these  : {', '.join(persona.ad_repellent_words)}")

    if not lines:
        return ""

    header = (
        "══════════════════════════════════════════════════════════════\n"
        "  BEHAVIORAL PROFILE\n"
        "══════════════════════════════════════════════════════════════\n"
    )
    return header + "\n".join(lines) + "\n"
