import { useEffect, useState } from 'react';
import { getHistory } from '../api';
import { CheckCircle, XCircle, AlertTriangle, Clock } from 'lucide-react';

export default function History() {
  const [records, setRecords] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    getHistory()
      .then(setRecords)
      .catch(console.error)
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <div className="text-center py-20 text-gray-500">Loading history...</div>;
  if (!records.length) return (
    <div className="text-center py-20 text-gray-400">
      <Clock size={48} className="mx-auto mb-3 opacity-40" />
      <p>No credit applications yet. Submit your first one!</p>
    </div>
  );

  return (
    <div className="max-w-4xl mx-auto space-y-4 animate-slide-up">
      <h2 className="text-2xl font-bold text-gray-900">Your Credit History</h2>
      {records.map(r => {
        const approved = r.decision.includes('Approved');
        const rejected = r.decision.includes('Rejected');
        return (
          <div key={r.id} className="glass-card p-6 flex flex-col sm:flex-row sm:items-center gap-4">
            <div className={`flex-shrink-0 w-16 h-16 rounded-full border-4 flex items-center justify-center font-black text-xl
              ${rejected ? 'border-red-400 text-red-600' : approved ? 'border-green-400 text-green-600' : 'border-yellow-400 text-yellow-600'}`}>
              {r.credit_score}
            </div>
            <div className="flex-1 min-w-0">
              <div className="flex items-center gap-2 mb-1">
                {approved ? <CheckCircle size={16} className="text-green-500" /> :
                 rejected ? <XCircle size={16} className="text-red-500" /> :
                 <AlertTriangle size={16} className="text-yellow-500" />}
                <span className="font-semibold text-gray-800">{r.decision}</span>
                <span className={`ml-2 px-2 py-0.5 rounded-full text-xs font-medium
                  ${r.risk_level === 'Low' ? 'bg-green-100 text-green-700' :
                    r.risk_level === 'High' ? 'bg-red-100 text-red-700' : 'bg-yellow-100 text-yellow-700'}`}>
                  {r.risk_level} Risk
                </span>
              </div>
              <p className="text-sm text-gray-500 truncate">{r.explanation}</p>
              <p className="text-xs text-gray-400 mt-1">{new Date(r.created_at).toLocaleString()}</p>
            </div>
            <div className="text-right text-sm text-gray-500">
              {(r.confidence_score * 100).toFixed(0)}% confidence
            </div>
          </div>
        );
      })}
    </div>
  );
}
