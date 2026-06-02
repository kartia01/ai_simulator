package com.adsimulator.entity;

import jakarta.persistence.*;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;

import java.util.List;
import java.util.UUID;

@Entity
@Table(name = "personas")
@Getter
@Setter
@NoArgsConstructor
public class Persona {

    @Id
    @GeneratedValue(strategy = GenerationType.UUID)
    private UUID id;

    @Column(nullable = false)
    private int age;

    @Column(nullable = false)
    private String job;

    /**
     * Situational context that grounds the AI persona in a real moment.
     * Example: "exhausted on packed subway after 10-hour work shift"
     */
    @Column(nullable = false, length = 500)
    private String context;

    /**
     * Specific behavioral triggers that cause immediate scroll-past.
     * Example: "too much text, no clear price, stock photos"
     */
    @Column(name = "drop_off_trigger", nullable = false, length = 500)
    private String dropOffTrigger;

    private String mbti;

    @ElementCollection(fetch = FetchType.EAGER)
    @CollectionTable(name = "persona_interests", joinColumns = @JoinColumn(name = "persona_id"))
    @Column(name = "interest")
    private List<String> interests;

    @Column(nullable = false)
    private String name;

    /** 소득 수준 — e.g. "저소득", "중산층", "고소득" */
    @Column(name = "income_level")
    private String incomeLevel;

    /** 구매 성향 — e.g. "충동구매 잦음", "비교 후 구매", "거의 안 삼" */
    @Column(name = "purchase_pattern")
    private String purchasePattern;

    /** 브랜드 민감도 — e.g. "브랜드 중시", "가격 중시", "무관심" */
    @Column(name = "brand_sensitivity")
    private String brandSensitivity;

    /** 평소 광고 반응 패턴 — e.g. "광고 거의 클릭 안 함, 할인 정보만 반응" */
    @Column(name = "typical_ad_behavior", length = 500)
    private String typicalAdBehavior;
}
