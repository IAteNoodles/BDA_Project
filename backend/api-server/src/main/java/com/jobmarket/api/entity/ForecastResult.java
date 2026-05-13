package com.jobmarket.api.entity;

import jakarta.persistence.*;
import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;
import java.math.BigDecimal;
import java.time.LocalDate;
import java.time.LocalDateTime;

@Data
@NoArgsConstructor
@AllArgsConstructor
@Entity
@Table(name = "forecast_results")
public class ForecastResult {
    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @Column(name = "skill_name", nullable = false, length = 255)
    private String skillName;

    @Column(name = "forecast_date", nullable = false)
    private LocalDate forecastDate;

    @Column(name = "predicted_demand", precision = 10, scale = 2)
    private BigDecimal predictedDemand;

    @Column(name = "confidence_lower", precision = 10, scale = 2)
    private BigDecimal confidenceLower;

    @Column(name = "confidence_upper", precision = 10, scale = 2)
    private BigDecimal confidenceUpper;

    @Column(name = "model_version", length = 50)
    private String modelVersion;

    @Column(length = 100)
    private String region;

    @Column(name = "created_at", updatable = false)
    private LocalDateTime createdAt;

    @PrePersist
    protected void onCreate() {
        createdAt = LocalDateTime.now();
    }
}