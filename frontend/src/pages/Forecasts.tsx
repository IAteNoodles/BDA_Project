import { useState, useEffect } from "react";
import { Line } from "react-chartjs-2";
import { format, parseISO } from "date-fns";
import {
  getForecastTrends,
  getForecasts,
  getPredictions,
  getJobListingsTrend,
  type ForecastTrend,
  type Forecast,
  type JobListingsTrend,
} from "../services/api";
import "../services/chartConfig";

const LINE_COLORS = [
  { border: "rgb(59, 130, 246)", bg: "rgba(59, 130, 246, 0.1)" },
  { border: "rgb(16, 185, 129)", bg: "rgba(16, 185, 129, 0.1)" },
  { border: "rgb(245, 158, 11)", bg: "rgba(245, 158, 11, 0.1)" },
  { border: "rgb(239, 68, 68)", bg: "rgba(239, 68, 68, 0.1)" },
  { border: "rgb(139, 92, 246)", bg: "rgba(139, 92, 246, 0.1)" },
  { border: "rgb(236, 72, 153)", bg: "rgba(236, 72, 153, 0.1)" },
  { border: "rgb(20, 184, 166)", bg: "rgba(20, 184, 166, 0.1)" },
  { border: "rgb(249, 115, 22)", bg: "rgba(249, 115, 22, 0.1)" },
  { border: "rgb(99, 102, 241)", bg: "rgba(99, 102, 241, 0.1)" },
  { border: "rgb(34, 197, 94)", bg: "rgba(34, 197, 94, 0.1)" },
];

