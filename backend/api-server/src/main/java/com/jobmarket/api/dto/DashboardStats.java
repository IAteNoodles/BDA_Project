package com.jobmarket.api.dto;

import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;
import java.util.List;

@Data
@NoArgsConstructor
@AllArgsConstructor
public class DashboardStats {
    private long totalJobs;
    private double avgSalary;
    private long remoteJobCount;
    private List<NameCount> topIndustries;
    private List<NameCount> topLocations;
    private List<NameCount> topSkills;

    @Data
    @NoArgsConstructor
    @AllArgsConstructor
    public static class NameCount {
        private String name;
        private long count;
    }
}