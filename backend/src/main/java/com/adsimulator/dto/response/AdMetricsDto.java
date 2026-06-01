package com.adsimulator.dto.response;

import com.fasterxml.jackson.annotation.JsonAlias;

/** Mirrors Python AdMetrics — incoming snake_case from FastAPI. */
public record AdMetricsDto(

        double vtr,
        double ctr,

        @JsonAlias("dropout_rate")
        double dropoutRate,

        @JsonAlias("avg_appeal_score")
        double avgAppealScore
) {}
