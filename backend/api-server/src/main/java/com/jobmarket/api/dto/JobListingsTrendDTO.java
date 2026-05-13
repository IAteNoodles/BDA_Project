package com.jobmarket.api.dto;

import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;
import java.math.BigDecimal;
import java.util.List;

@Data
@NoArgsConstructor
@AllArgsConstructor
public class JobListingsTrendDTO {
    private List<DataPoint> historical;
    private List<DataPoint> predicted;

    @Data
    @NoArgsConstructor
    @AllArgsConstructor
    public static class DataPoint {
        private String date;
        private BigDecimal count;
        private BigDecimal confidenceLower;
        private BigDecimal confidenceUpper;
    }
}