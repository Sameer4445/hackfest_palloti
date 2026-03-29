import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  CheckCircle, XCircle, AlertTriangle, ArrowLeft, Lightbulb,
  Star, Building2, Landmark, BadgeIndianRupee, ChevronDown, ChevronUp,
  TrendingUp, Wallet, Calculator, IndianRupee, ShieldCheck, ShieldAlert,
  ArrowUpRight, ArrowDownRight, Minus,
} from 'lucide-react';

// ── helpers ───────────────────────────────────────────────────────────────────

const fmt  = (n) => `₹${Number(n).toLocaleString('en-IN')}`;
const fmtK = (n) => n >= 100000 ? `₹${(n/100000).toFixed(1)}L` : n >= 1000 ? `₹${(n/1000).toFixed(0)}K` : fmt(n);

const calcEMI = (p, r, m) => {
  if (r === 0) return p / m;
  const mr = r / 100 / 12;
  return p * mr * Math.pow(1 + mr, m) / (Math.pow(1 + mr, m) - 1);
};

const PROVIDER = {
  government: { label: 'Govt',  bg: 'bg-blue-50',   border: 'border-blue-100',  text: 'text-blue-700',   icon: <Landmark size={12} /> },
  nbfc:       { label: 'NBFC',  bg: 'bg-violet-50',  border: 'border-violet-100', text: 'text-violet-700', icon: <BadgeIndianRupee size={12} /> },
  bank:       { label: 'Bank',  bg: 'bg-emerald-50', border: 'border-emerald-100',text: 'text-emerald-700',icon: <Building2 size={12} /> },
};

// ── Score ring ────────────────────────────────────────────────────────────────

function ScoreRing({ score }) {
  const r   = 54;
  const circ = 2 * Math.PI * r;
  const pct  = Math.max(0, Math.min(100, score));
  const dash = (pct / 100) * circ;
  const color = pct >= 70 ? '#16a34a' : pct >= 45 ? '#d97706' : '#dc2626';
  const glow  = pct >= 70 ? 'drop-shadow(0 0 8px #16a34a55)' : pct >= 45 ? 'drop-shadow(0 0 8px #d9770655)' : 'drop-shadow(0 0 8px #dc262655)';

  return (
    <div className="relative inline-flex items-center justify-center">
      <svg width="140" height="140" className="-rotate-90" style={{ filter: glow }}>
        <circle cx="70" cy="70" r={r} fill="none" stroke="#f1f5f9" strokeWidth="10" />
        <circle cx="70" cy="70" r={r} fill="none" stroke={color} strokeWidth="10"
          strokeLinecap="round"
          strokeDasharray={`${dash} ${circ}`}
          className="animate-score-ring"
          style={{ transition: 'stroke-dasharray 1s ease-out' }} />
      </svg>
      <div className="absolute text-center">
        <span className="text-4xl font-black" style={{ color }}>{score}</span>
        <span className="block text-xs text-slate-400 font-medium">/ 100</span>
      </div>
    </div>
  );
}

// ── Metric card ───────────────────────────────────────────────────────────────

function MetricCard({ label, value, icon, trend, className = '' }) {
  return (
    <div className={`card p-4 ${className}`}>
      <div className="flex items-start justify-between mb-2">
        <span className="text-xs font-semibold text-slate-400 uppercase tracking-wide">{label}</span>
        <div className="text-slate-300">{icon}</div>
      </div>
      <p className="text-lg font-bold text-slate-900">{value}</p>
      {trend && <p className="text-xs text-slate-400 mt-0.5">{trend}</p>}
    </div>
  );
}

// ── Affordability badge ───────────────────────────────────────────────────────

function AffBadge({ status }) {
  const map = { safe: 'badge badge-green', moderate: 'badge badge-yellow', risky: 'badge badge-red' };
  const lbl = { safe: 'Safe', moderate: 'Risky', risky: 'Not Affordable' };
  return <span className={map[status] || map.risky}>{lbl[status] || 'Not Affordable'}</span>;
}

