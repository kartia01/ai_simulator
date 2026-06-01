package com.adsimulator.controller;

import com.adsimulator.dto.request.AdSimulationRequest;
import com.adsimulator.dto.response.SimulationResultDto;
import com.adsimulator.service.SimulationService;
import jakarta.validation.Valid;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

@RestController
@RequestMapping("/api")
@CrossOrigin(origins = "${frontend.origin:http://localhost:3000}")
public class SimulationController {

    private static final Logger log = LoggerFactory.getLogger(SimulationController.class);

    private final SimulationService simulationService;

    public SimulationController(SimulationService simulationService) {
        this.simulationService = simulationService;
    }

    @PostMapping("/simulate")
    public ResponseEntity<SimulationResultDto> simulate(
            @Valid @RequestBody AdSimulationRequest request
    ) {
        SimulationResultDto result = simulationService.runSimulation(request);
        return ResponseEntity.ok(result);
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
