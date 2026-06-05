-- ============================================================
-- ClickMe 시드 데이터 (개발/테스트용)
-- ============================================================

BEGIN;

-- ============================================================
-- 관리자 비밀번호 해시 업데이트 (ChangeMe123!)
-- ============================================================

UPDATE users
SET password_hash = '$2b$12$4SzJfxOP400GQPu9InVujuwjxQCMY3d0iuNpg8ADAM1FebSlq0lKy'
WHERE id = '00000000-0000-0000-0000-000000000001';

-- ============================================================
-- 조직
-- ============================================================

INSERT INTO organizations (id, name, plan_type) VALUES
    ('00000000-0000-0000-0000-000000000002', '테크스타트업', 'professional'),
    ('00000000-0000-0000-0000-000000000003', '마케팅에이전시', 'free');

-- ============================================================
-- 사용자 (비밀번호: Password123!)
-- ============================================================

INSERT INTO users (id, organization_id, email, password_hash, name, role) VALUES
    -- 테크스타트업
    ('00000000-0000-0000-0000-000000000002',
     '00000000-0000-0000-0000-000000000002',
     'kim@techstartup.io',
     '$2b$12$sM/Bb9uH/hePbFOFOCU9Lei/zq.ygWoCdD0FuYtlYfdl0TCnKPdVG',
     '김민준', 'admin'),
    ('00000000-0000-0000-0000-000000000003',
     '00000000-0000-0000-0000-000000000002',
     'lee@techstartup.io',
     '$2b$12$sM/Bb9uH/hePbFOFOCU9Lei/zq.ygWoCdD0FuYtlYfdl0TCnKPdVG',
     '이서연', 'user'),
    ('00000000-0000-0000-0000-000000000004',
     '00000000-0000-0000-0000-000000000002',
     'park@techstartup.io',
     '$2b$12$sM/Bb9uH/hePbFOFOCU9Lei/zq.ygWoCdD0FuYtlYfdl0TCnKPdVG',
     '박지훈', 'user'),
    -- 마케팅에이전시
    ('00000000-0000-0000-0000-000000000005',
     '00000000-0000-0000-0000-000000000003',
     'choi@agency.io',
     '$2b$12$sM/Bb9uH/hePbFOFOCU9Lei/zq.ygWoCdD0FuYtlYfdl0TCnKPdVG',
     '최수아', 'admin');

-- ============================================================
-- 사용자 설정
-- ============================================================

INSERT INTO user_settings (user_id, theme) VALUES
    ('00000000-0000-0000-0000-000000000001', 'dark'),
    ('00000000-0000-0000-0000-000000000002', 'light'),
    ('00000000-0000-0000-0000-000000000003', 'light'),
    ('00000000-0000-0000-0000-000000000004', 'dark'),
    ('00000000-0000-0000-0000-000000000005', 'light');

-- ============================================================
-- 프로젝트
-- ============================================================

INSERT INTO projects (id, organization_id, created_by, name, description, status) VALUES
    ('10000000-0000-0000-0000-000000000001',
     '00000000-0000-0000-0000-000000000002',
     '00000000-0000-0000-0000-000000000002',
     '여름 신제품 론칭 캠페인',
     '2026년 여름 시즌 신제품 출시를 위한 광고 효과 사전 분석',
     'active'),
    ('10000000-0000-0000-0000-000000000002',
     '00000000-0000-0000-0000-000000000002',
     '00000000-0000-0000-0000-000000000003',
     '앱 다운로드 전환율 캠페인',
     '모바일 앱 신규 설치 유도를 위한 소셜미디어 광고 최적화',
     'active'),
    ('10000000-0000-0000-0000-000000000003',
     '00000000-0000-0000-0000-000000000003',
     '00000000-0000-0000-0000-000000000005',
     '브랜드 인지도 제고 캠페인',
     '신규 브랜드 런칭 인지도 광고',
     'active');

-- ============================================================
-- 프로젝트 멤버
-- ============================================================

