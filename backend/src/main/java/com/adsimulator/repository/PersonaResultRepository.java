package com.adsimulator.repository;

import com.adsimulator.entity.PersonaResult;
import org.springframework.data.jpa.repository.JpaRepository;

import java.util.UUID;

public interface PersonaResultRepository extends JpaRepository<PersonaResult, UUID> {
}
