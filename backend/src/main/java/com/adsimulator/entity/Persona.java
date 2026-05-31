package com.adsimulator.entity;

import jakarta.persistence.*;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;

import java.util.List;
import java.util.UUID;

@Entity
@Table(name = "personas")
@Getter
@Setter
@NoArgsConstructor
public class Persona {

    @Id
    @GeneratedValue(strategy = GenerationType.UUID)
    private UUID id;

    @Column(nullable = false)
    private int age;

    @Column(nullable = false)
    private String job;

    /**
     * Situational context that grounds the AI persona in a real moment.
     * Example: "exhausted on packed subway after 10-hour work shift"
     */
    @Column(nullable = false, length = 500)
    private String context;

    /**
     * Specific behavioral triggers that cause immediate scroll-past.
     * Example: "too much text, no clear price, stock photos"
     */
    @Column(name = "drop_off_trigger", nullable = false, length = 500)
    private String dropOffTrigger;

    private String mbti;

    @ElementCollection(fetch = FetchType.EAGER)
    @CollectionTable(name = "persona_interests", joinColumns = @JoinColumn(name = "persona_id"))
    @Column(name = "interest")
    private List<String> interests;

    @Column(nullable = false)
    private String name;
}
