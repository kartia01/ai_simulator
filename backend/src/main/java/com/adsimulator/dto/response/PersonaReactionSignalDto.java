package com.adsimulator.dto.response;

import com.fasterxml.jackson.annotation.JsonAlias;

import java.util.List;

/** Mirrors Python PersonaReactionSignal — flat structure returned by FastAPI /simulate. */
public record PersonaReactionSignalDto(

        @JsonAlias("persona_id")
        String personaId,

        String segment,

        double attention,
        double sentiment,

        @JsonAlias("click_intent")
        boolean clickIntent,

        @JsonAlias("conversion_intent")
        boolean conversionIntent,

        Double comprehension,
        String reasoning,
        Double recall,

        List<String> emotions,
        Double confidence,

        @JsonAlias("creative_id")
        String creativeId,

        String objective,

        String impression
) {}
