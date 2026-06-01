package com.adsimulator.dto.response;

import com.fasterxml.jackson.annotation.JsonAlias;

/** Mirrors Python CognitiveLoopResult — incoming snake_case from FastAPI. */
public record CognitiveLoopResultDto(

        @JsonAlias("persona_id")
        String personaId,

        @JsonAlias("step1_unconscious_reaction")
        UnconsciousReactionDto step1UnconsciousReaction,

        @JsonAlias("step2_selfish_filtering")
        SelfishFilteringDto step2SelfishFiltering,

        @JsonAlias("step3_final_action")
        FinalActionDto step3FinalAction
) {}
