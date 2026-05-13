package com.jobmarket.api.dto;

import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;
import java.math.BigDecimal;
import java.time.LocalDate;

@Data
@NoArgsConstructor
@AllArgsConstructor
public class ForecastResultDTO {
    private Long id;
    private String skillName;
    private LocalDate forecastDate;
    private BigDecimal predictedDemand;
    private BigDecimal confidenceLower;
    private BigDecimal confidenceUpper;
    private String modelVersion;
    private String region;
}