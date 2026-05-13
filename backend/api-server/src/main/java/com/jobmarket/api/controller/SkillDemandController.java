package com.jobmarket.api.controller;

import com.jobmarket.api.dto.SkillDemandDTO;
import com.jobmarket.api.dto.TopSkillDTO;
import com.jobmarket.api.entity.SkillDemand;
import com.jobmarket.api.repository.SkillDemandRepository;
import jakarta.persistence.criteria.Predicate;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.PageRequest;
import org.springframework.data.domain.Pageable;
import org.springframework.data.domain.Sort;
import org.springframework.data.jpa.domain.Specification;
import org.springframework.web.bind.annotation.*;
import java.util.List;
import java.util.Map;
import java.util.stream.Collectors;

@RestController
@RequestMapping("/api/skills")
public class SkillDemandController {

    private final SkillDemandRepository skillDemandRepository;

    public SkillDemandController(SkillDemandRepository skillDemandRepository) {
        this.skillDemandRepository = skillDemandRepository;
    }

    @GetMapping
    public Page<SkillDemandDTO> listSkills(
            @RequestParam(required = false) String skillName,
            @RequestParam(required = false) String region,
            @RequestParam(defaultValue = "0") int page,
            @RequestParam(defaultValue = "20") int size
    ) {
        Pageable pageable = PageRequest.of(page, size, Sort.by(Sort.Direction.DESC, "demandCount"));

        Specification<SkillDemand> spec = (root, query, cb) -> {
            List<Predicate> predicates = new java.util.ArrayList<>();
            if (skillName != null && !skillName.isBlank()) {
                predicates.add(cb.like(cb.lower(root.get("skillName")), "%" + skillName.toLowerCase() + "%"));
            }
            if (region != null && !region.isBlank()) {
                predicates.add(cb.equal(cb.lower(root.get("region")), region.toLowerCase()));
            }
            return cb.and(predicates.toArray(new Predicate[0]));
        };

        Page<SkillDemand> result = skillDemandRepository.findAll(spec, pageable);
        return result.map(this::toDTO);
    }

    @GetMapping("/top")
    public List<TopSkillDTO> topSkills(@RequestParam(defaultValue = "20") int count) {
        List<SkillDemand> all = skillDemandRepository.findAll();

        Map<String, Long> aggregated = all.stream()
                .collect(Collectors.groupingBy(
                        s -> s.getSkillName().toLowerCase(),
                        Collectors.summingLong(s -> s.getDemandCount() != null ? s.getDemandCount() : 0)
                ));

        return aggregated.entrySet().stream()
                .sorted(Map.Entry.<String, Long>comparingByValue().reversed())
                .limit(count)
                .map(e -> new TopSkillDTO(e.getKey(), e.getValue()))
                .collect(Collectors.toList());
    }

    private SkillDemandDTO toDTO(SkillDemand s) {
        return new SkillDemandDTO(
                s.getId(),
                s.getSkillName(),
                s.getDemandCount(),
                s.getPeriodStart(),
                s.getPeriodEnd(),
                s.getRegion(),
                s.getIndustry()
        );
    }
}