package com.jobmarket.api.repository;

import com.jobmarket.api.entity.ForecastResult;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.JpaSpecificationExecutor;
import java.time.LocalDate;
import java.util.List;

public interface ForecastResultRepository extends JpaRepository<ForecastResult, Long>, JpaSpecificationExecutor<ForecastResult> {
    List<ForecastResult> findBySkillNameIgnoreCase(String skillName);
    List<ForecastResult> findByForecastDateBetween(LocalDate start, LocalDate end);
}