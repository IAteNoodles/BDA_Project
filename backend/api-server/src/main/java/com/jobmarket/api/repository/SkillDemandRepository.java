package com.jobmarket.api.repository;

import com.jobmarket.api.entity.SkillDemand;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.JpaSpecificationExecutor;
import java.time.LocalDate;
import java.util.List;

public interface SkillDemandRepository extends JpaRepository<SkillDemand, Long>, JpaSpecificationExecutor<SkillDemand> {
    List<SkillDemand> findBySkillNameIgnoreCase(String skillName);
    List<SkillDemand> findByPeriodStartBetween(LocalDate start, LocalDate end);
    List<SkillDemand> findByRegionIgnoreCase(String region);
}