import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { submitApplication } from '../api';
import {
  Briefcase, MapPin, Wallet, CreditCard, Clock,
  Activity, Loader2, ChevronRight, IndianRupee,
} from 'lucide-react';

const OCCUPATIONS = ['Street Vendor','Gig Driver','Construction Worker','Cleaner','Tailor','Delivery Agent'];
const LOCATIONS   = ['Urban','Semi-Urban','Rural'];
const INCOME_SRC  = [
  { value: 'Cash',    label: 'Mostly Cash' },
  { value: 'Digital', label: 'Mostly Digital (UPI/Bank)' },
  { value: 'Mixed',   label: 'Mixed' },
];

function FormSection({ icon, title, color, children }) {
  return (
    <div className="space-y-4">
      <div className={`flex items-center gap-2 pb-2 border-b border-slate-100`}>
        <div className={`p-1.5 rounded-lg ${color}`}>{icon}</div>
        <h3 className="text-sm font-semibold text-slate-700">{title}</h3>
      </div>
      {children}
    </div>
  );
}

function Field({ label, children }) {
  return (
    <div>
      <label className="label-text">{label}</label>
      {children}
    </div>
  );
}

function SliderField({ label, name, value, onChange, min = 0, max = 1, step = 0.1, leftLabel, rightLabel, display }) {
  return (
    <div>
      <div className="flex justify-between items-center mb-1">
        <label className="label-text">{label}</label>
        <span className="text-xs font-semibold text-brand-600 bg-brand-50 px-2 py-0.5 rounded-full">{display}</span>
      </div>
      <input type="range" name={name} value={value} onChange={onChange}
        min={min} max={max} step={step}
        className="w-full h-1.5 rounded-full accent-brand-600 cursor-pointer" />
      {(leftLabel || rightLabel) && (
        <div className="flex justify-between text-xs text-slate-400 mt-1">
          <span>{leftLabel}</span><span>{rightLabel}</span>
        </div>
      )}
    </div>
  );
}

