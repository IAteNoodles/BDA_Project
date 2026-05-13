package com.jobmarket.api.repository;

import com.jobmarket.api.entity.JobListing;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.JpaSpecificationExecutor;
import org.springframework.data.jpa.repository.Query;
import java.util.List;

public interface JobListingRepository extends JpaRepository<JobListing, Long>, JpaSpecificationExecutor<JobListing> {
    List<JobListing> findByTitleContainingIgnoreCase(String title);
    List<JobListing> findByLocationIgnoreCase(String location);
    List<JobListing> findByIndustryIgnoreCase(String industry);
    List<JobListing> findByExperienceLevelIgnoreCase(String level);
    List<JobListing> findByIsRemoteTrue();

    long countByIsRemoteTrue();

    @Query("SELECT AVG((j.salaryMin + j.salaryMax) / 2.0) FROM JobListing j WHERE j.salaryMin IS NOT NULL AND j.salaryMax IS NOT NULL")
    Double getAverageSalary();

    @Query("SELECT j.industry, COUNT(j) FROM JobListing j WHERE j.industry IS NOT NULL AND j.industry <> '' GROUP BY j.industry ORDER BY COUNT(j) DESC")
    List<Object[]> countByIndustry();

    @Query("SELECT j.location, COUNT(j) FROM JobListing j WHERE j.location IS NOT NULL AND j.location <> '' GROUP BY j.location ORDER BY COUNT(j) DESC")
    List<Object[]> countByLocation();

    @Query(value = "SELECT TRIM(unnest(string_to_array(skills, ','))) AS skill, COUNT(*) AS cnt FROM job_listings WHERE skills IS NOT NULL AND skills <> '' GROUP BY skill ORDER BY cnt DESC", nativeQuery = true)
    List<Object[]> countBySkill();

    @Query(value = "SELECT DATE_TRUNC('month', posted_date) AS month, COUNT(*) AS cnt FROM job_listings WHERE posted_date IS NOT NULL GROUP BY DATE_TRUNC('month', posted_date) ORDER BY month", nativeQuery = true)
    List<Object[]> countByMonth();
}