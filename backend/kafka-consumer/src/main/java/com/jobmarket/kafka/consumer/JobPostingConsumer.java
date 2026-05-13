package com.jobmarket.kafka.consumer;

import com.fasterxml.jackson.core.type.TypeReference;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.jobmarket.kafka.entity.JobListing;
import com.jobmarket.kafka.repository.JobListingRepository;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.kafka.annotation.KafkaListener;
import org.springframework.stereotype.Component;

import java.math.BigDecimal;
import java.time.LocalDateTime;
import java.time.format.DateTimeFormatter;
import java.util.List;
import java.util.Map;

@Slf4j
@Component
@RequiredArgsConstructor
public class JobPostingConsumer {

    private final JobListingRepository jobListingRepository;
    private final ObjectMapper objectMapper;

    @KafkaListener(topics = "job-postings", groupId = "job-market-consumer")
    public void consume(String message) {
        try {
            Map<String, Object> data = objectMapper.readValue(message, new TypeReference<>() {});

            JobListing job = JobListing.builder()
                    .title((String) data.get("title"))
                    .company((String) data.get("company"))
                    .location((String) data.get("location"))
                    .salaryMin(toBigDecimal(data.get("salaryMin")))
                    .salaryMax(toBigDecimal(data.get("salaryMax")))
                    .salaryCurrency((String) data.getOrDefault("salaryCurrency", "USD"))
                    .source((String) data.get("source"))
                    .sourceId((String) data.get("sourceId"))
                    .postedDate(toLocalDateTime(data.get("postedDate")))
                    .jobType((String) data.get("jobType"))
                    .experienceLevel((String) data.get("experienceLevel"))
                    .industry((String) data.get("industry"))
                    .isRemote(toBoolean(data.get("isRemote")))
                    .skills(toSkillsString((List<String>) data.get("skills")))
                    .build();

            jobListingRepository.save(job);
            log.info("Consumed job posting: id={}, title={}, company={}", data.get("jobId"), data.get("title"), data.get("company"));
        } catch (Exception e) {
            log.error("Failed to process job posting message: {}", e.getMessage(), e);
        }
    }

    private BigDecimal toBigDecimal(Object value) {
        if (value == null) return null;
        if (value instanceof Number) return BigDecimal.valueOf(((Number) value).doubleValue());
        return new BigDecimal(value.toString());
    }

    private LocalDateTime toLocalDateTime(Object value) {
        if (value == null) return null;
        return LocalDateTime.parse(value.toString() + "T00:00:00", DateTimeFormatter.ISO_LOCAL_DATE_TIME);
    }

    private Boolean toBoolean(Object value) {
        if (value == null) return false;
        return Boolean.TRUE.equals(value);
    }

    private String toSkillsString(List<String> list) {
        if (list == null || list.isEmpty()) return null;
        return String.join(",", list);
    }
}