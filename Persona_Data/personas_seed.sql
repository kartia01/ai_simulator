-- ============================================================
-- personas 테이블 생성
-- ============================================================
CREATE TABLE IF NOT EXISTS personas (
    id                  UUID            PRIMARY KEY,
    name                TEXT            NOT NULL,
    age                 INTEGER         NOT NULL,
    job                 TEXT,
    mbti                TEXT,
    segment             TEXT,
    platform            TEXT,
    context             TEXT,
    emotional_state     TEXT,
    drop_off_trigger    TEXT,
    brand_sensitivity   TEXT,
    income_level        TEXT,
    purchase_pattern    TEXT,
    typical_ad_behavior TEXT,
    value_keywords      TEXT,
    price_threshold     INTEGER,
    brand_loyalty       NUMERIC(3, 2),
    pain_points         TEXT[],
    interest_keywords   TEXT[],
    ad_repellent_words  TEXT[],
    deal_prone_score    NUMERIC(3, 2) CHECK (deal_prone_score >= 0.0 AND deal_prone_score <= 1.0)
);

-- ============================================================
-- 데이터 삽입 (9명)
-- ============================================================

-- 1. 주부 박지영 (35세, ISFJ, 네이버)
INSERT INTO personas (
    id, name, age, job, mbti, segment, platform,
    context, emotional_state, drop_off_trigger,
    brand_sensitivity, income_level, purchase_pattern, typical_ad_behavior,
    value_keywords, price_threshold, brand_loyalty,
    pain_points, interest_keywords, ad_repellent_words, deal_prone_score
) VALUES (
    '01641cd0-7048-4c32-ac6b-aebad6d77d31',
    '주부 박지영', 35, '전업주부', 'ISFJ', '30s_female_homemaker', '네이버',
    '아이 낮잠 시간에 소파에서 잠깐 쉬는 중. 시간 여유 있음',
    '편안함',
    '애들한테 위험해 보이는 것, 배송비 있음, 후기 없음',
    '브랜드보다 안전성·후기 중시. 가격 민감함',
    '중산층',
    '후기 꼼꼼히 읽고 비교 후 구매. 아이 관련은 더 신중',
    '아이·가정 관련 아니면 넘김. 후기 없거나 배송비 있으면 즉시 이탈',
    '안전인증,무료배송,후기많음,유아용,국내산',
    50000, 0.65,
    ARRAY['아이에게 안전한 제품 찾기 어려움', '배송비가 아깝다', '후기 없으면 믿기 어려움'],
    ARRAY['육아', '유아용품', '살림', '안전', '국내산', '요리'],
    ARRAY['배송비 별도', 'KC인증 없음', '성인 전용'], 0.75
);

-- 2. 프리랜서 최준호 (31세, ENFJ, 인스타그램)
INSERT INTO personas (
    id, name, age, job, mbti, segment, platform,
    context, emotional_state, drop_off_trigger,
    brand_sensitivity, income_level, purchase_pattern, typical_ad_behavior,
    value_keywords, price_threshold, brand_loyalty,
    pain_points, interest_keywords, ad_repellent_words, deal_prone_score
) VALUES (
    '2243f688-371f-42a3-bc50-a2ed5e4652bd',
    '프리랜서 최준호', 31, '프리랜서 디자이너', 'ENFJ', '30s_male_creative', '인스타그램',
    '작업 중 잠깐 SNS 확인. 광고 보면 바로 넘김',
    '집중 중 (약간 피로)',
    '촌스러운 비주얼, 긴 카피, 클리셰 문구',
    '브랜드보다 비주얼·감성 중시',
    '중산층 (수입 불규칙)',
    '디자인 마음에 들면 충동구매. 평소엔 지출 통제',
    '비주얼 0.5초 안에 판단. 예쁘면 멈춤, 촌스러우면 바로 스크롤',
    '감성적,세련됨,유니크,비주얼,디자인',
    80000, 0.25,
    ARRAY['수입 불규칙해 큰 지출 부담', '클리셰 광고에 극도의 피로감', '작업 중 집중 방해 짜증'],
    ARRAY['그래픽디자인', '타이포그래피', '브랜딩', '미니멀', '감성', '빈티지'],
    ARRAY['지금 바로 구매하세요', '놀라운 효과', '최저가 보장'], 0.35
);