INSERT INTO project_members (project_id, user_id, role) VALUES
    ('10000000-0000-0000-0000-000000000001', '00000000-0000-0000-0000-000000000002', 'owner'),
    ('10000000-0000-0000-0000-000000000001', '00000000-0000-0000-0000-000000000003', 'editor'),
    ('10000000-0000-0000-0000-000000000001', '00000000-0000-0000-0000-000000000004', 'viewer'),
    ('10000000-0000-0000-0000-000000000002', '00000000-0000-0000-0000-000000000003', 'owner'),
    ('10000000-0000-0000-0000-000000000002', '00000000-0000-0000-0000-000000000004', 'editor'),
    ('10000000-0000-0000-0000-000000000003', '00000000-0000-0000-0000-000000000005', 'owner');

-- ============================================================
-- 광고 시안
-- ============================================================

INSERT INTO ads (id, project_id, created_by, name, input_type, text_content, analysis_status, analysis_result, analysis_confidence) VALUES
    -- 프로젝트1: 텍스트 광고 (분석 완료)
    ('20000000-0000-0000-0000-000000000001',
     '10000000-0000-0000-0000-000000000001',
     '00000000-0000-0000-0000-000000000002',
     '여름 신제품 메인 카피',
     'text',
     '{"headline": "올 여름, 당신의 일상을 바꿀 단 하나의 선택", "body": "새로운 라이프스타일을 위한 스마트한 제품. 지금 바로 경험해보세요.", "cta": "무료 체험 시작하기"}',
     'completed',
     '{"brandSafety": "safe", "emotionalTone": "positive", "keyThemes": ["혁신", "라이프스타일", "편의성"], "targetAgeGroup": "25-40", "estimatedCtr": 3.2}',
     0.87),
    -- 프로젝트1: 텍스트 광고 (분석 중)
    ('20000000-0000-0000-0000-000000000002',
     '10000000-0000-0000-0000-000000000001',
     '00000000-0000-0000-0000-000000000003',
     '여름 신제품 서브 카피 A',
     'text',
     '{"headline": "더위야 물렀거라! 시원한 여름 준비 완료", "body": "프리미엄 기능을 합리적인 가격에. 한정 수량 특별 할인 진행 중.", "cta": "지금 구매하기"}',
     'analyzing',
     NULL,
     NULL),
    -- 프로젝트2: 텍스트 광고 (분석 완료)
    ('20000000-0000-0000-0000-000000000003',
     '10000000-0000-0000-0000-000000000002',
     '00000000-0000-0000-0000-000000000003',
     '앱 다운로드 유도 배너',
     'text',
     '{"headline": "30초 만에 설치하고 첫 달 무료로 쓰세요", "body": "이미 50만 명이 선택한 앱. 지금 다운로드하면 프리미엄 1개월 무료 제공.", "cta": "앱 다운로드"}',
     'completed',
     '{"brandSafety": "safe", "emotionalTone": "neutral", "keyThemes": ["무료체험", "사회적증거", "즉시성"], "targetAgeGroup": "20-35", "estimatedCtr": 4.7}',
     0.91);

-- ============================================================
-- 페르소나 템플릿 (embedding은 AI 서비스 실행 시 채워짐)
-- ============================================================

