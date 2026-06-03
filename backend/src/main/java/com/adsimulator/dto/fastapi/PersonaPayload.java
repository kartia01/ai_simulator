package com.adsimulator.dto.fastapi;

import com.fasterxml.jackson.annotation.JsonProperty;

import java.util.List;

/**
 * Outgoing DTO sent TO FastAPI — must match Python PersonaInput (snake_case).
 */
public record PersonaPayload(

        @JsonProperty("persona_id")
        String personaId,

        String name,
        int age,
        String job,

        String platform,

        String context,

        @JsonProperty("drop_off_trigger")
        String dropOffTrigger,

        String mbti,

        List<String> interests,

        @JsonProperty("income_level")
        String incomeLevel,

        @JsonProperty("purchase_pattern")
        String purchasePattern,

        @JsonProperty("brand_sensitivity")
        String brandSensitivity,

        @JsonProperty("typical_ad_behavior")
        String typicalAdBehavior,

        @JsonProperty("value_keywords")
        String valueKeywords,

        @JsonProperty("emotional_state")
        String emotionalState
) {}
