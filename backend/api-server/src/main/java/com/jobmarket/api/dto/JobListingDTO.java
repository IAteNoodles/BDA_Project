package com.jobmarket.api.dto;

import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;
import java.math.BigDecimal;
import java.time.LocalDateTime;
import java.util.List;

@Data
@NoArgsConstructor
@AllArgsConstructor
public class JobListingDTO {
    private Long id;
    private String title;
    private String company;
    private String location;
    private BigDecimal salaryMin;
    private BigDecimal salaryMax;
    private String salaryCurrency;
    private String source;
    private LocalDateTime postedDate;
    private String jobType;
    private String experienceLevel;
    private String industry;
    private Boolean isRemote;
    private List<String> skills;
}