package com.jobmarket.api.service;

import com.jobmarket.api.dto.ForecastResultDTO;
import com.jobmarket.api.dto.ForecastTrendDTO;
import com.jobmarket.api.dto.JobListingsTrendDTO;
import com.jobmarket.api.entity.SkillDemand;
import com.jobmarket.api.repository.ForecastResultRepository;
import com.jobmarket.api.repository.JobListingRepository;
import com.jobmarket.api.repository.SkillDemandRepository;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;

import java.math.BigDecimal;
import java.math.RoundingMode;
import java.time.LocalDate;
import java.time.YearMonth;
import java.time.format.DateTimeFormatter;
import java.util.*;
import java.util.stream.Collectors;

@Service
@RequiredArgsConstructor
public class ForecastService {

    private final SkillDemandRepository skillDemandRepository;
    private final ForecastResultRepository forecastResultRepository;
    private final JobListingRepository jobListingRepository;

    private static final LocalDate BASE_DATE = LocalDate.of(2024, 1, 1);
    private static final LocalDate FORECAST_END = LocalDate.of(2027, 12, 1);
    private static final BigDecimal Z_SCORE_95 = new BigDecimal("1.96");
    private static final String MODEL_VERSION = "v2.0-linreg";
    private static final String REGION = "Global";

    public List<ForecastTrendDTO> predictFutureTrends(int topN) {
        List<SkillDemand> allDemands = skillDemandRepository.findAll();

        Map<String, List<SkillDemand>> grouped = allDemands.stream()
                .collect(Collectors.groupingBy(
                        sd -> sd.getSkillName().toLowerCase(),
                        LinkedHashMap::new,
                        Collectors.toList()
                ));

        List<ForecastTrendDTO> trends = new ArrayList<>();

        for (Map.Entry<String, List<SkillDemand>> entry : grouped.entrySet()) {
            String skillName = entry.getKey();
            List<SkillDemand> records = entry.getValue();

            records.sort(Comparator.comparing(SkillDemand::getPeriodStart));

            List<double[]> points = new ArrayList<>();
            for (SkillDemand sd : records) {
                int monthIndex = computeMonthIndex(sd.getPeriodStart());
                points.add(new double[]{monthIndex, sd.getDemandCount()});
            }

            if (points.size() < 2) {
                continue;
            }

            double[] coefficients = fitLinearRegression(points);
            double intercept = coefficients[0];
            double slope = coefficients[1];
            double se = residualStandardError(points, intercept, slope);

            YearMonth lastHistoricalMonth = YearMonth.from(
                    records.stream().map(SkillDemand::getPeriodStart)
                            .max(Comparator.naturalOrder()).orElse(BASE_DATE)
            );
            YearMonth forecastStart = lastHistoricalMonth.plusMonths(1);
            YearMonth forecastEnd = YearMonth.from(FORECAST_END);

            List<ForecastResultDTO> forecasts = new ArrayList<>();
            for (YearMonth ym = forecastStart; !ym.isAfter(forecastEnd); ym = ym.plusMonths(1)) {
                int monthIndex = computeMonthIndex(ym.atDay(1));
                double predicted = intercept + slope * monthIndex;
                predicted = Math.max(0, predicted);

                double lower = Math.max(0, predicted - Z_SCORE_95.doubleValue() * se);
                double upper = predicted + Z_SCORE_95.doubleValue() * se;

                ForecastResultDTO dto = new ForecastResultDTO(
                        null,
                        skillName,
                        ym.atDay(1),
                        BigDecimal.valueOf(predicted).setScale(2, RoundingMode.HALF_UP),
                        BigDecimal.valueOf(lower).setScale(2, RoundingMode.HALF_UP),
                        BigDecimal.valueOf(upper).setScale(2, RoundingMode.HALF_UP),
                        MODEL_VERSION,
                        REGION
                );
                forecasts.add(dto);
            }

            double avgDemand = forecasts.stream()
                    .mapToDouble(f -> f.getPredictedDemand().doubleValue())
                    .average()
                    .orElse(0.0);

            ForecastTrendDTO trend = new ForecastTrendDTO();
            trend.setSkillName(skillName);
            trend.setForecasts(forecasts);
            trend.setAveragePredictedDemand(avgDemand);
            trends.add(trend);
        }

        trends.sort(Comparator.comparingDouble(ForecastTrendDTO::getAveragePredictedDemand).reversed());

        List<ForecastTrendDTO> result = trends.stream()
                .limit(topN)
                .collect(Collectors.toList());

        return result;
    }

