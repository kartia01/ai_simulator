package com.adsimulator.dto.response;

import com.fasterxml.jackson.annotation.JsonProperty;

import java.util.List;

/**
 * Top-level response DTO.
 *
 * Jackson deserializes this from snake_case JSON received from FastAPI,
 * then re-serializes it as camelCase JSON back to the React frontend
 * (Spring Boot's default Jackson config handles this automatically).
 */
public record SimulationResultDto(

        @JsonProperty("ad_id")
        String adId,

        @JsonProperty("total_personas")
        int totalPersonas,

        List<CognitiveLoopResultDto> results,

        AdMetricsDto metrics
) {}
