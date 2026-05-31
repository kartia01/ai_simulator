package com.adsimulator.dto.response;

import com.fasterxml.jackson.annotation.JsonProperty;

/** Mirrors Python AdMetrics — incoming snake_case from FastAPI. */
public record AdMetricsDto(

        double vtr,
        double ctr,

        @JsonProperty("dropout_rate")
        double dropoutRate,

        @JsonProperty("avg_appeal_score")
        double avgAppealScore
) {}