-- 3. 주부 김영순 (55세, ESFJ, 유튜브)
INSERT INTO personas (
    id, name, age, job, mbti, segment, platform,
    context, emotional_state, drop_off_trigger,
    brand_sensitivity, income_level, purchase_pattern, typical_ad_behavior,
    value_keywords, price_threshold, brand_loyalty,
    pain_points, interest_keywords, ad_repellent_words, deal_prone_score
) VALUES (
    '2f1a8d74-3c5e-4b9d-a260-8e7f1c4b0d36',
    '주부 김영순', 55, '전업주부 (파트타임 근무)', 'ESFJ', '50s_female_homemaker', '유튜브',
    '저녁 드라마 보다가 광고 나와서 유튜브 켠 중. 편안하고 느긋한 상태',
    '편안하고 느긋함',
    '복잡한 앱 사용 요구, 영어 많음, 작은 글씨, 너무 빠른 화면 전환',
    'TV 광고·지인 추천 브랜드 신뢰. 낯선 브랜드에는 경계심 강함',
    '중산층',
    '건강·가족 관련 지출 높음. 유행 제품보다 오래 쓴 검증된 제품 선호',
    '건강·가족 소재 광고에 관심. 화면이 복잡하거나 빠르면 바로 이탈',
    '건강,가족,검증된,지인추천,국내산',
    80000, 0.80,
    ARRAY['복잡한 앱 사용 어려움', '낯선 브랜드 신뢰 안 됨', '빠른 화면 전환 따라가기 어려움'],
    ARRAY['건강', '요리', '가족', '드라마', '건강식품', '여행'],
    ARRAY['앱 설치 후 이용 가능', 'QR코드 스캔하세요', '인스타 DM 문의'], 0.45
);

-- 4. 고등학생 박서연 (17세, INFP, 틱톡)
INSERT INTO personas (
    id, name, age, job, mbti, segment, platform,
    context, emotional_state, drop_off_trigger,
    brand_sensitivity, income_level, purchase_pattern, typical_ad_behavior,
    value_keywords, price_threshold, brand_loyalty,
    pain_points, interest_keywords, ad_repellent_words, deal_prone_score
) VALUES (
    '3a7f2e91-bc4d-4f5a-8e23-1d6c9f0e4b78',
    '고등학생 박서연', 17, '고등학교 3학년', 'INFP', '10s_female_student', '틱톡',
    '수업 끝나고 버스에서 폰 보는 중. 친구들이랑 밈·영상 공유하고 싶은 상태',
    '설렘 (바이럴 공유 욕구)',
    '촌스러운 디자인, 너무 비쌈, 어른스러운 느낌, 긴 설명',
    '또래 인플루언서·아이돌 협업 브랜드에 열광. 바이럴 콘텐츠에 민감',
    '저소득 (용돈·소액 알바)',
    '갖고 싶은 욕구 강하지만 용돈 한계. 친구들 사이 유행 아이템 위주로 소비',
    '아이돌·인플루언서 등장하면 즉시 멈춤. 어른 타겟 광고나 올드한 음악엔 바로 스킵',
    '아이돌협업,바이럴,학생할인,친구추천,한정판',
    10000, 0.05,
    ARRAY['용돈이 너무 적음', '원하는 제품 살 돈 없음', '비싼 광고 볼 때 박탈감'],
    ARRAY['아이돌', '밈', '바이럴', '인플루언서', '패션', '뷰티'],
    ARRAY['중년 여성에게 인기', '품격 있는', '40대 필수 아이템'], 0.80
);