const ApplicationForm = ({ setScoringResult }) => {
  const navigate  = useNavigate();
  const [loading, setLoading] = useState(false);
  const [formData, setFormData] = useState({
    age: 30, occupation: 'Street Vendor', location_type: 'Urban',
    avg_daily_income: 500, work_days_per_month: 26, income_variance: 0.3,
    income_source_type: 'Cash', daily_expense: 300, has_bank_account: 1,
    digital_transaction_usage: 0.5, avg_work_hours_per_day: 10, location_consistency: 0.8,
  });

  const handleChange = (e) => {
    const { name, value, type } = e.target;
    setFormData(prev => ({ ...prev, [name]: (type === 'number' || type === 'range') ? parseFloat(value) : value }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    try {
      const result = await submitApplication(formData);
      setScoringResult(result);
      navigate('/result');
    } catch (error) {
      const msg = error.response?.data?.error || 'Error analyzing application. Please ensure backend is running.';
      alert(msg);
    } finally {
      setLoading(false);
    }
  };

  // Live preview
  const monthlyIncome  = formData.avg_daily_income * 30;
  const monthlyExpense = formData.daily_expense * 30;
  const disposable     = monthlyIncome - monthlyExpense;

  return (
    <div className="max-w-4xl mx-auto animate-slide-up space-y-6">

      {/* Hero header */}
      <div className="text-center space-y-2 py-4">
        <h1 className="text-3xl sm:text-4xl font-bold text-slate-900 tracking-tight">
          AI Credit Evaluation
        </h1>
        <p className="text-slate-500 text-base max-w-xl mx-auto">
          Get an instant credit score based on your real financial behaviour — no formal credit history needed.
        </p>
      </div>

      {/* Live financial preview */}
      <div className="grid grid-cols-3 gap-3">
        {[
          { label: 'Monthly Income',  value: `₹${monthlyIncome.toLocaleString('en-IN')}`,  color: 'text-green-600',  bg: 'bg-green-50'  },
          { label: 'Monthly Expense', value: `₹${monthlyExpense.toLocaleString('en-IN')}`, color: 'text-red-500',    bg: 'bg-red-50'    },
          { label: 'Disposable',      value: `₹${disposable.toLocaleString('en-IN')}`,     color: disposable >= 0 ? 'text-blue-600' : 'text-red-600', bg: disposable >= 0 ? 'bg-blue-50' : 'bg-red-50' },
        ].map(m => (
          <div key={m.label} className={`card p-3 text-center ${m.bg} border-0`}>
            <p className="text-xs text-slate-500 mb-0.5">{m.label}</p>
            <p className={`text-base font-bold ${m.color}`}>{m.value}</p>
          </div>
        ))}
      </div>

      {/* Form card */}
      <div className="card overflow-hidden">
        <div className="h-1 w-full bg-gradient-to-r from-brand-500 via-blue-500 to-purple-500" />
        <form onSubmit={handleSubmit} className="p-6 sm:p-8">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-8">

            <FormSection icon={<Briefcase size={15} className="text-indigo-600" />} title="Basic Details" color="bg-indigo-50">
              <Field label="Age">
                <input type="number" name="age" value={formData.age} onChange={handleChange}
                  min="18" max="100" className="input-field" required />
              </Field>
              <Field label="Occupation">
                <select name="occupation" value={formData.occupation} onChange={handleChange} className="input-field">
                  {OCCUPATIONS.map(o => <option key={o}>{o}</option>)}
                </select>
              </Field>
              <Field label="Location Type">
                <select name="location_type" value={formData.location_type} onChange={handleChange} className="input-field">
                  {LOCATIONS.map(l => <option key={l}>{l}</option>)}
                </select>
              </Field>
            </FormSection>

            <FormSection icon={<Wallet size={15} className="text-green-600" />} title="Income & Expenses" color="bg-green-50">
              <Field label="Average Daily Income (₹)">
                <input type="number" name="avg_daily_income" value={formData.avg_daily_income}
                  onChange={handleChange} min="0" className="input-field" required />
              </Field>
              <Field label="Average Daily Expense (₹)">
                <input type="number" name="daily_expense" value={formData.daily_expense}
                  onChange={handleChange} min="0" className="input-field" required />
              </Field>
              <SliderField label="Income Stability" name="income_variance" value={formData.income_variance}
                onChange={handleChange} min={0} max={1} step={0.1}
                leftLabel="Very Stable" rightLabel="Highly Variable"
                display={`${(formData.income_variance * 100).toFixed(0)}% variance`} />
            </FormSection>

            <FormSection icon={<CreditCard size={15} className="text-blue-600" />} title="Banking & Digital Use" color="bg-blue-50">
              <Field label="Primary Income Source">
                <select name="income_source_type" value={formData.income_source_type} onChange={handleChange} className="input-field">
                  {INCOME_SRC.map(s => <option key={s.value} value={s.value}>{s.label}</option>)}
                </select>
              </Field>
              <div className="flex items-center gap-3 py-1">
                <input type="checkbox" id="bank_acc" checked={formData.has_bank_account === 1}
                  onChange={e => setFormData({ ...formData, has_bank_account: e.target.checked ? 1 : 0 })}
                  className="w-4 h-4 rounded accent-brand-600 cursor-pointer" />
                <label htmlFor="bank_acc" className="text-sm text-slate-700 font-medium cursor-pointer">
                  Has formal bank account
                </label>
              </div>
              <SliderField label="Digital Transaction Frequency" name="digital_transaction_usage"
                value={formData.digital_transaction_usage} onChange={handleChange} min={0} max={1} step={0.1}
                leftLabel="Rarely" rightLabel="Always"
                display={`${(formData.digital_transaction_usage * 100).toFixed(0)}%`} />
            </FormSection>

            <FormSection icon={<Activity size={15} className="text-orange-500" />} title="Work Behaviour" color="bg-orange-50">
              <Field label="Work Days per Month">
                <input type="number" name="work_days_per_month" value={formData.work_days_per_month}
                  onChange={handleChange} min="1" max="31" className="input-field" required />
              </Field>
              <Field label="Avg Work Hours per Day">
                <input type="number" name="avg_work_hours_per_day" value={formData.avg_work_hours_per_day}
                  onChange={handleChange} min="1" max="24" className="input-field" required />
              </Field>
              <SliderField label="Location Consistency" name="location_consistency"
                value={formData.location_consistency} onChange={handleChange} min={0} max={1} step={0.1}
                leftLabel="Varies a lot" rightLabel="Always same spot"
                display={`${(formData.location_consistency * 100).toFixed(0)}%`} />
            </FormSection>
          </div>

          <div className="mt-8 pt-6 border-t border-slate-100 flex justify-center">
            <button type="submit" disabled={loading}
              className="btn-primary px-10 py-3 text-base min-w-[220px]">
              {loading
                ? <><Loader2 className="animate-spin" size={18} /> Analyzing...</>
                : <><span>Generate Credit Score</span><ChevronRight size={18} /></>
              }
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default ApplicationForm;
