package com.adsimulator.dto.request;

import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.Size;

import java.util.List;
import java.util.UUID;

/**
 * Inbound request from the React frontend.
 * personaIds may be omitted to use all personas in the database.
 */
public record AdSimulationRequest(

        @NotBlank
        String adId,

        @NotBlank
        @Size(min = 10, max = 4000)
        String adContent,

        String adType,    // "IMAGE" | "VIDEO" | "CAROUSEL"  (defaults to IMAGE if null)

        List<UUID> personaIds   // null = use all personas
) {}
