package com.adsimulator.dto.fastapi;

import com.fasterxml.jackson.annotation.JsonProperty;

import java.util.List;

/**
 * Outgoing DTO sent TO FastAPI — must match Python SimulationRequest (snake_case).
 */
public record SimulationPayload(

        @JsonProperty("ad_id")
        String adId,

        @JsonProperty("ad_content")
        String adContent,

        @JsonProperty("ad_type")
        String adType,

        List<PersonaPayload> personas
) {}
