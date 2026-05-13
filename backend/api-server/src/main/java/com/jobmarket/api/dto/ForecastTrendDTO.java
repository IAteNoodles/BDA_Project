package com.jobmarket.api.dto;

import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;
import java.util.List;

@Data
@NoArgsConstructor
@AllArgsConstructor
public class ForecastTrendDTO {
    private String skillName;
    private List<ForecastResultDTO> forecasts;
    private double averagePredictedDemand;
}