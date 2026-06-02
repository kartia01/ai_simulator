package com.adsimulator.entity;

import jakarta.persistence.*;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;

import java.time.LocalDateTime;
import java.util.ArrayList;
import java.util.List;
import java.util.UUID;

@Entity
@Table(name = "simulation_runs")
@Getter
@Setter
@NoArgsConstructor
public class SimulationRun {

    @Id
    @GeneratedValue(strategy = GenerationType.UUID)
    private UUID id;

    @Column(name = "ad_id", nullable = false)
    private String adId;

    @Column(name = "ad_content", nullable = false, length = 2000)
    private String adContent;

    @Column(name = "ad_type", nullable = false)
    private String adType;

    @Column(name = "run_at", nullable = false)
    private LocalDateTime runAt;

    @Column(name = "total_personas", nullable = false)
    private int totalPersonas;

    @Column(nullable = false)
    private double vtr;

    @Column(nullable = false)
    private double ctr;

    @Column(name = "dropout_rate", nullable = false)
    private double dropoutRate;

    @Column(name = "avg_appeal_score", nullable = false)
    private double avgAppealScore;

    @OneToMany(mappedBy = "run", cascade = CascadeType.ALL, orphanRemoval = true)
    private List<PersonaResult> personaResults = new ArrayList<>();
}
