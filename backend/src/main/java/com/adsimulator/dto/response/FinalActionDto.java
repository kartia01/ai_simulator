package com.adsimulator.dto.response;

import com.fasterxml.jackson.annotation.JsonProperty;

/** Mirrors Python FinalAction — incoming snake_case from FastAPI. */
public record FinalActionDto(

        boolean clicked,

        @JsonProperty("action_reason")
        String actionReason
) {}
