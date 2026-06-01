package com.adsimulator.dto.response;

import com.fasterxml.jackson.annotation.JsonAlias;

/** Mirrors Python FinalAction — incoming snake_case from FastAPI. */
public record FinalActionDto(

        boolean clicked,

        @JsonAlias("action_reason")
        String actionReason
) {}