// ── EMI panel ─────────────────────────────────────────────────────────────────

function EMIPanel({ scheme }) {
  const max = scheme.recommended_amount;
  const min = Math.max(1000, Math.round(max * 0.2));
  const [amt, setAmt]       = useState(max);
  const [tenure, setTenure] = useState(scheme.recommended_plan?.tenure_months || 36);
  const safe = scheme.safe_emi_limit || 0;

  const plans = [12, 24, 36].map(t => {
    const emi  = calcEMI(amt, scheme.interest_rate, t);
    const tot  = emi * t;
    const aff  = emi <= safe ? 'safe' : emi <= safe * 1.4 ? 'moderate' : 'risky';
    return { t, emi, tot, interest: tot - amt, aff, isRec: scheme.recommended_plan?.tenure_months === t };
  });

  const active = plans.find(p => p.t === tenure) || plans[0];
  const bg = active.aff === 'safe' ? 'bg-green-50 border-green-200' : active.aff === 'moderate' ? 'bg-amber-50 border-amber-200' : 'bg-red-50 border-red-200';
  const tc = active.aff === 'safe' ? 'text-green-700' : active.aff === 'moderate' ? 'text-amber-700' : 'text-red-700';

  return (
    <div className="mt-4 pt-4 border-t border-slate-100 space-y-3 animate-fade-in">
      {/* Slider */}
      <div>
        <div className="flex justify-between text-xs text-slate-500 mb-1">
          <span className="flex items-center gap-1"><Wallet size={11} /> Loan Amount</span>
          <span className="font-semibold text-slate-800">{fmt(amt)}</span>
        </div>
        <input type="range" min={min} max={max} step={1000} value={amt}
          onChange={e => setAmt(Number(e.target.value))}
          className="w-full h-1.5 rounded-full accent-brand-600 cursor-pointer" />
        <div className="flex justify-between text-xs text-slate-400 mt-0.5">
          <span>{fmtK(min)}</span><span>{fmtK(max)}</span>
        </div>
      </div>

      {/* Tenure tabs */}
      <div className="flex gap-2">
        {plans.map(p => (
          <button key={p.t} onClick={() => setTenure(p.t)}
            className={`flex-1 py-1.5 rounded-lg text-xs font-semibold border transition-all ${
              tenure === p.t ? 'bg-slate-900 text-white border-slate-900' : 'bg-white text-slate-600 border-slate-200 hover:border-slate-400'
            }`}>
            {p.t}mo{p.isRec && <span className="ml-1 text-amber-400">★</span>}
          </button>
        ))}
      </div>

      {/* Result */}
      <div className={`rounded-xl p-3 border ${bg}`}>
        <div className="flex items-center justify-between mb-2">
          <span className="text-xs text-slate-500">Monthly EMI</span>
          <AffBadge status={active.aff} />
        </div>
        <p className={`text-2xl font-black ${tc}`}>
          {fmt(Math.round(active.emi))}<span className="text-sm font-normal text-slate-400">/mo</span>
        </p>
        <div className="grid grid-cols-2 gap-2 mt-2 text-xs">
          <div className="bg-white/70 rounded-lg p-2">
            <p className="text-slate-400">Total Interest</p>
            <p className="font-semibold text-slate-700">{fmt(Math.round(active.interest))}</p>
          </div>
          <div className="bg-white/70 rounded-lg p-2">
            <p className="text-slate-400">Total Payment</p>
            <p className="font-semibold text-slate-700">{fmt(Math.round(active.tot))}</p>
          </div>
        </div>
        {safe > 0 && <p className="text-xs text-slate-400 mt-2">Safe EMI limit: {fmt(Math.round(safe))}/mo</p>}
      </div>
    </div>
  );
}

// ── Scheme card ───────────────────────────────────────────────────────────────

