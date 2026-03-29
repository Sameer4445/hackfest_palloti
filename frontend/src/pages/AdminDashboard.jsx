import { useEffect, useState } from 'react';
import { getAdminApplications, getAdminStats } from '../api';
import { Users, TrendingUp, CheckCircle, XCircle, BarChart2 } from 'lucide-react';

export default function AdminDashboard() {
  const [apps, setApps] = useState([]);
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([getAdminApplications(), getAdminStats()])
      .then(([a, s]) => { setApps(a); setStats(s); })
      .catch(console.error)
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <div className="text-center py-20 text-gray-500">Loading admin data...</div>;

  return (
    <div className="max-w-6xl mx-auto space-y-8 animate-slide-up">
      <h2 className="text-2xl font-bold text-gray-900">Admin Dashboard</h2>

      {/* Stats cards */}
      {stats && (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          {[
            { label: 'Total Applications', value: stats.total_applications, icon: <BarChart2 size={20} />, color: 'text-indigo-600' },
            { label: 'Approved', value: stats.approved, icon: <CheckCircle size={20} />, color: 'text-green-600' },
            { label: 'Rejected', value: stats.rejected, icon: <XCircle size={20} />, color: 'text-red-600' },
            { label: 'Avg Score', value: stats.avg_credit_score, icon: <TrendingUp size={20} />, color: 'text-primary-600' },
          ].map(card => (
            <div key={card.label} className="glass-card p-5 flex flex-col gap-1">
              <div className={`${card.color}`}>{card.icon}</div>
              <div className="text-2xl font-bold text-gray-900">{card.value}</div>
              <div className="text-xs text-gray-500">{card.label}</div>
            </div>
          ))}
        </div>
      )}

      {/* Risk distribution */}
      {stats && (
        <div className="glass-card p-6">
          <h3 className="font-semibold text-gray-800 mb-4">Risk Distribution</h3>
          <div className="flex gap-4">
            {Object.entries(stats.risk_distribution).map(([level, count]) => (
              <div key={level} className="flex-1 text-center">
                <div className={`text-2xl font-bold ${level === 'Low' ? 'text-green-600' : level === 'High' ? 'text-red-600' : 'text-yellow-600'}`}>
                  {count}
                </div>
                <div className="text-sm text-gray-500">{level} Risk</div>
                <div className="mt-2 h-2 rounded-full bg-gray-100 overflow-hidden">
                  <div
                    className={`h-full rounded-full ${level === 'Low' ? 'bg-green-400' : level === 'High' ? 'bg-red-400' : 'bg-yellow-400'}`}
                    style={{ width: stats.total_applications ? `${(count / stats.total_applications) * 100}%` : '0%' }}
                  />
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* All applications table */}
      <div className="glass-card overflow-hidden">
        <div className="p-6 border-b border-gray-100 flex items-center gap-2">
          <Users size={18} className="text-indigo-500" />
          <h3 className="font-semibold text-gray-800">All Applications</h3>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead className="bg-gray-50 text-gray-500 text-xs uppercase">
              <tr>
                {['User', 'Email', 'Score', 'Decision', 'Risk', 'Date'].map(h => (
                  <th key={h} className="px-4 py-3 text-left font-medium">{h}</th>
                ))}
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {apps.map(a => (
                <tr key={a.id} className="hover:bg-gray-50 transition">
                  <td className="px-4 py-3 font-medium text-gray-800">{a.user.name}</td>
                  <td className="px-4 py-3 text-gray-500">{a.user.email}</td>
                  <td className="px-4 py-3 font-bold text-gray-900">{a.credit_score}</td>
                  <td className="px-4 py-3">
                    <span className={`px-2 py-0.5 rounded-full text-xs font-medium
                      ${a.decision.includes('Approved') ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-700'}`}>
                      {a.decision}
                    </span>
                  </td>
                  <td className="px-4 py-3">
                    <span className={`px-2 py-0.5 rounded-full text-xs font-medium
                      ${a.risk_level === 'Low' ? 'bg-green-100 text-green-700' :
                        a.risk_level === 'High' ? 'bg-red-100 text-red-700' : 'bg-yellow-100 text-yellow-700'}`}>
                      {a.risk_level}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-gray-400">{new Date(a.created_at).toLocaleDateString()}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
