package com.adsimulator.entity;

import jakarta.persistence.*;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;

import java.util.UUID;

@Entity
@Table(name = "persona_results")
@Getter
@Setter
@NoArgsConstructor
public class PersonaResult {

    @Id
    @GeneratedValue(strategy = GenerationType.UUID)
    private UUID id;

    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "run_id", nullable = false)
    private SimulationRun run;

    @Column(name = "persona_name", nullable = false)
    private String personaName;

    @Column(name = "appeal_score", nullable = false)
    private int appealScore;

    /** 쉼표로 구분된 키워드 목록 (ex: "신선함,호기심,관심") */
    @Column(length = 500)
    private String keywords;

    @Column(name = "is_dropped_out", nullable = false)
    private boolean isDroppedOut;

    @Column(name = "selfish_reason", length = 1000)
    private String selfishReason;

    @Column(nullable = false)
    private boolean clicked;

    @Column(name = "action_reason", length = 1000)
    private String actionReason;
}
