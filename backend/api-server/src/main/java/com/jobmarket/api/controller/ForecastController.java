package com.jobmarket.api.controller;

import com.jobmarket.api.dto.ForecastResultDTO;
import com.jobmarket.api.dto.ForecastTrendDTO;
import com.jobmarket.api.dto.JobListingsTrendDTO;
import com.jobmarket.api.entity.ForecastResult;
import com.jobmarket.api.repository.ForecastResultRepository;
import com.jobmarket.api.service.ForecastService;
import jakarta.persistence.criteria.Predicate;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.PageRequest;
import org.springframework.data.domain.Pageable;
import org.springframework.data.domain.Sort;
import org.springframework.data.jpa.domain.Specification;
import org.springframework.web.bind.annotation.*;
import java.util.Comparator;
import java.util.List;
import java.util.Map;
import java.util.stream.Collectors;

@RestController
@RequestMapping("/api/forecasts")
public class ForecastController {

    private final ForecastResultRepository forecastResultRepository;
    private final ForecastService forecastService;

    public ForecastController(ForecastResultRepository forecastResultRepository, ForecastService forecastService) {
        this.forecastResultRepository = forecastResultRepository;
        this.forecastService = forecastService;
    }

    @GetMapping
    public Page<ForecastResultDTO> listForecasts(
            @RequestParam(required = false) String skillName,
            @RequestParam(defaultValue = "0") int page,
            @RequestParam(defaultValue = "20") int size
    ) {
        Pageable pageable = PageRequest.of(page, size, Sort.by(Sort.Direction.ASC, "skillName", "forecastDate"));

        Specification<ForecastResult> spec = (root, query, cb) -> {
            List<Predicate> predicates = new java.util.ArrayList<>();
            if (skillName != null && !skillName.isBlank()) {
                predicates.add(cb.like(cb.lower(root.get("skillName")), "%" + skillName.toLowerCase() + "%"));
            }
            return cb.and(predicates.toArray(new Predicate[0]));
        };

        Page<ForecastResult> result = forecastResultRepository.findAll(spec, pageable);
        return result.map(this::toDTO);
    }

    @GetMapping("/trends")
    public List<ForecastTrendDTO> getTrends(@RequestParam(defaultValue = "10") int topN) {
        List<ForecastResult> all = forecastResultRepository.findAll();

        Map<String, Double> latestDemand = all.stream()
                .collect(Collectors.groupingBy(
                        f -> f.getSkillName().toLowerCase(),
                        Collectors.averagingDouble(f -> f.getPredictedDemand() != null ? f.getPredictedDemand().doubleValue() : 0.0)
                ));

        List<String> topSkills = latestDemand.entrySet().stream()
                .sorted(Map.Entry.<String, Double>comparingByValue().reversed())
                .limit(topN)
                .map(Map.Entry::getKey)
                .collect(Collectors.toList());

        return topSkills.stream().map(skill -> {
            List<ForecastResultDTO> forecasts = all.stream()
                    .filter(f -> f.getSkillName().equalsIgnoreCase(skill))
                    .sorted(Comparator.comparing(ForecastResult::getForecastDate))
                    .map(this::toDTO)
                    .collect(Collectors.toList());
            ForecastTrendDTO dto = new ForecastTrendDTO();
            dto.setSkillName(skill);
            dto.setForecasts(forecasts);
            dto.setAveragePredictedDemand(latestDemand.getOrDefault(skill, 0.0));
            return dto;
        }).collect(Collectors.toList());
    }

    @GetMapping("/predictions")
    public List<ForecastTrendDTO> getPredictions(@RequestParam(defaultValue = "10") int topN) {
        return forecastService.predictFutureTrends(topN);
    }

    @GetMapping("/job-listings-trend")
    public JobListingsTrendDTO getJobListingsTrend() {
        return forecastService.predictJobListingsTrend();
    }

    private ForecastResultDTO toDTO(ForecastResult f) {
        return new ForecastResultDTO(
                f.getId(),
                f.getSkillName(),
                f.getForecastDate(),
                f.getPredictedDemand(),
                f.getConfidenceLower(),
                f.getConfidenceUpper(),
                f.getModelVersion(),
                f.getRegion()
        );
    }
}