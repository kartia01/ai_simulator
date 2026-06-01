package com.adsimulator.dto.response;

import com.fasterxml.jackson.annotation.JsonAlias;

import java.util.List;

/** Mirrors Python UnconsciousReaction — incoming snake_case from FastAPI. */
public record UnconsciousReactionDto(

        List<String> keywords,

        @JsonAlias("appeal_score")
        int appealScore
) {}
