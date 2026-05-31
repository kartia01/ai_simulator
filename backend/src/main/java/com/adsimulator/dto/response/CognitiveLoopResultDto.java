package com.adsimulator.dto.response;

import com.fasterxml.jackson.annotation.JsonProperty;

/** Mirrors Python CognitiveLoopResult — incoming snake_case from FastAPI. */
public record CognitiveLoopResultDto(

        @JsonProperty("persona_id")
        String personaId,

        @JsonProperty("step1_unconscious_reaction")
        UnconsciousReactionDto step1UnconsciousReaction,

        @JsonProperty("step2_selfish_filtering")
        SelfishFilteringDto step2SelfishFiltering,

        @JsonProperty("step3_final_action")
        FinalActionDto step3FinalAction
) {}