export default function Forecasts() {
  const [trends, setTrends] = useState<ForecastTrend[]>([]);
  const [predictions, setPredictions] = useState<ForecastTrend[]>([]);
  const [jobListingsTrend, setJobListingsTrend] =
    useState<JobListingsTrend | null>(null);
  const [forecasts, setForecasts] = useState<Forecast[]>([]);
  const [totalElements, setTotalElements] = useState(0);
  const [page, setPage] = useState(0);
  const [skillFilter, setSkillFilter] = useState("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    setLoading(true);
    Promise.all([
      getForecastTrends(),
      getPredictions(10),
      getJobListingsTrend(),
    ])
      .then(([trendsRes, predictionsRes, listingsRes]) => {
        setTrends(trendsRes.data);
        setPredictions(predictionsRes.data);
        setJobListingsTrend(listingsRes.data);
      })
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  useEffect(() => {
    setLoading(true);
    setError(null);
    getForecasts({ page, size: 20, skillName: skillFilter || undefined })
      .then((res) => {
        setForecasts(res.data.content);
        setTotalElements(res.data.totalElements);
      })
      .catch((err) => setError(err.message || "Failed to load forecasts"))
      .finally(() => setLoading(false));
  }, [page, skillFilter]);

  const allDates = trends
    .flatMap((t) => t.forecasts.map((f) => f.forecastDate))
    .filter((v, i, a) => a.indexOf(v) === i)
    .sort();

  const lineDatasets = trends.slice(0, 10).map((trend, i) => {
    const color = LINE_COLORS[i % LINE_COLORS.length];
    const dateMap = new Map(trend.forecasts.map((f) => [f.forecastDate, f]));
    return {
      label: trend.skillName,
      data: allDates.map((d) => dateMap.get(d)?.predictedDemand ?? null),
      borderColor: color.border,
      backgroundColor: color.bg,
      tension: 0.3,
      fill: false,
      pointRadius: 3,
    };
  });

  const confidenceDatasets = trends.slice(0, 10).flatMap((trend, i) => {
    const color = LINE_COLORS[i % LINE_COLORS.length];
    const dateMap = new Map(trend.forecasts.map((f) => [f.forecastDate, f]));
    return [
      {
        label: `${trend.skillName} Upper`,
        data: allDates.map((d) => dateMap.get(d)?.confidenceUpper ?? null),
        borderColor: "transparent",
        backgroundColor: color.bg,
        fill: "+1",
        pointRadius: 0,
      },
      {
        label: `${trend.skillName} Lower`,
        data: allDates.map((d) => dateMap.get(d)?.confidenceLower ?? null),
        borderColor: "transparent",
        backgroundColor: "transparent",
        fill: false,
        pointRadius: 0,
      },
    ];
  });

  const chartData = {
    labels: allDates.map((d) => format(parseISO(d), "MMM yyyy")),
    datasets: [...confidenceDatasets, ...lineDatasets],
  };

  const predAllDates = predictions
    .flatMap((t) => t.forecasts.map((f) => f.forecastDate))
    .filter((v, i, a) => a.indexOf(v) === i)
    .sort();

  const predLineDatasets = predictions.map((trend, i) => {
    const color = LINE_COLORS[i % LINE_COLORS.length];
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
    const color = LINE_COLORS[i % LINE_COLORS.length];
    const dateMap = new Map(trend.forecasts.map((f) => [f.forecastDate, f]));
    return [
      {
        label: `${trend.skillName} Upper`,
        data: predAllDates.map((d) => {
          const f = dateMap.get(d);
          return f ? f.confidenceUpper : null;
        }),
        borderColor: "transparent",
        backgroundColor: color.bg,
        fill: "+1",
        pointRadius: 0,
      },
      {
        label: `${trend.skillName} Lower`,
        data: predAllDates.map((d) => {
          const f = dateMap.get(d);
          return f ? f.confidenceLower : null;
        }),
        borderColor: "transparent",
        backgroundColor: "transparent",
        fill: false,
        pointRadius: 0,
      },
    ];
  });

  const predictionChartData = {
    labels: predAllDates.map((d) => format(parseISO(d), "MMM yyyy")),
    datasets: [...predConfidenceDatasets, ...predLineDatasets],
  };

  let jobListingsChartData = null;
  if (jobListingsTrend) {
    const allMonths = [
      ...jobListingsTrend.historical.map((h) => h.date),
      ...jobListingsTrend.predicted.map((p) => p.date),
    ].sort();

    const historicalMap = new Map(
      jobListingsTrend.historical.map((h) => [h.date, h]),
    );
    const predictedMap = new Map(
      jobListingsTrend.predicted.map((p) => [p.date, p]),
    );

    jobListingsChartData = {
      labels: allMonths.map((d) => format(parseISO(d), "MMM yyyy")),
      datasets: [
        {
          label: "Prediction Upper CI",
          data: allMonths.map((d) => {
            const p = predictedMap.get(d);
            return p?.confidenceUpper ?? null;
          }),
          borderColor: "transparent",
          backgroundColor: "rgba(239, 68, 68, 0.08)",
          fill: "+1",
          pointRadius: 0,
        },
        {
          label: "Prediction Lower CI",
          data: allMonths.map((d) => {
            const p = predictedMap.get(d);
            return p?.confidenceLower ?? null;
          }),
          borderColor: "transparent",
          backgroundColor: "transparent",
          fill: false,
          pointRadius: 0,
        },
        {
          label: "Historical",
          data: allMonths.map((d) => {
            const h = historicalMap.get(d);
            return h ? h.count : null;
          }),
          borderColor: "rgb(59, 130, 246)",
          backgroundColor: "rgba(59, 130, 246, 0.1)",
          tension: 0.3,
          fill: false,
          pointRadius: 2,
          borderWidth: 2,
        },
        {
          label: "ML Prediction",
          data: allMonths.map((d) => {
            const p = predictedMap.get(d);
            return p ? p.count : null;
          }),
          borderColor: "rgb(239, 68, 68)",
          backgroundColor: "rgba(239, 68, 68, 0.1)",
          borderDash: [6, 3],
          tension: 0.3,
          fill: false,
          pointRadius: 2,
          borderWidth: 2,
        },
      ],
    };
  }

  return (
    <div className="space-y-6">
      <div className="rounded-lg bg-white p-6 shadow">
        <h3 className="mb-4 text-lg font-medium text-gray-900">
          Forecast Trends with Confidence Intervals
        </h3>
        <div className="h-[28rem]">
          <Line
            data={chartData}
            options={{
              responsive: true,
              maintainAspectRatio: false,
              plugins: {
                legend: {
                  position: "bottom",
                  labels: {
                    filter: (item) =>
                      !item.text.includes("Upper") &&
                      !item.text.includes("Lower"),
                  },
                },
                tooltip: {
                  mode: "index",
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
                mode: "nearest",
                axis: "x",
                intersect: false,
              },
            }}
          />
        </div>
      </div>

      {jobListingsChartData && (
        <div className="rounded-lg bg-white p-6 shadow">
          <h3 className="mb-2 text-lg font-medium text-gray-900">
            Job Listings Forecast — ML Prediction (to 2027)
          </h3>
          <p className="mb-4 text-sm text-gray-500">
            Linear regression model trained on historical posting data. Dashed
            line = ML prediction with 95% confidence band.
          </p>
          <div className="h-[28rem]">
            <Line
              data={jobListingsChartData}
              options={{
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                  legend: {
                    position: "bottom",
                    labels: {
                      filter: (item) =>
                        !item.text.includes("CI") &&
                        !item.text.includes("Confidence"),
                    },
                  },
                  tooltip: {
                    mode: "index",
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
                      text: "Job Listings Count",
                    },
                  },
                },
                interaction: {
                  mode: "nearest",
                  axis: "x",
                  intersect: false,
                },
              }}
            />
          </div>
        </div>
      )}

      {predictions.length > 0 && (
        <div className="rounded-lg bg-white p-6 shadow">
          <h3 className="mb-2 text-lg font-medium text-gray-900">
            Skill Demand ML Predictions (to 2027)
          </h3>
          <p className="mb-4 text-sm text-gray-500">
            Linear regression forecast per skill based on historical demand
            data. Top 10 skills by average predicted demand.
          </p>
          <div className="h-[28rem]">
            <Line
              data={predictionChartData}
              options={{
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                  legend: {
                    position: "bottom",
                    labels: {
                      filter: (item) =>
                        !item.text.includes("Upper") &&
                        !item.text.includes("Lower"),
                    },
                  },
                  tooltip: {
                    mode: "index",
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
                      text: "Predicted Demand",
                    },
                  },
                },
                interaction: {
                  mode: "nearest",
                  axis: "x",
                  intersect: false,
                },
              }}
            />
          </div>
        </div>
      )}

      <div className="rounded-lg bg-white shadow">
        <div className="border-b border-gray-200 px-6 py-4">
          <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
            <h3 className="text-lg font-medium text-gray-900">Forecast Data</h3>
            <div className="flex items-center gap-3">
              <input
                type="text"
                value={skillFilter}
                onChange={(e) => {
                  setSkillFilter(e.target.value);
                  setPage(0);
                }}
                placeholder="Filter by skill name..."
                className="rounded-md border border-gray-300 px-3 py-2 text-sm shadow-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
              />
            </div>
          </div>
        </div>

        {error && <div className="p-4 text-sm text-red-700">{error}</div>}

        {loading ? (
          <div className="flex h-48 items-center justify-center">
            <div className="h-8 w-8 animate-spin rounded-full border-4 border-blue-500 border-t-transparent" />
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500">
                    Skill
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500">
                    Forecast Date
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500">
                    Predicted Demand
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500">
                    Confidence Range
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500">
                    Model Version
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500">
                    Region
                  </th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-200 bg-white">
                {forecasts.map((fc) => (
                  <tr key={fc.id} className="hover:bg-gray-50">
                    <td className="whitespace-nowrap px-6 py-4 text-sm font-medium text-gray-900">
                      {fc.skillName}
                    </td>
                    <td className="whitespace-nowrap px-6 py-4 text-sm text-gray-500">
                      {format(parseISO(fc.forecastDate), "MMM d, yyyy")}
                    </td>
                    <td className="whitespace-nowrap px-6 py-4 text-sm text-gray-900 font-semibold">
                      {fc.predictedDemand.toLocaleString()}
                    </td>
                    <td className="whitespace-nowrap px-6 py-4 text-sm text-gray-500">
                      {fc.confidenceLower.toLocaleString()} –{" "}
                      {fc.confidenceUpper.toLocaleString()}
                    </td>
                    <td className="whitespace-nowrap px-6 py-4 text-sm text-gray-500">
                      {fc.modelVersion}
                    </td>
                    <td className="whitespace-nowrap px-6 py-4 text-sm text-gray-500">
                      {fc.region || "N/A"}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}

        {Math.ceil(totalElements / 20) > 1 && (
          <div className="flex items-center justify-between border-t border-gray-200 px-6 py-3">
            <button
              onClick={() => setPage((p) => Math.max(0, p - 1))}
              disabled={page === 0}
              className="rounded-md border border-gray-300 bg-white px-3 py-1 text-sm font-medium text-gray-700 hover:bg-gray-50 disabled:cursor-not-allowed disabled:opacity-50"
            >
              Previous
            </button>
            <span className="text-sm text-gray-700">
              Page {page + 1} of {Math.ceil(totalElements / 20)}
            </span>
            <button
              onClick={() => setPage((p) => p + 1)}
              disabled={page >= Math.ceil(totalElements / 20) - 1}
              className="rounded-md border border-gray-300 bg-white px-3 py-1 text-sm font-medium text-gray-700 hover:bg-gray-50 disabled:cursor-not-allowed disabled:opacity-50"
            >
              Next
            </button>
          </div>
        )}
      </div>
    </div>
  );
}
