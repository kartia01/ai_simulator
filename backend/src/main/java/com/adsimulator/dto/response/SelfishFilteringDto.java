package com.adsimulator.dto.response;

import com.fasterxml.jackson.annotation.JsonProperty;

/** Mirrors Python SelfishFiltering — incoming snake_case from FastAPI. */
public record SelfishFilteringDto(

        @JsonProperty("is_dropped_out")
        boolean isDroppedOut,

        String reason
) {}
