import { useState, useEffect } from 'react';
import { Bar } from 'react-chartjs-2';
import { format, parseISO } from 'date-fns';
import {
  getTopSkills,
  getSkills,
  type TopSkill,
  type SkillDemand,
} from '../services/api';
import '../services/chartConfig';

const CHART_COLORS = Array.from({ length: 20 }, (_, i) => {
  const hue = (i * 18) % 360;
  return `hsla(${hue}, 65%, 55%, 0.8)`;
});

export default function Skills() {
  const [topSkills, setTopSkills] = useState<TopSkill[]>([]);
  const [skills, setSkills] = useState<SkillDemand[]>([]);
  const [totalElements, setTotalElements] = useState(0);
  const [page, setPage] = useState(0);
  const [searchName, setSearchName] = useState('');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    getTopSkills(20)
      .then((res) => setTopSkills(res.data))
      .catch(() => {});
  }, []);

  useEffect(() => {
    setLoading(true);
    setError(null);
    getSkills({ page, size: 20, skillName: searchName || undefined })
      .then((res) => {
        setSkills(res.data.content);
        setTotalElements(res.data.totalElements);
      })
      .catch((err) => setError(err.message || 'Failed to load skills'))
      .finally(() => setLoading(false));
  }, [page, searchName]);

  const barData = {
    labels: topSkills.map((s) => s.skillName),
    datasets: [
      {
        label: 'Total Demand',
        data: topSkills.map((s) => s.totalDemand),
        backgroundColor: CHART_COLORS,
        borderRadius: 4,
      },
    ],
  };

  return (
    <div className="space-y-6">
      <div className="rounded-lg bg-white p-6 shadow">
        <h3 className="mb-4 text-lg font-medium text-gray-900">Top 20 Skills by Demand</h3>
        <div className="h-96">
          <Bar
            data={barData}
            options={{
              responsive: true,
              maintainAspectRatio: false,
              plugins: {
                legend: { display: false },
              },
              scales: {
                x: { ticks: { maxRotation: 60, minRotation: 45 } },
                y: { beginAtZero: true },
              },
            }}
          />
        </div>
      </div>

      <div className="rounded-lg bg-white shadow">
        <div className="border-b border-gray-200 px-6 py-4">
          <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
            <h3 className="text-lg font-medium text-gray-900">Skill Demand Data</h3>
            <div className="flex items-center gap-3">
              <input
                type="text"
                value={searchName}
                onChange={(e) => {
                  setSearchName(e.target.value);
                  setPage(0);
                }}
                placeholder="Search skills..."
                className="rounded-md border border-gray-300 px-3 py-2 text-sm shadow-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
              />
            </div>
          </div>
        </div>

        {error && (
          <div className="p-4 text-sm text-red-700">{error}</div>
        )}

        {loading ? (
          <div className="flex h-48 items-center justify-center">
            <div className="h-8 w-8 animate-spin rounded-full border-4 border-blue-500 border-t-transparent" />
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500">Skill</th>
                  <th className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500">Demand Count</th>
                  <th className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500">Period</th>
                  <th className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500">Region</th>
                  <th className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500">Industry</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-200 bg-white">
                {skills.map((skill) => (
                  <tr key={skill.id} className="hover:bg-gray-50">
                    <td className="whitespace-nowrap px-6 py-4 text-sm font-medium text-gray-900">{skill.skillName}</td>
                    <td className="whitespace-nowrap px-6 py-4 text-sm text-gray-500">{skill.demandCount.toLocaleString()}</td>
                    <td className="whitespace-nowrap px-6 py-4 text-sm text-gray-500">
                      {skill.periodStart && skill.periodEnd
                        ? `${format(parseISO(skill.periodStart), 'MMM yyyy')} – ${format(parseISO(skill.periodEnd), 'MMM yyyy')}`
                        : 'N/A'}
                    </td>
                    <td className="whitespace-nowrap px-6 py-4 text-sm text-gray-500">{skill.region || 'N/A'}</td>
                    <td className="whitespace-nowrap px-6 py-4 text-sm text-gray-500">{skill.industry || 'N/A'}</td>
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