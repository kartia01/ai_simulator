package com.adsimulator.service;

import com.adsimulator.client.FastApiClient;
import com.adsimulator.dto.fastapi.PersonaPayload;
import com.adsimulator.dto.fastapi.SimulationPayload;
import com.adsimulator.dto.request.AdSimulationRequest;
import com.adsimulator.dto.response.SimulationResultDto;
import com.adsimulator.entity.Persona;
import com.adsimulator.repository.PersonaRepository;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.stereotype.Service;

import java.util.List;

@Service
public class SimulationService {

    private static final Logger log = LoggerFactory.getLogger(SimulationService.class);

    private final PersonaRepository personaRepo;
    private final FastApiClient fastApiClient;

    public SimulationService(PersonaRepository personaRepo, FastApiClient fastApiClient) {
        this.personaRepo = personaRepo;
        this.fastApiClient = fastApiClient;
    }

    /**
     * Orchestrates a full simulation run:
     *  1. Fetch personas from PostgreSQL
     *  2. Map entities → FastAPI payload (snake_case via @JsonProperty)
     *  3. Fire async HTTP request to AI Engine
     *  4. Block and return the structured result to the controller
     */
    public SimulationResultDto runSimulation(AdSimulationRequest req) {
        List<Persona> personas = resolvePersonas(req);

        if (personas.isEmpty()) {
            throw new IllegalArgumentException("No personas found — seed the database first");
        }

        log.info("Running simulation adId={} with {} personas", req.adId(), personas.size());

        SimulationPayload payload = new SimulationPayload(
                req.adId(),
                req.adContent(),
                req.adType() != null ? req.adType() : "IMAGE",
                personas.stream().map(this::toPayload).toList()
        );

        // block() is intentional here — the controller endpoint is synchronous (MVC).
        // For a reactive controller, return the Mono directly from fastApiClient.simulate().
        return fastApiClient.simulate(payload).block();
    }

    // ── Private helpers ──────────────────────────────────────────────────────

    private List<Persona> resolvePersonas(AdSimulationRequest req) {
        if (req.personaIds() == null || req.personaIds().isEmpty()) {
            return personaRepo.findAll();
        }
        return personaRepo.findAllByIdIn(req.personaIds());
    }

    private PersonaPayload toPayload(Persona p) {
        return new PersonaPayload(
                p.getId().toString(),
                p.getAge(),
                p.getJob(),
                p.getContext(),
                p.getDropOffTrigger(),
                p.getMbti(),
                p.getInterests()
        );
    }
}