    public JobListingsTrendDTO predictJobListingsTrend() {
        List<Object[]> monthlyCounts = jobListingRepository.countByMonth();

        List<double[]> points = new ArrayList<>();
        List<JobListingsTrendDTO.DataPoint> historical = new ArrayList<>();

        DateTimeFormatter fmt = DateTimeFormatter.ofPattern("yyyy-MM-dd");

        for (Object[] row : monthlyCounts) {
            java.sql.Timestamp ts = (java.sql.Timestamp) row[0];
            Long cnt = ((Number) row[1]).longValue();

            LocalDate monthDate = ts.toLocalDateTime().toLocalDate().withDayOfMonth(1);
            int monthIndex = computeMonthIndex(monthDate);

            points.add(new double[]{monthIndex, cnt.doubleValue()});
            historical.add(new JobListingsTrendDTO.DataPoint(
                    monthDate.format(fmt),
                    BigDecimal.valueOf(cnt),
                    null,
                    null
            ));
        }

        if (points.size() < 2) {
            return new JobListingsTrendDTO(historical, Collections.emptyList());
        }

        double[] coefficients = fitLinearRegression(points);
        double intercept = coefficients[0];
        double slope = coefficients[1];
        double se = residualStandardError(points, intercept, slope);

        YearMonth lastDataMonth = YearMonth.from(
                ((java.sql.Timestamp) monthlyCounts.get(monthlyCounts.size() - 1)[0])
                        .toLocalDateTime().toLocalDate()
        );
        YearMonth forecastStart = lastDataMonth.plusMonths(1);
        YearMonth forecastEnd = YearMonth.from(FORECAST_END);

        List<JobListingsTrendDTO.DataPoint> predicted = new ArrayList<>();
        for (YearMonth ym = forecastStart; !ym.isAfter(forecastEnd); ym = ym.plusMonths(1)) {
            int monthIndex = computeMonthIndex(ym.atDay(1));
            double predictedVal = Math.max(0, intercept + slope * monthIndex);
            double lower = Math.max(0, predictedVal - Z_SCORE_95.doubleValue() * se);
            double upper = predictedVal + Z_SCORE_95.doubleValue() * se;

            predicted.add(new JobListingsTrendDTO.DataPoint(
                    ym.atDay(1).format(fmt),
                    BigDecimal.valueOf(predictedVal).setScale(2, RoundingMode.HALF_UP),
                    BigDecimal.valueOf(lower).setScale(2, RoundingMode.HALF_UP),
                    BigDecimal.valueOf(upper).setScale(2, RoundingMode.HALF_UP)
            ));
        }

        return new JobListingsTrendDTO(historical, predicted);
    }

    private int computeMonthIndex(LocalDate date) {
        return (date.getYear() - BASE_DATE.getYear()) * 12 + (date.getMonthValue() - BASE_DATE.getMonthValue());
    }

    private double[] fitLinearRegression(List<double[]> points) {
        int n = points.size();
        double sumX = 0, sumY = 0, sumXY = 0, sumXX = 0;

        for (double[] p : points) {
            double x = p[0];
            double y = p[1];
            sumX += x;
            sumY += y;
            sumXY += x * y;
            sumXX += x * x;
        }

        double denominator = n * sumXX - sumX * sumX;
        double slope;
        if (denominator == 0) {
            slope = 0;
        } else {
            slope = (n * sumXY - sumX * sumY) / denominator;
        }
        double intercept = (sumY - slope * sumX) / n;

        return new double[]{intercept, slope};
    }

    private double residualStandardError(List<double[]> points, double intercept, double slope) {
        int n = points.size();
        double ssResidual = 0;

        for (double[] p : points) {
            double predicted = intercept + slope * p[0];
            double residual = p[1] - predicted;
            ssResidual += residual * residual;
        }

        int df = Math.max(1, n - 2);
        return Math.sqrt(ssResidual / df);
    }
}