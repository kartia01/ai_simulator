package com.adsimulator.dto.request;

import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.Size;

import java.util.List;
import java.util.UUID;

/**
 * Inbound request from the React frontend.
 * adContent is optional when mediaBase64 is provided.
 * personaIds may be omitted to use all personas in the database.
 */
public record AdSimulationRequest(

        @NotBlank
        String adId,

        @Size(max = 4000)
        String adContent,   // optional when mediaBase64 is provided

        String adType,    // "IMAGE" | "VIDEO" | "CAROUSEL"  (defaults to IMAGE if null)

        List<UUID> personaIds,   // null = use all personas

        String mediaBase64,       // Base64-encoded image or video bytes (optional)

        String mediaContentType   // MIME type e.g. "image/jpeg", "video/mp4" (optional)
) {}
