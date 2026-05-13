package com.jobmarket.api.dto;

import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;
import java.time.LocalDate;

@Data
@NoArgsConstructor
@AllArgsConstructor
public class SkillDemandDTO {
    private Long id;
    private String skillName;
    private Integer demandCount;
    private LocalDate periodStart;
    private LocalDate periodEnd;
    private String region;
    private String industry;
}