INSERT INTO persona_templates (id, name, cluster_id, attributes, is_public) VALUES
    ('30000000-0000-0000-0000-000000000001',
     '20대 여성 직장인',
     'cluster_young_female_worker',
     '{"age": 27, "gender": "female", "occupation": "직장인", "income_level": "중", "location": "서울", "lifestyle": ["SNS 활동적", "트렌드 민감", "온라인 쇼핑 선호"], "media_channels": ["인스타그램", "유튜브", "틱톡"], "pain_points": ["바쁜 일상", "가성비"], "values": ["자기계발", "워라밸"]}',
     true),
    ('30000000-0000-0000-0000-000000000002',
     '30대 남성 직장인',
     'cluster_mid_male_worker',
     '{"age": 34, "gender": "male", "occupation": "직장인", "income_level": "중상", "location": "경기도", "lifestyle": ["실용적 소비", "정보 수집 후 구매"], "media_channels": ["유튜브", "네이버", "카카오"], "pain_points": ["시간 부족", "신뢰성 중요"], "values": ["안정", "효율"]}',
     true),
    ('30000000-0000-0000-0000-000000000003',
     '40대 여성 주부',
     'cluster_40s_female_homemaker',
     '{"age": 43, "gender": "female", "occupation": "주부", "income_level": "중", "location": "서울/경기", "lifestyle": ["가족 중심", "커뮤니티 활동"], "media_channels": ["카카오톡", "네이버 카페", "유튜브"], "pain_points": ["가격 민감", "품질 중시"], "values": ["가족", "건강", "신뢰"]}',
     true),
    ('30000000-0000-0000-0000-000000000004',
     '20대 남성 대학생',
     'cluster_young_male_student',
     '{"age": 22, "gender": "male", "occupation": "대학생", "income_level": "하", "location": "서울", "lifestyle": ["게임", "배달음식", "구독서비스"], "media_channels": ["유튜브", "트위치", "인스타그램"], "pain_points": ["예산 한정", "가성비 극단적 중시"], "values": ["재미", "커뮤니티", "경험"]}',
     true),
    ('30000000-0000-0000-0000-000000000005',
     '50대 남성 자영업자',
     'cluster_50s_male_selfemployed',
     '{"age": 52, "gender": "male", "occupation": "자영업자", "income_level": "중상", "location": "지방 대도시", "lifestyle": ["오프라인 구매 선호", "입소문 중요"], "media_channels": ["네이버", "카카오", "TV"], "pain_points": ["디지털 복잡성", "사후지원"], "values": ["신뢰", "실용성", "관계"]}',
     true),
    ('30000000-0000-0000-0000-000000000006',
     '30대 여성 프리랜서',
     'cluster_30s_female_freelancer',
     '{"age": 31, "gender": "female", "occupation": "프리랜서", "income_level": "중", "location": "서울", "lifestyle": ["유연한 시간", "카페 작업", "온라인 커뮤니티"], "media_channels": ["인스타그램", "유튜브", "링크드인"], "pain_points": ["불안정한 수입", "자기관리"], "values": ["자유", "창의성", "성장"]}',
     true);

-- ============================================================
-- 시뮬레이션 (완료된 샘플 1건)
-- ============================================================

INSERT INTO simulations (id, project_id, ad_id, created_by, simulation_type, objective, status,
    persona_count, persona_config, requested_count, received_count, sample_size,
    results_summary, llm_cost_usd, started_at, completed_at)
VALUES (
    '40000000-0000-0000-0000-000000000001',
    '10000000-0000-0000-0000-000000000001',
    '20000000-0000-0000-0000-000000000001',
    '00000000-0000-0000-0000-000000000002',
    'ad_reaction',
    'conversion',
    'completed',
    20,
    '{"ageRange": [20, 45], "genderRatio": {"female": 0.55, "male": 0.45}, "regions": ["서울", "경기", "부산"], "includeClusters": ["cluster_young_female_worker", "cluster_mid_male_worker", "cluster_30s_female_freelancer"]}',
    20, 20, 20,
    '{"overallScore": 74, "verdict": "긍정적 반응 우세, 구매 전환 가능성 높음",
      "kpi": {"attentionScore": 0.81, "sentimentScore": 0.62, "clickIntentRate": 0.60, "conversionIntentRate": 0.45, "comprehensionScore": 0.78, "recallScore": 0.71},
      "funnelDrop": {"attention_to_click": 0.26, "click_to_conversion": 0.25},
      "bySegment": [
        {"segment": "20대 여성", "overallScore": 82, "clickIntentRate": 0.73},
        {"segment": "30대 남성", "overallScore": 69, "clickIntentRate": 0.52},
        {"segment": "30대 여성", "overallScore": 76, "clickIntentRate": 0.61}
      ],
      "topDrivers": ["감성적 카피 공감", "무료 체험 CTA 효과", "트렌디한 표현"],
      "topObjections": ["구체적 혜택 불명확", "제품 특성 설명 부족"]}',
    0.42,
    NOW() - INTERVAL '2 days',
    NOW() - INTERVAL '2 days' + INTERVAL '3 minutes'
);

