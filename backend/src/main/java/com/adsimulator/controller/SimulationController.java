package com.adsimulator.controller;

import com.adsimulator.dto.request.AdSimulationRequest;
import com.adsimulator.dto.response.SimulationResultDto;
import com.adsimulator.service.SimulationService;
import jakarta.validation.Valid;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

@RestController
@RequestMapping("/api")
@CrossOrigin(origins = "${frontend.origin:http://localhost:3000}")
public class SimulationController {

    private final SimulationService simulationService;

    public SimulationController(SimulationService simulationService) {
        this.simulationService = simulationService;
    }

    /**
     * POST /api/simulate
     *
     * Called by the React dashboard. Returns the full simulation result
     * including per-persona 3-step cognitive loops and aggregate KPI metrics.
     *
     * Response is camelCase JSON (Spring Boot Jackson default).
     */
    @PostMapping("/simulate")
    public ResponseEntity<SimulationResultDto> simulate(
            @Valid @RequestBody AdSimulationRequest request
    ) {
        SimulationResultDto result = simulationService.runSimulation(request);
        return ResponseEntity.ok(result);
    }
}