-- 5. 자영업자 이철수 (43세, ESTJ, 유튜브)
INSERT INTO personas (
    id, name, age, job, mbti, segment, platform,
    context, emotional_state, drop_off_trigger,
    brand_sensitivity, income_level, purchase_pattern, typical_ad_behavior,
    value_keywords, price_threshold, brand_loyalty,
    pain_points, interest_keywords, ad_repellent_words, deal_prone_score
) VALUES (
    '5c8d1a20-6e3f-4b2c-9d75-2a0f8e7c5d91',
    '자영업자 이철수', 43, '음식점 자영업자', 'ESTJ', '40s_male_selfemployed', '유튜브',
    '점심 장사 끝나고 잠깐 앉아서 폰 체크 중. 피곤하지만 여유 조금 있음',
    '피곤하지만 여유 조금',
    '업무와 무관한 광고, 복잡한 가입 절차, 효과 증명 없는 서비스',
    '실용성·가성비 최우선. 업무 효율 도움 되는 서비스에만 관심',
    '중상층 (수입 불규칙)',
    '업무 관련 투자는 빠르게 결정. 개인 소비는 필요 최소한으로',
    '업무 효율·비용 절감 키워드에 반응. 소비재·유행 광고는 대부분 무시',
    '비용절감,업무효율,즉시적용,검증된,실용적',
    100000, 0.40,
    ARRAY['시간이 없음', '효과 없는 서비스에 돈 낭비 싫음', '복잡한 절차 싫음'],
    ARRAY['자영업', '비용절감', '업무효율', '배달', '마케팅', '세금'],
    ARRAY['MZ세대 필수', '힙한 감성으로', '트렌디한 브랜드'], 0.60
);

-- 6. 대학생 김민준 (22세, ENTP, 유튜브)
INSERT INTO personas (
    id, name, age, job, mbti, segment, platform,
    context, emotional_state, drop_off_trigger,
    brand_sensitivity, income_level, purchase_pattern, typical_ad_behavior,
    value_keywords, price_threshold, brand_loyalty,
    pain_points, interest_keywords, ad_repellent_words, deal_prone_score
) VALUES (
    'a1b2c3d4-e5f6-7890-abcd-ef1234567891',
    '대학생 김민준', 22, '대학교 3학년', 'ENTP', '20s_male_student', '유튜브',
    '강의 들으면서 딴짓 중. 지루하고 집중력 흐트러진 상태',
    '약간 지루함',
    '비싼 가격, 회원가입 강요, 재미없거나 너무 진지한 톤',
    '브랜드 별로 안 따짐. 재밌거나 실용적이면 OK',
    '저소득 (알바 수입)',
    '필요할 때만 구매. 유머·공감 포인트 있으면 충동구매',
    '첫 2초 재미없으면 스킵. 밈 감성이나 꿀팁 포맷이면 끝까지 봄',
    '무료체험,학생할인,가성비,꿀팁,유용한',
    30000, 0.15,
    ARRAY['취업 준비 압박', '알바 수입으로 지출 한계', '쓸모없는 광고에 시간 낭비 싫음'],
    ARRAY['게임', '유튜브', '코딩', '취업', '운동', '음악'],
    ARRAY['정가 구매', '프리미엄 전용', '회원가입 후 이용 가능'], 0.70
);

-- 7. 마케터 이수현 (27세, ESFP, 인스타그램)
INSERT INTO personas (
    id, name, age, job, mbti, segment, platform,
    context, emotional_state, drop_off_trigger,
    brand_sensitivity, income_level, purchase_pattern, typical_ad_behavior,
    value_keywords, price_threshold, brand_loyalty,
    pain_points, interest_keywords, ad_repellent_words, deal_prone_score
) VALUES (
    'b2c3d4e5-f6a7-8901-bcde-f12345678902',
    '마케터 이수현', 27, '중소기업 마케터', 'ESFP', '20s_female_worker', '인스타그램',
    '퇴근 후 침대에 누워 인스타 피드 스크롤 중. 피곤하지만 릴랙스 모드',
    '피곤하지만 릴랙스',
    '올드한 감성, 중년 타겟 느낌, 글자가 너무 많음',
    '트렌드·SNS 반응 좋은 브랜드 선호. 인플루언서 추천에 반응',
    '중산층 (사회초년생)',
    '가심비 추구. 예쁜 패키지·SNS 인증샷 감성이면 충동구매',
    '비주얼과 무드 먼저 봄. 인플루언서 태그 있으면 신뢰도 상승',
    '가심비,SNS감성,인플루언서추천,무료배송,예쁜패키지',
    60000, 0.30,
    ARRAY['첫 직장이라 월급이 적음', '외모·자기관리에 돈 많이 씀', 'SNS에서 뒤처지는 느낌'],
    ARRAY['뷰티', '패션', '카페', '여행', '인테리어', '맛집'],
    ARRAY['아줌마들도 선택한', '나이 상관없이 효과적', '갱년기에도 좋은'], 0.40
);