-- ============================================================
-- 페르소나 응답 (시뮬레이션 샘플 — 6건)
-- ============================================================

INSERT INTO persona_responses (simulation_id, persona_id, segment, persona_attributes, signals, reasoning, confidence, llm_model, tokens_used, response_time_ms) VALUES
    ('40000000-0000-0000-0000-000000000001', 'persona_001', '20대 여성',
     '{"age": 25, "gender": "female", "occupation": "직장인", "location": "서울"}',
     '{"attention": 0.88, "sentiment": 0.75, "click_intent": true, "conversion_intent": true, "comprehension": 0.82, "recall": 0.79}',
     '일상 변화라는 키워드가 직접적으로 공감됨. 무료 체험 CTA가 전환 의도를 높임.',
     0.91, 'gpt-4o-mini', 412, 1840),

    ('40000000-0000-0000-0000-000000000001', 'persona_002', '30대 남성',
     '{"age": 33, "gender": "male", "occupation": "직장인", "location": "경기도"}',
     '{"attention": 0.71, "sentiment": 0.41, "click_intent": false, "conversion_intent": false, "comprehension": 0.74, "recall": 0.65}',
     '카피가 감성적이라 실용적 정보가 부족하게 느껴짐. 제품 스펙 정보가 없어 구매 결정 유보.',
     0.84, 'gpt-4o-mini', 398, 1720),

    ('40000000-0000-0000-0000-000000000001', 'persona_003', '20대 여성',
     '{"age": 28, "gender": "female", "occupation": "직장인", "location": "서울"}',
     '{"attention": 0.92, "sentiment": 0.81, "click_intent": true, "conversion_intent": true, "comprehension": 0.88, "recall": 0.83}',
     '트렌디한 표현과 라이프스타일 연결이 강하게 작용. 즉시 클릭 의향 높음.',
     0.93, 'gpt-4o-mini', 435, 1910),

    ('40000000-0000-0000-0000-000000000001', 'persona_004', '30대 여성',
     '{"age": 31, "gender": "female", "occupation": "프리랜서", "location": "서울"}',
     '{"attention": 0.79, "sentiment": 0.63, "click_intent": true, "conversion_intent": false, "comprehension": 0.77, "recall": 0.72}',
     '클릭 의향은 있으나 무료 체험 이후 결제로 이어질지 불확실. 더 구체적인 혜택 명시 필요.',
     0.87, 'gpt-4o-mini', 421, 1780),

    ('40000000-0000-0000-0000-000000000001', 'persona_005', '30대 남성',
     '{"age": 36, "gender": "male", "occupation": "직장인", "location": "서울"}',
     '{"attention": 0.68, "sentiment": 0.35, "click_intent": false, "conversion_intent": false, "comprehension": 0.71, "recall": 0.58}',
     '메시지 자체는 이해했으나 설득력 부족. 경쟁 제품 대비 차별점이 없어 보임.',
     0.82, 'gpt-4o-mini', 388, 1650),

    ('40000000-0000-0000-0000-000000000001', 'persona_006', '20대 여성',
     '{"age": 24, "gender": "female", "occupation": "대학원생", "location": "서울"}',
     '{"attention": 0.85, "sentiment": 0.69, "click_intent": true, "conversion_intent": true, "comprehension": 0.80, "recall": 0.76}',
     '무료 체험이라는 진입 장벽 낮은 CTA가 효과적. 감성 카피와 연령대 일치.',
     0.89, 'gpt-4o-mini', 408, 1800);

-- ============================================================
-- 리포트
-- ============================================================

