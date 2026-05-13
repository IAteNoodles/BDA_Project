import { useState, useEffect } from 'react';
import { Bar, Line } from 'react-chartjs-2';
import { format, parseISO } from 'date-fns';
import {
  getDashboardStats,
  getTopSkills,
  getForecastTrends,
  getJobs,
  getJobListingsTrend,
  getPredictions,
  type DashboardStats,
  type TopSkill,
  type ForecastTrend,
  type Job,
  type JobListingsTrend,
} from '../services/api';
import '../services/chartConfig';

const CHART_COLORS = [
  'rgba(59, 130, 246, 0.8)',
  'rgba(16, 185, 129, 0.8)',
  'rgba(245, 158, 11, 0.8)',
  'rgba(239, 68, 68, 0.8)',
  'rgba(139, 92, 246, 0.8)',
  'rgba(236, 72, 153, 0.8)',
  'rgba(20, 184, 166, 0.8)',
  'rgba(249, 115, 22, 0.8)',
  'rgba(99, 102, 241, 0.8)',
  'rgba(34, 197, 94, 0.8)',
];

const LINE_COLORS = [
  { border: 'rgb(59, 130, 246)', bg: 'rgba(59, 130, 246, 0.1)' },
  { border: 'rgb(16, 185, 129)', bg: 'rgba(16, 185, 129, 0.1)' },
  { border: 'rgb(245, 158, 11)', bg: 'rgba(245, 158, 11, 0.1)' },
  { border: 'rgb(239, 68, 68)', bg: 'rgba(239, 68, 68, 0.1)' },
  { border: 'rgb(139, 92, 246)', bg: 'rgba(139, 92, 246, 0.1)' },
];

const PREDICTION_COLORS = [
  { border: 'rgb(59, 130, 246)', bg: 'rgba(59, 130, 246, 0.1)' },
  { border: 'rgb(16, 185, 129)', bg: 'rgba(16, 185, 129, 0.1)' },
  { border: 'rgb(245, 158, 11)', bg: 'rgba(245, 158, 11, 0.1)' },
  { border: 'rgb(239, 68, 68)', bg: 'rgba(239, 68, 68, 0.1)' },
  { border: 'rgb(139, 92, 246)', bg: 'rgba(139, 92, 246, 0.1)' },
  { border: 'rgb(236, 72, 153)', bg: 'rgba(236, 72, 153, 0.1)' },
  { border: 'rgb(20, 184, 166)', bg: 'rgba(20, 184, 166, 0.1)' },
  { border: 'rgb(249, 115, 22)', bg: 'rgba(249, 115, 22, 0.1)' },
  { border: 'rgb(99, 102, 241)', bg: 'rgba(99, 102, 241, 0.1)' },
  { border: 'rgb(34, 197, 94)', bg: 'rgba(34, 197, 94, 0.1)' },
];

function StatCard({
  title,
  value,
  icon,
}: {
  title: string;
  value: string | number;
  icon: React.ReactNode;
}) {
  return (
    <div className="rounded-lg bg-white p-6 shadow">
      <div className="flex items-center">
        <div className="flex-shrink-0">
          <div className="flex h-12 w-12 items-center justify-center rounded-md bg-blue-50 text-blue-600">
            {icon}
          </div>
        </div>
        <div className="ml-4">
          <p className="text-sm font-medium text-gray-500">{title}</p>
          <p className="text-2xl font-semibold text-gray-900">{value}</p>
        </div>
      </div>
    </div>
  );
}

function formatSalary(min: number | null, max: number | null, currency: string) {
  const fmt = (v: number) =>
    `${currency === 'USD' ? '$' : currency}${(v / 1000).toFixed(0)}k`;
  if (min != null && max != null) return `${fmt(min)} – ${fmt(max)}`;
  if (min != null) return `From ${fmt(min)}`;
  if (max != null) return `Up to ${fmt(max)}`;
  return 'N/A';
}

