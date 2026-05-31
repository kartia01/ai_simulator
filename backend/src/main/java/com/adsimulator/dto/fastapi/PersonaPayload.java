package com.adsimulator.dto.fastapi;

import com.fasterxml.jackson.annotation.JsonProperty;

import java.util.List;

/**
 * Outgoing DTO sent TO FastAPI — must match Python PersonaInput (snake_case).
 */
public record PersonaPayload(

        @JsonProperty("persona_id")
        String personaId,

        int age,
        String job,
        String context,

        @JsonProperty("drop_off_trigger")
        String dropOffTrigger,

        String mbti,

        List<String> interests
) {}
