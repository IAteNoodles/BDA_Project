import axios from 'axios';

const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL
    ? `${import.meta.env.VITE_API_URL}/api`
    : '/api',
});

export interface Job {
  id: number;
  title: string;
  company: string;
  location: string;
  salaryMin: number | null;
  salaryMax: number | null;
  salaryCurrency: string;
  source: string;
  postedDate: string;
  jobType: string;
  experienceLevel: string;
  industry: string;
  isRemote: boolean;
  skills: string[];
}

export interface PaginatedResponse<T> {
  content: T[];
  totalElements: number;
  totalPages: number;
  number: number;
  size: number;
}

export interface DashboardStats {
  totalJobs: number;
  avgSalary: number;
  remoteJobCount: number;
  topIndustries: { name: string; count: number }[];
  topLocations: { name: string; count: number }[];
  topSkills: { name: string; count: number }[];
}

export interface SkillDemand {
  id: number;
  skillName: string;
  demandCount: number;
  periodStart: string;
  periodEnd: string;
  region: string;
  industry: string;
}

export interface TopSkill {
  skillName: string;
  totalDemand: number;
}

export interface Forecast {
  id: number;
  skillName: string;
  forecastDate: string;
  predictedDemand: number;
  confidenceLower: number;
  confidenceUpper: number;
  modelVersion: string;
  region: string;
}

export interface ForecastTrend {
  skillName: string;
  averagePredictedDemand: number;
  forecasts: {
    forecastDate: string;
    predictedDemand: number;
    confidenceLower: number;
    confidenceUpper: number;
  }[];
}

export interface JobsParams {
  page?: number;
  size?: number;
  title?: string;
  location?: string;
  industry?: string;
  experienceLevel?: string;
  isRemote?: boolean;
}

export interface SkillsParams {
  skillName?: string;
  region?: string;
  page?: number;
  size?: number;
}

export interface ForecastsParams {
  skillName?: string;
  page?: number;
  size?: number;
}

export const getHealth = () => api.get<{ status: string }>('/health');

export const getJobs = (params: JobsParams = {}) =>
  api.get<PaginatedResponse<Job>>('/jobs', { params });

export const getJob = (id: number) => api.get<Job>(`/jobs/${id}`);

export const getDashboardStats = () => api.get<DashboardStats>('/jobs/stats');

export const getSkills = (params: SkillsParams = {}) =>
  api.get<PaginatedResponse<SkillDemand>>('/skills', { params });

export const getTopSkills = (count = 20) =>
  api.get<TopSkill[]>('/skills/top', { params: { count } });

export const getForecasts = (params: ForecastsParams = {}) =>
  api.get<PaginatedResponse<Forecast>>('/forecasts', { params });

export const getForecastTrends = (topN = 10) =>
  api.get<ForecastTrend[]>('/forecasts/trends', { params: { topN } });

export interface JobListingsTrend {
  historical: {
    date: string;
    count: number;
    confidenceLower: number | null;
    confidenceUpper: number | null;
  }[];
  predicted: {
    date: string;
    count: number;
    confidenceLower: number;
    confidenceUpper: number;
  }[];
}

export const getJobListingsTrend = () =>
  api.get<JobListingsTrend>('/forecasts/job-listings-trend');

export const getPredictions = (topN = 10) =>
  api.get<ForecastTrend[]>('/forecasts/predictions', { params: { topN } });

export default api;