export default function Dashboard() {
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [topSkills, setTopSkills] = useState<TopSkill[]>([]);
  const [trends, setTrends] = useState<ForecastTrend[]>([]);
  const [recentJobs, setRecentJobs] = useState<Job[]>([]);
  const [jobListingsTrend, setJobListingsTrend] = useState<JobListingsTrend | null>(null);
  const [predictions, setPredictions] = useState<ForecastTrend[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function load() {
      try {
        const [statsRes, skillsRes, trendsRes, jobsRes, listingsTrendRes, predictionsRes] = await Promise.all([
          getDashboardStats(),
          getTopSkills(10),
          getForecastTrends(),
          getJobs({ page: 0, size: 10 }),
          getJobListingsTrend(),
          getPredictions(5),
        ]);
        setStats(statsRes.data);
        setTopSkills(skillsRes.data);
        setTrends(trendsRes.data);
        setRecentJobs(jobsRes.data.content);
        setJobListingsTrend(listingsTrendRes.data);
        setPredictions(predictionsRes.data);
      } catch (err: any) {
        setError(err.message || 'Failed to load dashboard data');
      } finally {
        setLoading(false);
      }
    }
    load();
  }, []);

  if (loading) {
    return (
      <div className="flex h-64 items-center justify-center">
        <div className="h-8 w-8 animate-spin rounded-full border-4 border-blue-500 border-t-transparent" />
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex h-64 items-center justify-center">
        <div className="rounded-lg bg-red-50 p-6 text-red-700">
          <p className="font-medium">Error loading dashboard</p>
          <p className="text-sm">{error}</p>
        </div>
      </div>
    );
  }

  const top5Trends = trends.slice(0, 5);

  const barChartData = {
    labels: topSkills.map((s) => s.skillName),
    datasets: [
      {
        label: 'Demand Count',
        data: topSkills.map((s) => s.totalDemand),
        backgroundColor: CHART_COLORS,
        borderRadius: 4,
      },
    ],
  };

  const allDates = top5Trends
    .flatMap((t) => t.forecasts.map((f) => f.forecastDate))
    .filter((v, i, a) => a.indexOf(v) === i)
    .sort();

  const lineChartData = {
    labels: allDates.map((d) => format(new Date(d), 'MMM yyyy')),
    datasets: top5Trends.map((trend, i) => {
      const dateMap = new Map(
        trend.forecasts.map((f) => [f.forecastDate, f])
      );
      return {
        label: trend.skillName,
        data: allDates.map(
          (d) => dateMap.get(d)?.predictedDemand ?? null
        ),
        borderColor: LINE_COLORS[i].border,
        backgroundColor: LINE_COLORS[i].bg,
        tension: 0.3,
        fill: false,
        pointRadius: 3,
      };
    }),
  };

  const confidenceDatasets = top5Trends.flatMap((trend, i) => {
    const dateMap = new Map(
      trend.forecasts.map((f) => [f.forecastDate, f])
    );
    return [
      {
        label: `${trend.skillName} Upper`,
        data: allDates.map(
          (d) => dateMap.get(d)?.confidenceUpper ?? null
        ),
        borderColor: 'transparent',
        backgroundColor: LINE_COLORS[i].bg,
        fill: '+1',
        pointRadius: 0,
      },
      {
        label: `${trend.skillName} Lower`,
        data: allDates.map(
          (d) => dateMap.get(d)?.confidenceLower ?? null
        ),
        borderColor: 'transparent',
        backgroundColor: 'transparent',
        fill: false,
        pointRadius: 0,
      },
    ];
  });

  const lineChartWithConfidence = {
    labels: lineChartData.labels,
    datasets: [...confidenceDatasets, ...lineChartData.datasets],
  };

  let jobListingsChartData = null;
  if (jobListingsTrend) {
    const allMonths = [
      ...jobListingsTrend.historical.map((h) => h.date),
      ...jobListingsTrend.predicted.map((p) => p.date),
    ].sort();

    const historicalMap = new Map(
      jobListingsTrend.historical.map((h) => [h.date, h])
    );
    const predictedMap = new Map(
      jobListingsTrend.predicted.map((p) => [p.date, p])
    );

    jobListingsChartData = {
      labels: allMonths.map((d) => format(parseISO(d), 'MMM yyyy')),
      datasets: [
        {
          label: 'Upper Confidence',
          data: allMonths.map((d) => {
            const h = historicalMap.get(d);
            const p = predictedMap.get(d);
            return p?.confidenceUpper ?? null;
          }),
          borderColor: 'transparent',
          backgroundColor: 'rgba(59, 130, 246, 0.08)',
          fill: '+1',
          pointRadius: 0,
        },
        {
          label: 'Lower Confidence',
          data: allMonths.map((d) => {
            const p = predictedMap.get(d);
            return p?.confidenceLower ?? null;
          }),
          borderColor: 'transparent',
          backgroundColor: 'transparent',
          fill: false,
          pointRadius: 0,
        },
        {
          label: 'Historical',
          data: allMonths.map((d) => {
            const h = historicalMap.get(d);
            return h ? h.count : null;
          }),
          borderColor: 'rgb(59, 130, 246)',
          backgroundColor: 'rgba(59, 130, 246, 0.1)',
          tension: 0.3,
          fill: false,
          pointRadius: 2,
          borderWidth: 2,
        },
        {
          label: 'ML Prediction',
          data: allMonths.map((d) => {
            const p = predictedMap.get(d);
            return p ? p.count : null;
          }),
          borderColor: 'rgb(239, 68, 68)',
          backgroundColor: 'rgba(239, 68, 68, 0.1)',
          borderDash: [6, 3],
          tension: 0.3,
          fill: false,
          pointRadius: 2,
          borderWidth: 2,
        },
      ],
    };
  }

  const predAllDates = predictions
    .flatMap((t) => t.forecasts.map((f) => f.forecastDate))
    .filter((v, i, a) => a.indexOf(v) === i)
    .sort();

  const predLineDatasets = predictions.map((trend, i) => {
    const color = PREDICTION_COLORS[i % PREDICTION_COLORS.length];
    const dateMap = new Map(trend.forecasts.map((f) => [f.forecastDate, f]));
    return {
      label: trend.skillName,
      data: predAllDates.map((d) => {
        const f = dateMap.get(d);
        return f ? f.predictedDemand : null;
      }),
      borderColor: color.border,
      backgroundColor: color.bg,
      tension: 0.3,
      fill: false,
      pointRadius: 2,
      borderWidth: 2,
    };
  });

  const predConfidenceDatasets = predictions.flatMap((trend, i) => {
    const color = PREDICTION_COLORS[i % PREDICTION_COLORS.length];
    const dateMap = new Map(trend.forecasts.map((f) => [f.forecastDate, f]));
    return [
      {
        label: `${trend.skillName} Upper`,
        data: predAllDates.map((d) => {
          const f = dateMap.get(d);
          return f ? f.confidenceUpper : null;
        }),
        borderColor: 'transparent',
        backgroundColor: color.bg,
        fill: '+1',
        pointRadius: 0,
      },
      {
        label: `${trend.skillName} Lower`,
        data: predAllDates.map((d) => {
          const f = dateMap.get(d);
          return f ? f.confidenceLower : null;
        }),
        borderColor: 'transparent',
        backgroundColor: 'transparent',
        fill: false,
        pointRadius: 0,
      },
    ];
  });

  const predictionChartData = {
    labels: predAllDates.map((d) => format(parseISO(d), 'MMM yyyy')),
    datasets: [...predConfidenceDatasets, ...predLineDatasets],
  };

  return (
    <div className="space-y-6">
      <div className="grid grid-cols-1 gap-5 sm:grid-cols-3">
        <StatCard
          title="Total Jobs"
          value={stats?.totalJobs?.toLocaleString() ?? '—'}
          icon={
            <svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 13.255A23.931 23.931 0 0112 15c-3.183 0-6.22-.62-9-1.745M16 6V4a2 2 0 00-2-2h-4a2 2 0 00-2 2v2m4 6h.01M5 20h14a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
            </svg>
          }
        />
        <StatCard
          title="Average Salary"
          value={stats?.avgSalary ? `$${(stats.avgSalary / 1000).toFixed(1)}k` : '—'}
          icon={
            <svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
          }
        />
        <StatCard
          title="Remote Jobs"
          value={stats?.remoteJobCount?.toLocaleString() ?? '—'}
          icon={
            <svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6" />
            </svg>
          }
        />
      </div>

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        <div className="rounded-lg bg-white p-6 shadow">
          <h3 className="mb-4 text-lg font-medium text-gray-900">Top 10 Skills by Demand</h3>
          <div className="h-80">
            <Bar
              data={barChartData}
              options={{
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                  legend: { display: false },
                  title: { display: false },
                },
                scales: {
                  x: { ticks: { maxRotation: 45, minRotation: 45 } },
                  y: { beginAtZero: true },
                },
              }}
            />
          </div>
        </div>

        <div className="rounded-lg bg-white p-6 shadow">
          <h3 className="mb-4 text-lg font-medium text-gray-900">Forecast Trends — Top 5 Skills</h3>
          <div className="h-96">
            <Line
              data={lineChartWithConfidence}
              options={{
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                  legend: {
                    position: 'bottom',
                    labels: {
                      filter: (item) => !item.text.includes('Upper') && !item.text.includes('Lower'),
                    },
                  },
                  tooltip: {
                    mode: 'index',
                    intersect: false,
                  },
                },
                scales: {
                  x: {
                    ticks: {
                      maxRotation: 45,
                      minRotation: 45,
                      autoSkip: true,
                      maxTicksLimit: 12,
                    },
                  },
                  y: { beginAtZero: true },
                },
                interaction: {
                  mode: 'nearest',
                  axis: 'x',
                  intersect: false,
                },
              }}
            />
          </div>
        </div>
      </div>

      {jobListingsChartData && (
        <div className="rounded-lg bg-white p-6 shadow">
          <h3 className="mb-4 text-lg font-medium text-gray-900">Job Listings Forecast — ML Prediction (to 2027)</h3>
          <p className="mb-4 text-sm text-gray-500">Linear regression model trained on historical posting data. Dashed line = ML prediction with 95% confidence band.</p>
          <div className="h-96">
            <Line
              data={jobListingsChartData}
              options={{
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                  legend: {
                    position: 'bottom',
                    labels: {
                      filter: (item) => !item.text.includes('Confidence'),
                    },
                  },
                  tooltip: {
                    mode: 'index',
                    intersect: false,
                  },
                },
                scales: {
                  x: {
                    ticks: {
                      maxRotation: 45,
                      minRotation: 45,
                      autoSkip: true,
                      maxTicksLimit: 15,
                    },
                  },
                  y: {
                    beginAtZero: true,
                    title: {
                      display: true,
                      text: 'Job Listings Count',
                    },
                  },
                },
                interaction: {
                  mode: 'nearest',
                  axis: 'x',
                  intersect: false,
                },
              }}
            />
          </div>
        </div>
      )}

      {predictions.length > 0 && (
        <div className="rounded-lg bg-white p-6 shadow">
          <h3 className="mb-4 text-lg font-medium text-gray-900">Skill Demand Predictions — ML Forecast (to 2027)</h3>
          <p className="mb-4 text-sm text-gray-500">Linear regression model trained on skill demand history. Top 5 skills by predicted average demand.</p>
          <div className="h-96">
            <Line
              data={predictionChartData}
              options={{
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                  legend: {
                    position: 'bottom',
                    labels: {
                      filter: (item) => !item.text.includes('Upper') && !item.text.includes('Lower'),
                    },
                  },
                  tooltip: {
                    mode: 'index',
                    intersect: false,
                  },
                },
                scales: {
                  x: {
                    ticks: {
                      maxRotation: 45,
                      minRotation: 45,
                      autoSkip: true,
                      maxTicksLimit: 15,
                    },
                  },
                  y: {
                    beginAtZero: true,
                    title: {
                      display: true,
                      text: 'Predicted Demand',
                    },
                  },
                },
                interaction: {
                  mode: 'nearest',
                  axis: 'x',
                  intersect: false,
                },
              }}
            />
          </div>
        </div>
      )}

      <div className="rounded-lg bg-white shadow">
        <div className="border-b border-gray-200 px-6 py-4">
          <h3 className="text-lg font-medium text-gray-900">Recent Job Listings</h3>
        </div>
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500">Title</th>
                <th className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500">Company</th>
                <th className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500">Location</th>
                <th className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500">Salary</th>
                <th className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500">Industry</th>
                <th className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500">Skills</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-200 bg-white">
              {recentJobs.map((job) => (
                <tr key={job.id} className="hover:bg-gray-50">
                  <td className="whitespace-nowrap px-6 py-4 text-sm font-medium text-gray-900">{job.title}</td>
                  <td className="whitespace-nowrap px-6 py-4 text-sm text-gray-500">{job.company}</td>
                  <td className="whitespace-nowrap px-6 py-4 text-sm text-gray-500">{job.location}</td>
                  <td className="whitespace-nowrap px-6 py-4 text-sm text-gray-500">
                    {formatSalary(job.salaryMin, job.salaryMax, job.salaryCurrency)}
                  </td>
                  <td className="whitespace-nowrap px-6 py-4 text-sm text-gray-500">{job.industry}</td>
                  <td className="px-6 py-4">
                    <div className="flex flex-wrap gap-1">
                      {job.skills.slice(0, 3).map((skill) => (
                        <span key={skill} className="inline-flex rounded-full bg-blue-100 px-2 py-0.5 text-xs font-medium text-blue-800">
                          {skill}
                        </span>
                      ))}
                      {job.skills.length > 3 && (
                        <span className="inline-flex rounded-full bg-gray-100 px-2 py-0.5 text-xs font-medium text-gray-600">
                          +{job.skills.length - 3}
                        </span>
                      )}
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}