INSERT INTO reports (simulation_id, report_data, disclaimer) VALUES
    ('40000000-0000-0000-0000-000000000001',
     '{"executiveSummary": {
        "overallScore": 74,
        "verdict": "긍정적 반응 우세, 구매 전환 가능성 높음",
        "topPriority": "30대 남성 세그먼트 대상 실용적 정보 보강 필요"
      },
      "detailedAnalysis": {
        "kpi": {
          "attentionScore": 0.81, "sentimentScore": 0.62,
          "clickIntentRate": 0.60, "conversionIntentRate": 0.45,
          "comprehensionScore": 0.78, "recallScore": 0.71
        },
        "funnel": {
          "impression_to_attention": 0.81,
          "attention_to_click": 0.60,
          "click_to_conversion": 0.45
        },
        "bySegment": [
          {"segment": "20대 여성", "overallScore": 82, "clickIntentRate": 0.73, "note": "핵심 타겟 반응 우수"},
          {"segment": "30대 남성", "overallScore": 69, "clickIntentRate": 0.52, "note": "실용 정보 부족으로 저조"},
          {"segment": "30대 여성", "overallScore": 76, "clickIntentRate": 0.61, "note": "평균 이상 반응"}
        ],
        "topDrivers": ["감성적 카피 공감", "무료 체험 CTA 효과", "트렌디한 표현"],
        "topObjections": ["구체적 혜택 불명확", "제품 특성 설명 부족", "경쟁 제품 대비 차별점 미흡"]
      },
      "actionItems": {
        "immediate": ["헤드라인에 핵심 기능 1가지 명시", "30대 남성 타겟 별도 소재 제작 검토"],
        "copySuggestions": ["올 여름, [핵심기능]으로 일상을 바꿔보세요", "검증된 50만 명의 선택"],
        "ctaSuggestions": ["7일 무료 체험 시작하기", "지금 바로 경험하기 (카드 불필요)"],
        "nextABTest": "감성 카피 vs 기능 중심 카피 A/B 테스트 권장"
      }}',
     '본 결과는 AI 시뮬레이션 기반 예측입니다. 실제 광고 성과와 ±20~30% 오차가 있을 수 있습니다.');

-- ============================================================
-- 채팅 세션 및 메시지
-- ============================================================

INSERT INTO chat_sessions (id, user_id, project_id, title) VALUES
    ('50000000-0000-0000-0000-000000000001',
     '00000000-0000-0000-0000-000000000002',
     '10000000-0000-0000-0000-000000000001',
     '여름 캠페인 시뮬레이션 결과 분석');

INSERT INTO chat_messages (session_id, role, content, metadata) VALUES
    ('50000000-0000-0000-0000-000000000001', 'user',
     '방금 완료된 시뮬레이션 결과 요약해줘.',
     '{"simulationId": "40000000-0000-0000-0000-000000000001"}'),
    ('50000000-0000-0000-0000-000000000001', 'assistant',
     '여름 신제품 메인 카피 시뮬레이션 결과를 요약해드릴게요.\n\n**종합 점수: 74/100** — 긍정적 반응 우세\n\n**주요 KPI**\n- 주목도: 81% · 감성: 긍정(0.62) · 클릭 의향: 60% · 전환 의향: 45%\n\n**세그먼트별 하이라이트**\n- 20대 여성(82점): 핵심 타겟, 반응 우수\n- 30대 남성(69점): 실용 정보 부족으로 저조\n\n**즉시 개선 제안**: 헤드라인에 핵심 기능 1가지를 명시하고, 30대 남성용 별도 소재 제작을 검토해보세요.',
     '{"simulationId": "40000000-0000-0000-0000-000000000001", "reportId": "40000000-0000-0000-0000-000000000001"}'),
    ('50000000-0000-0000-0000-000000000001', 'user',
     '30대 남성 세그먼트를 위한 카피 개선안 3가지만 제안해줘.',
     NULL),
    ('50000000-0000-0000-0000-000000000001', 'assistant',
     '30대 남성 세그먼트 맞춤 카피 개선안입니다.\n\n**1. 기능 중심형**\n> "하루 10분, [핵심기능]으로 업무 효율 30% UP — 지금 무료로 시작"\n\n**2. 사회적 증거형**\n> "직장인 32만 명이 선택한 이유, 직접 확인해보세요 (7일 무료)"\n\n**3. 문제 해결형**\n> "바쁠수록 스마트하게. 복잡한 [문제]를 한 번에 해결하는 방법"\n\n세 안 모두 실용적 정보와 낮은 진입 장벽 CTA를 조합했습니다. A/B 테스트를 통해 검증하는 걸 권장합니다.',
     NULL);

COMMIT;
