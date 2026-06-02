package com.adsimulator.controller;

import com.adsimulator.dto.request.AdSimulationRequest;
import com.adsimulator.dto.response.SimulationResultDto;
import com.adsimulator.service.SimulationService;
import jakarta.validation.Valid;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.http.MediaType;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.multipart.MultipartFile;

import java.io.IOException;
import java.util.Base64;
import java.util.List;

@RestController
@RequestMapping("/api")
@CrossOrigin(origins = "${frontend.origin:http://localhost:3000}")
public class SimulationController {

    private static final Logger log = LoggerFactory.getLogger(SimulationController.class);
    private static final long MAX_IMAGE_BYTES = 10L * 1024 * 1024;   // 10 MB
    private static final long MAX_VIDEO_BYTES = 50L * 1024 * 1024;   // 50 MB

    private final SimulationService simulationService;

    public SimulationController(SimulationService simulationService) {
        this.simulationService = simulationService;
    }

    /** JSON endpoint — backward-compatible, no file */
    @PostMapping(value = "/simulate", consumes = MediaType.APPLICATION_JSON_VALUE)
    public ResponseEntity<SimulationResultDto> simulate(
            @Valid @RequestBody AdSimulationRequest request
    ) {
        validateAdContent(request);
        SimulationResultDto result = simulationService.runSimulation(request);
        return ResponseEntity.ok(result);
    }

    /** Multipart endpoint — accepts optional image or video file alongside form fields */
    @PostMapping(value = "/simulate", consumes = MediaType.MULTIPART_FORM_DATA_VALUE)
    public ResponseEntity<SimulationResultDto> simulateWithMedia(
            @RequestParam("adId") String adId,
            @RequestParam(value = "adContent", required = false, defaultValue = "") String adContent,
            @RequestParam(value = "adType", required = false, defaultValue = "IMAGE") String adType,
            @RequestPart(value = "mediaFile", required = false) MultipartFile mediaFile
    ) throws IOException {

        String mediaBase64 = null;
        String mediaContentType = null;

        if (mediaFile != null && !mediaFile.isEmpty()) {
            mediaContentType = mediaFile.getContentType();
            boolean isVideo = mediaContentType != null && mediaContentType.startsWith("video/");
            long limit = isVideo ? MAX_VIDEO_BYTES : MAX_IMAGE_BYTES;

            if (mediaFile.getSize() > limit) {
                throw new IllegalArgumentException(
                        isVideo ? "영상 파일 크기는 50MB를 초과할 수 없습니다."
                                : "이미지 파일 크기는 10MB를 초과할 수 없습니다."
                );
            }

            mediaBase64 = Base64.getEncoder().encodeToString(mediaFile.getBytes());
            log.info("Media file received: type={} size={}KB", mediaContentType, mediaFile.getSize() / 1024);
        }

        AdSimulationRequest request = new AdSimulationRequest(
                adId, adContent, adType, List.of(), mediaBase64, mediaContentType
        );
        validateAdContent(request);

        SimulationResultDto result = simulationService.runSimulation(request);
        return ResponseEntity.ok(result);
    }

    private void validateAdContent(AdSimulationRequest req) {
        boolean hasText = req.adContent() != null && req.adContent().trim().length() >= 10;
        boolean hasMedia = req.mediaBase64() != null && !req.mediaBase64().isBlank();
        if (!hasText && !hasMedia) {
            throw new IllegalArgumentException(
                    "광고 내용(최소 10자) 또는 이미지/영상 파일 중 하나 이상 필요합니다."
            );
        }
    }

    @ExceptionHandler(IllegalArgumentException.class)
    public ResponseEntity<ErrorBody> handleBadRequest(IllegalArgumentException ex) {
        log.warn("Bad request: {}", ex.getMessage());
        return ResponseEntity.badRequest().body(new ErrorBody(ex.getMessage()));
    }

    @ExceptionHandler(RuntimeException.class)
    public ResponseEntity<ErrorBody> handleRuntime(RuntimeException ex) {
        log.error("Simulation error: {}", ex.getMessage(), ex);
        return ResponseEntity.status(502).body(new ErrorBody(ex.getMessage()));
    }

    record ErrorBody(String message) {}
}
