package com.jobmarket.api.service;

import com.jobmarket.api.dto.ForecastResultDTO;
import com.jobmarket.api.dto.ForecastTrendDTO;
import com.jobmarket.api.dto.JobListingsTrendDTO;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.core.ParameterizedTypeReference;
import org.springframework.http.HttpMethod;
import org.springframework.http.ResponseEntity;
import org.springframework.stereotype.Service;
import org.springframework.web.client.RestTemplate;

import java.math.BigDecimal;
import java.time.LocalDate;
import java.util.Collections;
import java.util.List;
import java.util.Map;
import java.util.stream.Collectors;

@Service
@Slf4j
public class ForecastService {

    private final RestTemplate restTemplate;
    private final String mlServiceUrl;

    public ForecastService(@Value("${ml.service.url:http://localhost:5000}") String mlServiceUrl) {
        this.restTemplate = new RestTemplate();
        this.mlServiceUrl = mlServiceUrl;
    }

    public List<ForecastTrendDTO> predictFutureTrends(int topN) {
        try {
            String url = mlServiceUrl + "/ml/predictions?topN=" + topN;
            ResponseEntity<List<Map<String, Object>>> response = restTemplate.exchange(
                    url,
                    HttpMethod.GET,
                    null,
                    new ParameterizedTypeReference<>() {}
            );

            List<Map<String, Object>> body = response.getBody();
            if (body == null) return Collections.emptyList();

            return body.stream().map(this::mapToForecastTrendDTO).collect(Collectors.toList());
        } catch (Exception e) {
            log.error("Failed to call ML service for predictions: {}", e.getMessage());
            return Collections.emptyList();
        }
    }

    public JobListingsTrendDTO predictJobListingsTrend() {
        try {
            String url = mlServiceUrl + "/ml/job-listings-trend";
            ResponseEntity<Map<String, Object>> response = restTemplate.exchange(
                    url,
                    HttpMethod.GET,
                    null,
                    new ParameterizedTypeReference<>() {}
            );

            Map<String, Object> body = response.getBody();
            if (body == null) return new JobListingsTrendDTO(Collections.emptyList(), Collections.emptyList());

            List<Map<String, Object>> historical = (List<Map<String, Object>>) body.get("historical");
            List<Map<String, Object>> predicted = (List<Map<String, Object>>) body.get("predicted");

            List<JobListingsTrendDTO.DataPoint> histPoints = historical != null
                    ? historical.stream().map(this::mapToDataPoint).collect(Collectors.toList())
                    : Collections.emptyList();
            List<JobListingsTrendDTO.DataPoint> predPoints = predicted != null
                    ? predicted.stream().map(this::mapToDataPoint).collect(Collectors.toList())
                    : Collections.emptyList();

            return new JobListingsTrendDTO(histPoints, predPoints);
        } catch (Exception e) {
            log.error("Failed to call ML service for job listings trend: {}", e.getMessage());
            return new JobListingsTrendDTO(Collections.emptyList(), Collections.emptyList());
        }
    }

    @SuppressWarnings("unchecked")
    private ForecastTrendDTO mapToForecastTrendDTO(Map<String, Object> map) {
        ForecastTrendDTO dto = new ForecastTrendDTO();
        dto.setSkillName((String) map.get("skillName"));
        dto.setAveragePredictedDemand(((Number) map.get("averagePredictedDemand")).doubleValue());

        List<Map<String, Object>> forecasts = (List<Map<String, Object>>) map.get("forecasts");
        if (forecasts != null) {
             List<ForecastResultDTO> forecastDTOs = forecasts.stream().map(f -> {
                 String dateStr = (String) f.get("forecastDate");
                 return new ForecastResultDTO(
                         null,
                         (String) f.get("skillName") != null ? (String) f.get("skillName") : dto.getSkillName(),
                         LocalDate.parse(dateStr),
                         toBigDecimal(f.get("predictedDemand")),
                         toBigDecimal(f.get("confidenceLower")),
                         toBigDecimal(f.get("confidenceUpper")),
                         "SARIMA(1,1,1)(1,1,1,12)",
                         "Global"
                 );
            }).collect(Collectors.toList());
            dto.setForecasts(forecastDTOs);
        }

        return dto;
    }

    private JobListingsTrendDTO.DataPoint mapToDataPoint(Map<String, Object> map) {
        return new JobListingsTrendDTO.DataPoint(
                (String) map.get("date"),
                toBigDecimal(map.get("count")),
                map.get("confidenceLower") != null ? toBigDecimal(map.get("confidenceLower")) : null,
                map.get("confidenceUpper") != null ? toBigDecimal(map.get("confidenceUpper")) : null
        );
    }

    private BigDecimal toBigDecimal(Object value) {
        if (value == null) return BigDecimal.ZERO;
        if (value instanceof BigDecimal) return (BigDecimal) value;
        if (value instanceof Number) return BigDecimal.valueOf(((Number) value).doubleValue()).setScale(2, java.math.RoundingMode.HALF_UP);
        return new BigDecimal(value.toString()).setScale(2, java.math.RoundingMode.HALF_UP);
    }
}