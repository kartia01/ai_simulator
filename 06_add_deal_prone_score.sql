-- ============================================================
-- Migration: add deal_prone_score to personas
-- Date: 2026-06-07
-- Ref: Lichtenstein et al. (1997) Deal Proneness (DPP)
--      0.0 = 가격 무관심 (품질·가치 중시)
--      0.5 = 보통
--      1.0 = 할인·혜택에 강하게 반응
-- ============================================================

ALTER TABLE personas
    ADD COLUMN IF NOT EXISTS deal_prone_score NUMERIC(3, 2)
        CHECK (deal_prone_score >= 0.0 AND deal_prone_score <= 1.0);

-- 기존 9명 페르소나 DPP 점수 설정

-- 박지영 (주부, 35세): 가격 민감 + 비교 구매 → 할인에 반응하지만 충동적이지 않음
UPDATE personas SET deal_prone_score = 0.75
WHERE id = '01641cd0-7048-4c32-ac6b-aebad6d77d31';

-- 최준호 (프리랜서, 31세): 감성·비주얼 > 가격
UPDATE personas SET deal_prone_score = 0.35
WHERE id = '2243f688-371f-42a3-bc50-a2ed5e4652bd';

-- 김영순 (주부, 55세): 검증·신뢰 > 할인
UPDATE personas SET deal_prone_score = 0.45
WHERE id = '2f1a8d74-3c5e-4b9d-a260-8e7f1c4b0d36';

-- 박서연 (고등학생, 17세): 용돈 한계 → 할인에 강하게 반응
UPDATE personas SET deal_prone_score = 0.80
WHERE id = '3a7f2e91-bc4d-4f5a-8e23-1d6c9f0e4b78';

-- 이철수 (자영업자, 43세): 가성비 중시, 실용성 우선
UPDATE personas SET deal_prone_score = 0.60
WHERE id = '5c8d1a20-6e3f-4b2c-9d75-2a0f8e7c5d91';

-- 김민준 (대학생, 22세): 저소득 + 무료·할인 키워드 반응
UPDATE personas SET deal_prone_score = 0.70
WHERE id = 'a1b2c3d4-e5f6-7890-abcd-ef1234567891';

-- 이수현 (마케터, 27세): 가심비·감성 > 가격 할인
UPDATE personas SET deal_prone_score = 0.40
WHERE id = 'b2c3d4e5-f6a7-8901-bcde-f12345678902';

-- 박준영 (개발자, 33세): 스펙·효율 > 가격, 리서치 후 구매
UPDATE personas SET deal_prone_score = 0.25
WHERE id = 'c3d4e5f6-a7b8-9012-cdef-123456789013';

-- 정병철 (부장, 52세): 공신력·브랜드 신뢰 > 할인
UPDATE personas SET deal_prone_score = 0.35
WHERE id = 'd4e5f6a7-b8c9-0123-defa-234567890124';
