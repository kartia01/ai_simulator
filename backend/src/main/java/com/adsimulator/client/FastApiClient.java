package com.adsimulator.client;

import com.adsimulator.dto.fastapi.SimulationPayload;
import com.adsimulator.dto.response.SimulationResultDto;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.http.MediaType;
import org.springframework.stereotype.Component;
import org.springframework.web.reactive.function.client.WebClient;
import org.springframework.web.reactive.function.client.WebClientResponseException;
import reactor.core.publisher.Mono;

import java.time.Duration;

@Component
public class FastApiClient {

    private static final Logger log = LoggerFactory.getLogger(FastApiClient.class);

    private final WebClient webClient;

    public FastApiClient(
            WebClient.Builder builder,
            @Value("${fastapi.base-url:http://localhost:8000}") String baseUrl
    ) {
        this.webClient = builder
                .baseUrl(baseUrl)
                .defaultHeader("Content-Type", MediaType.APPLICATION_JSON_VALUE)
                .build();
    }

    /**
     * POST /simulate → returns Mono so the caller can block or chain reactively.
     *
     * Snake_case ↔ camelCase mapping is handled by @JsonProperty annotations
     * on the Payload and Result DTOs — no global Jackson config change needed.
     */
    public Mono<SimulationResultDto> simulate(SimulationPayload payload) {
        log.info("→ FastAPI /simulate  ad_id={} personas={}",
                payload.adId(), payload.personas().size());

        return webClient.post()
                .uri("/simulate")
                .bodyValue(payload)
                .retrieve()
                .bodyToMono(SimulationResultDto.class)
                .timeout(Duration.ofSeconds(300))
                .doOnSuccess(r -> log.info(
                        "← FastAPI OK  ad_id={}  VTR={}%  CTR={}%",
                        r.adId(), r.metrics().vtr(), r.metrics().ctr()))
                .onErrorMap(WebClientResponseException.class, ex -> {
                    log.error("FastAPI error {}: {}", ex.getStatusCode(), ex.getResponseBodyAsString());
                    return new RuntimeException("AI Engine error: " + ex.getStatusCode());
                });
    }
}
