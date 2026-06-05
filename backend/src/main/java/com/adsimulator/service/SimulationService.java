package com.adsimulator.service;

import com.adsimulator.client.FastApiClient;
import com.adsimulator.dto.fastapi.PersonaPayload;
import com.adsimulator.dto.fastapi.SimulationPayload;
import com.adsimulator.dto.request.AdSimulationRequest;
import com.adsimulator.dto.response.PersonaReactionSignalDto;
import com.adsimulator.dto.response.SimulationResultDto;
import com.adsimulator.entity.Persona;
import com.adsimulator.entity.PersonaResult;
import com.adsimulator.entity.SimulationRun;
import com.adsimulator.repository.PersonaRepository;
import com.adsimulator.repository.SimulationRunRepository;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.context.annotation.Lazy;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.time.LocalDateTime;
import java.util.List;
import java.util.Map;
import java.util.stream.Collectors;

@Service
public class SimulationService {

    private static final Logger log = LoggerFactory.getLogger(SimulationService.class);

    private final PersonaRepository personaRepo;
    private final FastApiClient fastApiClient;
    private final SimulationRunRepository simulationRunRepo;

    // 자기 주입 — self.resolvePersonas/saveRun 호출 시 Spring 프록시를 통해
    // @Transactional이 실제로 적용되도록 한다. @Lazy로 순환 의존성을 방지한다.
    @Lazy
    @Autowired
    private SimulationService self;

    public SimulationService(PersonaRepository personaRepo, FastApiClient fastApiClient,
                             SimulationRunRepository simulationRunRepo) {
        this.personaRepo = personaRepo;
        this.fastApiClient = fastApiClient;
        this.simulationRunRepo = simulationRunRepo;
    }

    /**
     * Orchestrates a full simulation run:
     *  1. Fetch personas from PostgreSQL
     *  2. Map entities → FastAPI payload (snake_case via @JsonProperty)
     *  3. Fire async HTTP request to AI Engine
     *  4. Block and return the structured result to the controller
     */
    // @Transactional 범위를 DB 저장으로만 제한 — FastAPI 호출(최대 300초)을 트랜잭션 밖에 둬야
    // 커넥션 풀이 고갈되지 않는다. resolvePersonas는 readOnly 트랜잭션으로, saveRun은 별도 트랜잭션으로 처리.
    public SimulationResultDto runSimulation(AdSimulationRequest req) {
        List<Persona> personas = self.resolvePersonas(req);

        if (personas.isEmpty()) {
            throw new IllegalArgumentException("No personas found — seed the database first");
        }

        log.info("Running simulation adId={} with {} personas", req.adId(), personas.size());

        Map<String, String> idToName = personas.stream()
                .collect(Collectors.toMap(p -> p.getId().toString(), Persona::getName));

        boolean isVideo = req.mediaContentType() != null && req.mediaContentType().startsWith("video/");
        String imageBase64 = (!isVideo) ? req.mediaBase64() : null;
        String videoBase64 = isVideo ? req.mediaBase64() : null;

        SimulationPayload payload = new SimulationPayload(
                req.adId(),
                req.adContent() != null ? req.adContent() : "",
                req.adType() != null ? req.adType() : "IMAGE",
                personas.stream().map(this::toPayload).toList(),
                imageBase64,
                videoBase64,
                req.mediaContentType()
        );

        SimulationResultDto raw = fastApiClient.simulate(payload).block();

        List<PersonaReactionSignalDto> enriched = raw.results().stream()
                .map(r -> new PersonaReactionSignalDto(
                        idToName.getOrDefault(r.personaId(), r.personaId()),
                        r.segment(),
                        r.attention(),
                        r.sentiment(),
                        r.clickIntent(),
                        r.conversionIntent(),
                        r.comprehension(),
                        r.reasoning(),
                        r.recall(),
                        r.emotions(),
                        r.confidence(),
                        r.creativeId(),
                        r.objective(),
                        r.impression()
                ))
                .toList();

        SimulationResultDto result = new SimulationResultDto(raw.adId(), raw.totalPersonas(), enriched, raw.metrics());
        self.saveRun(req, result);
        return result;
    }

    @Transactional
    public void saveRun(AdSimulationRequest req, SimulationResultDto result) {
        SimulationRun run = new SimulationRun();
        run.setAdId(result.adId());
        run.setAdContent(req.adContent() != null ? req.adContent() : "");
        run.setAdType(req.adType() != null ? req.adType() : "IMAGE");
        run.setRunAt(LocalDateTime.now());
        run.setTotalPersonas(result.totalPersonas());
        run.setVtr(result.metrics().vtr());
        run.setCtr(result.metrics().ctr());
        run.setDropoutRate(result.metrics().dropoutRate());
        run.setAvgAppealScore(result.metrics().avgAppealScore());

        List<PersonaResult> personaResults = result.results().stream()
                .map(r -> {
                    PersonaResult pr = new PersonaResult();
                    pr.setRun(run);
                    pr.setPersonaName(r.personaId());
                    // attention(0-1) → appeal_score(1-5): reverse of agent.py formula (score-1)/4
                    pr.setAppealScore((int) Math.round(r.attention() * 4 + 1));
                    pr.setKeywords(r.emotions() != null ? String.join(",", r.emotions()) : "");
                    pr.setDroppedOut(!r.clickIntent() && r.sentiment() < 0);
                    pr.setSelfishReason(r.reasoning() != null ? r.reasoning() : "");
                    pr.setClicked(r.clickIntent());
                    pr.setActionReason(r.impression() != null ? r.impression() : "");
                    return pr;
                })
                .toList();

        run.getPersonaResults().addAll(personaResults);
        simulationRunRepo.save(run);
        log.info("Saved simulation run id={} adId={}", run.getId(), run.getAdId());
    }

    // ── Private helpers ──────────────────────────────────────────────────────

    @Transactional(readOnly = true)
    public List<Persona> resolvePersonas(AdSimulationRequest req) {
        if (req.personaIds() == null || req.personaIds().isEmpty()) {
            return personaRepo.findAll();
        }
        return personaRepo.findAllByIdIn(req.personaIds());
    }

    private PersonaPayload toPayload(Persona p) {
        return new PersonaPayload(
                p.getId().toString(),
                p.getName(),
                p.getAge(),
                p.getJob(),
                p.getPlatform(),
                p.getContext(),
                p.getDropOffTrigger(),
                p.getMbti(),
                p.getInterests(),
                p.getIncomeLevel(),
                p.getPurchasePattern(),
                p.getBrandSensitivity(),
                p.getTypicalAdBehavior(),
                p.getValueKeywords(),
                p.getEmotionalState()
        );
    }
}