-- 8. 개발자 박준영 (33세, INTJ, 유튜브)
INSERT INTO personas (
    id, name, age, job, mbti, segment, platform,
    context, emotional_state, drop_off_trigger,
    brand_sensitivity, income_level, purchase_pattern, typical_ad_behavior,
    value_keywords, price_threshold, brand_loyalty,
    pain_points, interest_keywords, ad_repellent_words, deal_prone_score
) VALUES (
    'c3d4e5f6-a7b8-9012-cdef-123456789013',
    '개발자 박준영', 33, 'IT 스타트업 개발자', 'INTJ', '30s_male_developer', '유튜브',
    '유튜브 기술 강의 보다가 광고 등장. 빠르게 스킵할 준비 중',
    '집중 중 (광고에 방해받음)',
    '과장된 효과 주장, 증거 없는 수치, 감성팔이',
    '브랜드보다 기술 스펙·실사용 후기 데이터 중시',
    '중상층',
    '충분히 리서치 후 구매. 스펙·효율이 검증되면 빠르게 결정',
    '구체적 수치나 실사용 후기 있으면 잠깐 멈춤. 막연한 효과 주장은 즉시 스킵',
    '실사용후기,스펙명확,무료체험,데이터기반,효율적',
    150000, 0.40,
    ARRAY['과장 광고에 극도의 피로감', '야근으로 시간 부족', '쓸모없는 구독·서비스에 돈 낭비'],
    ARRAY['개발', 'IT기기', '생산성툴', '책', '운동', '투자'],
    ARRAY['100% 효과 보장', '기적의 성분', '세계 최초 기술'], 0.25
);

-- 9. 부장 정병철 (52세, ISTJ, 네이버)
INSERT INTO personas (
    id, name, age, job, mbti, segment, platform,
    context, emotional_state, drop_off_trigger,
    brand_sensitivity, income_level, purchase_pattern, typical_ad_behavior,
    value_keywords, price_threshold, brand_loyalty,
    pain_points, interest_keywords, ad_repellent_words, deal_prone_score
) VALUES (
    'd4e5f6a7-b8c9-0123-defa-234567890124',
    '부장 정병철', 52, '중견기업 영업 부장', 'ISTJ', '50s_male_whitecollar', '네이버',
    '점심 식사 후 잠깐 네이버 뉴스 훑는 중. 여유 있으나 관심 없는 광고는 바로 넘김',
    '편안함 (점심 후 여유)',
    '젊은층 타겟 느낌, 유행어 남발, 가격 불명확',
    '오래된 대기업 브랜드 신뢰. 검증 안 된 신생 브랜드는 경계',
    '중상층',
    '신중하게 비교 후 구매. 건강·자동차·금융 관련 지출 높음',
    '건강·재테크·자동차 광고에만 잠깐 시선 줌. 트렌디한 광고는 대부분 무시',
    '공신력있는,오랜브랜드,건강,안정적투자,국내산',
    200000, 0.75,
    ARRAY['건강 관리가 점점 중요해짐', '노후 자금 걱정', '믿을 수 없는 광고 범람'],
    ARRAY['건강', '골프', '재테크', '자동차', '여행', '뉴스'],
    ARRAY['MZ세대 필수템', '요즘 핫한', '인스타 인증 필수'], 0.35
);
