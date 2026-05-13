package com.jobmarket.api.controller;

import com.jobmarket.api.dto.DashboardStats;
import com.jobmarket.api.dto.JobListingDTO;
import com.jobmarket.api.entity.JobListing;
import com.jobmarket.api.repository.JobListingRepository;
import jakarta.persistence.criteria.Predicate;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.PageRequest;
import org.springframework.data.domain.Pageable;
import org.springframework.data.domain.Sort;
import org.springframework.data.jpa.domain.Specification;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;
import java.math.BigDecimal;
import java.math.RoundingMode;
import java.util.*;
import java.util.stream.Collectors;

@RestController
@RequestMapping("/api/jobs")
public class JobListingController {

    private final JobListingRepository jobListingRepository;

    public JobListingController(JobListingRepository jobListingRepository) {
        this.jobListingRepository = jobListingRepository;
    }

    @GetMapping
    public Page<JobListingDTO> listJobs(
            @RequestParam(defaultValue = "0") int page,
            @RequestParam(defaultValue = "20") int size,
            @RequestParam(required = false) String title,
            @RequestParam(required = false) String location,
            @RequestParam(required = false) String industry,
            @RequestParam(required = false) String experienceLevel,
            @RequestParam(required = false) Boolean isRemote
    ) {
        Pageable pageable = PageRequest.of(page, size, Sort.by(Sort.Direction.DESC, "postedDate"));

        Specification<JobListing> spec = (root, query, cb) -> {
            List<Predicate> predicates = new ArrayList<>();
            if (title != null && !title.isBlank()) {
                predicates.add(cb.like(cb.lower(root.get("title")), "%" + title.toLowerCase() + "%"));
            }
            if (location != null && !location.isBlank()) {
                predicates.add(cb.equal(cb.lower(root.get("location")), location.toLowerCase()));
            }
            if (industry != null && !industry.isBlank()) {
                predicates.add(cb.equal(cb.lower(root.get("industry")), industry.toLowerCase()));
            }
            if (experienceLevel != null && !experienceLevel.isBlank()) {
                predicates.add(cb.equal(cb.lower(root.get("experienceLevel")), experienceLevel.toLowerCase()));
            }
            if (isRemote != null && isRemote) {
                predicates.add(cb.isTrue(root.get("isRemote")));
            }
            return cb.and(predicates.toArray(new Predicate[0]));
        };

        Page<JobListing> result = jobListingRepository.findAll(spec, pageable);
        return result.map(this::toDTO);
    }

    @GetMapping("/{id}")
    public ResponseEntity<JobListingDTO> getJob(@PathVariable Long id) {
        return jobListingRepository.findById(id)
                .map(j -> ResponseEntity.ok(toDTO(j)))
                .orElse(ResponseEntity.notFound().build());
    }

    @GetMapping("/stats")
    public DashboardStats getStats() {
        long totalJobs = jobListingRepository.count();
        long remoteJobCount = jobListingRepository.countByIsRemoteTrue();

        Double avgSalary = jobListingRepository.getAverageSalary();

        List<Object[]> industryRows = jobListingRepository.countByIndustry();
        List<DashboardStats.NameCount> topIndustries = industryRows.stream()
                .limit(10)
                .map(row -> new DashboardStats.NameCount((String) row[0], ((Number) row[1]).longValue()))
                .collect(Collectors.toList());

        List<Object[]> locationRows = jobListingRepository.countByLocation();
        List<DashboardStats.NameCount> topLocations = locationRows.stream()
                .limit(10)
                .map(row -> new DashboardStats.NameCount((String) row[0], ((Number) row[1]).longValue()))
                .collect(Collectors.toList());

        List<Object[]> skillRows = jobListingRepository.countBySkill();
        List<DashboardStats.NameCount> topSkills = skillRows.stream()
                .limit(20)
                .map(row -> new DashboardStats.NameCount((String) row[0], ((Number) row[1]).longValue()))
                .collect(Collectors.toList());

        return new DashboardStats(
                totalJobs,
                BigDecimal.valueOf(avgSalary != null ? avgSalary : 0.0).setScale(2, RoundingMode.HALF_UP).doubleValue(),
                remoteJobCount,
                topIndustries,
                topLocations,
                topSkills
        );
    }

    private JobListingDTO toDTO(JobListing j) {
        List<String> skillsList = null;
        if (j.getSkills() != null && !j.getSkills().isBlank()) {
            skillsList = Arrays.stream(j.getSkills().split(","))
                    .map(String::trim)
                    .filter(s -> !s.isEmpty())
                    .collect(Collectors.toList());
        }
        return new JobListingDTO(
                j.getId(),
                j.getTitle(),
                j.getCompany(),
                j.getLocation(),
                j.getSalaryMin(),
                j.getSalaryMax(),
                j.getSalaryCurrency(),
                j.getSource(),
                j.getPostedDate(),
                j.getJobType(),
                j.getExperienceLevel(),
                j.getIndustry(),
                j.getIsRemote(),
                skillsList
        );
    }
}