function SchemeCard({ scheme }) {
  const [emiOpen, setEmiOpen]       = useState(false);
  const [detailOpen, setDetailOpen] = useState(false);
  const { tier, eligibility_score: score } = scheme;
  const pv = PROVIDER[scheme.provider_type] || PROVIDER.nbfc;

  const scoreColor = score >= 70 ? 'text-green-600' : score >= 40 ? 'text-amber-600' : 'text-red-500';
  const scoreBg    = score >= 70 ? 'bg-green-500'   : score >= 40 ? 'bg-amber-400'   : 'bg-red-400';

  return (
    <div className={`card p-4 transition-all duration-200 ${
      tier === 'eligible' && scheme.is_best_match ? 'ring-2 ring-amber-300 shadow-md' : ''
    } ${tier === 'rejected' ? 'opacity-70' : ''}`}>

      {/* Header */}
      <div className="flex items-start justify-between gap-2 mb-3">
        <div className="flex-1 min-w-0">
          <div className="flex flex-wrap items-center gap-1.5 mb-1.5">
            {scheme.is_best_match && (
              <span className="badge bg-amber-100 text-amber-700">
                <Star size={9} fill="currentColor" /> Best Match
              </span>
            )}
            {tier === 'partial' && <span className="badge badge-yellow"><AlertTriangle size={9} /> Partial</span>}
            <span className={`badge border ${pv.bg} ${pv.border} ${pv.text}`}>
              {pv.icon} {pv.label}
            </span>
          </div>
          <p className="font-semibold text-slate-900 text-sm leading-tight">{scheme.name}</p>
        </div>
        <div className="text-right flex-shrink-0">
          <p className="text-sm font-bold text-slate-900">{fmtK(scheme.recommended_amount)}</p>
          {scheme.recommended_amount < scheme.max_amount && (
            <p className="text-xs text-slate-400 line-through">{fmtK(scheme.max_amount)}</p>
          )}
          <p className="text-xs text-slate-400">{scheme.interest_rate}% p.a.</p>
        </div>
      </div>

      {/* Score bar */}
      <div className="mb-3">
        <div className="flex justify-between text-xs mb-1">
          <span className="text-slate-400">Eligibility</span>
          <span className={`font-bold ${scoreColor}`}>{score}/100</span>
        </div>
        <div className="h-1.5 bg-slate-100 rounded-full overflow-hidden">
          <div className={`h-full rounded-full transition-all duration-700 ${scoreBg}`} style={{ width: `${score}%` }} />
        </div>
      </div>

      {/* Reasons */}
      {tier !== 'rejected' && scheme.eligible_reasons?.slice(0, 2).map((r, i) => (
        <p key={i} className="text-xs text-green-700 flex items-start gap-1.5 mb-1">
          <CheckCircle size={11} className="mt-0.5 flex-shrink-0" /> {r}
        </p>
      ))}
      {tier === 'rejected' && scheme.rejection_reasons?.slice(0, 2).map((r, i) => (
        <p key={i} className="text-xs text-red-500 flex items-start gap-1.5 mb-1">
          <XCircle size={11} className="mt-0.5 flex-shrink-0" /> {r}
        </p>
      ))}

      {/* Actions */}
      <div className="flex gap-2 mt-3">
        {tier !== 'rejected' && (
          <button onClick={() => { setEmiOpen(o => !o); setDetailOpen(false); }}
            className={`flex-1 flex items-center justify-center gap-1.5 py-1.5 rounded-lg text-xs font-semibold border transition-all ${
              emiOpen ? 'bg-slate-900 text-white border-slate-900' : 'btn-outline'
            }`}>
            <Calculator size={12} />
            {emiOpen ? 'Hide EMI' : 'View EMI'}
          </button>
        )}
        <button onClick={() => { setDetailOpen(o => !o); setEmiOpen(false); }}
          className="flex-1 flex items-center justify-center gap-1 py-1.5 rounded-lg text-xs text-slate-400 hover:text-slate-600 border border-transparent hover:border-slate-200 transition-all">
          {detailOpen ? <ChevronUp size={12} /> : <ChevronDown size={12} />}
          {detailOpen ? 'Less' : 'Details'}
        </button>
      </div>

      {emiOpen && <EMIPanel scheme={scheme} />}

      {detailOpen && (
        <div className="mt-3 pt-3 border-t border-slate-100 space-y-2 animate-fade-in">
          <p className="text-xs text-slate-500 leading-relaxed">{scheme.description}</p>
          {scheme.eligible_reasons?.length > 2 && (
            <div className="space-y-1">
              <p className="text-xs font-semibold text-green-700">Why eligible:</p>
              {scheme.eligible_reasons.slice(2).map((r, i) => (
                <p key={i} className="text-xs text-green-600 flex items-start gap-1.5">
                  <CheckCircle size={10} className="mt-0.5 flex-shrink-0" /> {r}
                </p>
              ))}
            </div>
          )}
          {scheme.rejection_reasons?.length > 0 && tier !== 'rejected' && (
            <div className="space-y-1">
              <p className="text-xs font-semibold text-orange-600">Limitations:</p>
              {scheme.rejection_reasons.map((r, i) => (
                <p key={i} className="text-xs text-orange-500 flex items-start gap-1.5">
                  <AlertTriangle size={10} className="mt-0.5 flex-shrink-0" /> {r}
                </p>
              ))}
            </div>
          )}
          {scheme.improvement_suggestions?.length > 0 && (
            <div className="space-y-1">
              <p className="text-xs font-semibold text-blue-600">How to improve:</p>
              {scheme.improvement_suggestions.map((s, i) => (
                <p key={i} className="text-xs text-blue-500 flex items-start gap-1.5">
                  <TrendingUp size={10} className="mt-0.5 flex-shrink-0" /> {s}
                </p>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
}

// ── Section wrapper ───────────────────────────────────────────────────────────

function Section({ icon, title, count, children }) {
  return (
    <div>
      <div className="flex items-center gap-2 mb-3">
        {icon}
        <h3 className="text-sm font-bold text-slate-700">{title}</h3>
        {count !== undefined && (
          <span className="ml-auto text-xs text-slate-400 bg-slate-100 px-2 py-0.5 rounded-full">{count}</span>
        )}
      </div>
      {children}
    </div>
  );
}

// ── Main page ─────────────────────────────────────────────────────────────────

const ResultDashboard = ({ result }) => {
  const navigate = useNavigate();
  const {
    credit_score, decision, risk_level, explanation, confidence_score,
    top_schemes = [], partial_schemes = [], rejected_schemes = [],
    monthly_income = 0, monthly_expense = 0,
    disposable_income = 0, safe_emi_limit = 0, max_loan_allowed = 0,
    financial_status = 'ok', warning_message = null,
    score_breakdown = null, why_bullets = [],
  } = result;

  const isApproved = decision.includes('Approved');
  const isRejected = decision.includes('Rejected');
  const isUnsafe   = ['no_income','low_income','no_disposable','unsafe'].includes(financial_status);

  const decisionBadge = isApproved
    ? <span className="badge badge-green text-sm px-3 py-1"><CheckCircle size={13} /> Approved</span>
    : <span className="badge badge-red text-sm px-3 py-1"><XCircle size={13} /> Rejected</span>;

  const riskBadge = risk_level === 'Low'
    ? <span className="badge badge-green"><ShieldCheck size={11} /> Low Risk</span>
    : risk_level === 'Medium'
    ? <span className="badge badge-yellow"><ShieldAlert size={11} /> Medium Risk</span>
    : <span className="badge badge-red"><ShieldAlert size={11} /> High Risk</span>;

  return (
    <div className="max-w-5xl mx-auto animate-slide-up pb-16 space-y-6">

      {/* Back */}
      <button onClick={() => navigate('/')} className="btn-outline text-xs px-3 py-1.5">
        <ArrowLeft size={14} /> Back
      </button>

      {/* ── Top row: score + metrics ── */}
      <div className="grid grid-cols-1 md:grid-cols-12 gap-4">

        {/* Score card */}
        <div className="md:col-span-4 card p-6 flex flex-col items-center text-center">
          <p className="section-label mb-4">AI Credit Score</p>
          <ScoreRing score={credit_score} />
          <div className="mt-4 flex flex-col items-center gap-2">
            {decisionBadge}
            {riskBadge}
            {confidence_score !== undefined && (
              <span className="badge badge-blue">{(confidence_score * 100).toFixed(1)}% confidence</span>
            )}
          </div>
        </div>

        {/* Metrics grid */}
        <div className="md:col-span-8 grid grid-cols-2 sm:grid-cols-3 gap-3 content-start">
          <MetricCard label="Monthly Income"  value={fmt(Math.round(monthly_income))}
            icon={<ArrowUpRight size={16} />}
            trend="Based on daily × 30" className="stagger-1 animate-slide-up" />
          <MetricCard label="Monthly Expense" value={fmt(Math.round(monthly_expense))}
            icon={<ArrowDownRight size={16} />}
            trend="Based on daily × 30" className="stagger-2 animate-slide-up" />
          <MetricCard label="Disposable Income" value={fmt(Math.round(disposable_income))}
            icon={<Minus size={16} />}
            trend="Income − Expense"
            className={`stagger-3 animate-slide-up ${disposable_income < 2000 ? 'border-red-200 bg-red-50' : ''}`} />
          <MetricCard label="Safe EMI Limit"  value={fmt(Math.round(safe_emi_limit))}
            icon={<ShieldCheck size={16} />}
            trend="50% of disposable" className="stagger-4 animate-slide-up" />
          <MetricCard label="Max Loan Capacity" value={fmtK(max_loan_allowed)}
            icon={<IndianRupee size={16} />}
            trend="Safe EMI × 20 months" className="stagger-4 animate-slide-up col-span-2 sm:col-span-1" />
        </div>
      </div>

      {/* ── Explanation + breakdown ── */}
      <div className="grid grid-cols-1 md:grid-cols-12 gap-4">
        <div className="md:col-span-7 card p-5">
          <div className="flex items-center gap-2 mb-3">
            <Lightbulb size={16} className="text-blue-500" />
            <h3 className="text-sm font-bold text-slate-700">AI Explanation</h3>
          </div>
          <p className="text-sm text-slate-600 leading-relaxed mb-4">"{explanation}"</p>
          {why_bullets?.length > 0 && (
            <>
              <p className="text-xs font-bold text-slate-500 uppercase tracking-wide mb-2">Why this decision?</p>
              <ul className="space-y-1.5">
                {why_bullets.map((b, i) => {
                  const positive = b.toLowerCase().includes('strong') || b.toLowerCase().includes('support');
                  return (
                    <li key={i} className="flex items-start gap-2 text-xs text-slate-600">
                      {positive
                        ? <CheckCircle size={11} className="text-green-500 mt-0.5 flex-shrink-0" />
                        : <AlertTriangle size={11} className="text-amber-500 mt-0.5 flex-shrink-0" />}
                      {b}
                    </li>
                  );
                })}
              </ul>
            </>
          )}
        </div>

        {score_breakdown && (
          <div className="md:col-span-5 card p-5">
            <div className="flex items-center gap-2 mb-3">
              <TrendingUp size={16} className="text-indigo-500" />
              <h3 className="text-sm font-bold text-slate-700">Score Breakdown</h3>
            </div>
            <div className="flex items-center gap-4 mb-4">
              <div className="text-center">
                <p className="text-xs text-slate-400">Base</p>
                <p className="text-2xl font-black text-slate-500">{score_breakdown.base_score}</p>
              </div>
              <div className="flex-1 h-px bg-slate-200 relative">
                <span className="absolute -top-2.5 left-1/2 -translate-x-1/2 text-slate-300 text-xs">→</span>
              </div>
              <div className="text-center">
                <p className="text-xs text-slate-400">Final</p>
                <p className={`text-2xl font-black ${score_breakdown.final_score >= 70 ? 'text-green-600' : score_breakdown.final_score >= 40 ? 'text-amber-600' : 'text-red-600'}`}>
                  {score_breakdown.final_score}
                </p>
              </div>
            </div>
            <div className="space-y-1.5">
              {score_breakdown.penalties?.map((p, i) => (
                <p key={i} className="text-xs text-slate-500 flex items-start gap-1.5">
                  <span className="text-indigo-400 flex-shrink-0 mt-0.5">•</span> {p}
                </p>
              ))}
            </div>
          </div>
        )}
      </div>

      {/* ── Financial warning ── */}
      {isUnsafe && (
        <div className="card p-5 border-l-4 border-l-red-500 bg-red-50 border-red-100">
          <div className="flex items-start gap-3">
            <ShieldAlert className="text-red-500 flex-shrink-0 mt-0.5" size={20} />
            <div>
              <h3 className="font-bold text-red-700 text-sm mb-1">Not Financially Safe to Take a Loan</h3>
              <p className="text-xs text-red-600 mb-3">{warning_message}</p>
              <p className="text-xs font-bold text-slate-600 uppercase tracking-wide mb-2">How to improve</p>
              <ul className="space-y-1.5">
                {[
                  disposable_income < 2000 && `Reduce monthly expenses by ₹${Math.ceil((2000 - disposable_income) / 100) * 100} to reach safe disposable income`,
                  'Increase income through additional work days or a secondary source',
                  'Build a savings buffer of at least 3 months of expenses',
                  'Consider joining a Self Help Group (SHG) for micro-savings support',
                ].filter(Boolean).map((s, i) => (
                  <li key={i} className="flex items-start gap-2 text-xs text-slate-600">
                    <TrendingUp size={11} className="text-blue-500 mt-0.5 flex-shrink-0" /> {s}
                  </li>
                ))}
              </ul>
            </div>
          </div>
        </div>
      )}

      {/* ── Loan sections ── */}
      {!isUnsafe && (
        <div className="card p-6 space-y-6">
          <Section
            icon={<CheckCircle size={16} className="text-green-500" />}
            title="Top Recommended Loans"
            count={`${top_schemes.length} eligible`}>
            {top_schemes.length === 0
              ? <p className="text-sm text-slate-400 text-center py-6">No fully eligible schemes for your current profile.</p>
              : <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
                  {top_schemes.map(s => <SchemeCard key={s.id} scheme={s} />)}
                </div>
            }
          </Section>

          {partial_schemes.length > 0 && (
            <>
              <div className="border-t border-slate-100" />
              <Section
                icon={<AlertTriangle size={16} className="text-amber-500" />}
                title="Partially Eligible"
                count={`${partial_schemes.length} schemes`}>
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                  {partial_schemes.map(s => <SchemeCard key={s.id} scheme={s} />)}
                </div>
              </Section>
            </>
          )}
        </div>
      )}

      {rejected_schemes.length > 0 && (
        <div className="card p-6">
          <Section
            icon={<XCircle size={16} className="text-slate-400" />}
            title={isUnsafe ? 'All Schemes — Currently Not Advisable' : 'Not Eligible'}
            count={`${rejected_schemes.length} schemes`}>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
              {rejected_schemes.map(s => <SchemeCard key={s.id} scheme={s} />)}
            </div>
          </Section>
        </div>
      )}
    </div>
  );
};

export default ResultDashboard;
