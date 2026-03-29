import { useState, useEffect } from 'react';
import { useNavigate, Link, useSearchParams } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { loginUser } from '../api';
import { Loader2 } from 'lucide-react';

function GoogleIcon() {
  return (
    <svg width="18" height="18" viewBox="0 0 18 18" fill="none">
      <path d="M17.64 9.2c0-.637-.057-1.251-.164-1.84H9v3.481h4.844c-.209 1.125-.843 2.078-1.796 2.717v2.258h2.908c1.702-1.567 2.684-3.875 2.684-6.615z" fill="#4285F4"/>
      <path d="M9 18c2.43 0 4.467-.806 5.956-2.18l-2.908-2.259c-.806.54-1.837.86-3.048.86-2.344 0-4.328-1.584-5.036-3.711H.957v2.332A8.997 8.997 0 0 0 9 18z" fill="#34A853"/>
      <path d="M3.964 10.71A5.41 5.41 0 0 1 3.682 9c0-.593.102-1.17.282-1.71V4.958H.957A8.996 8.996 0 0 0 0 9c0 1.452.348 2.827.957 4.042l3.007-2.332z" fill="#FBBC05"/>
      <path d="M9 3.58c1.321 0 2.508.454 3.44 1.345l2.582-2.58C13.463.891 11.426 0 9 0A8.997 8.997 0 0 0 .957 4.958L3.964 6.29C4.672 4.163 6.656 3.58 9 3.58z" fill="#EA4335"/>
    </svg>
  );
}

export default function Login() {
  const { login }    = useAuth();
  const navigate     = useNavigate();
  const [params]     = useSearchParams();
  const [form, setForm]     = useState({ email: '', password: '' });
  const [error, setError]   = useState('');
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (params.get('error')) setError('Google sign-in failed. Please try again.');
  }, [params]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);
    try {
      const data = await loginUser(form);
      login(data.token, data.user);
      navigate(data.user.role === 'admin' ? '/admin' : '/');
    } catch (err) {
      setError(err.response?.data?.error || 'Login failed');
    } finally {
      setLoading(false);
    }
  };

  const handleGoogleLogin = () => {
    window.location.href = '/auth/google/login';
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-slate-50 px-4">
      <div className="card w-full max-w-sm p-8 space-y-5">

        {/* Logo */}
        <div className="text-center space-y-1">
          <div className="w-10 h-10 rounded-xl bg-brand-600 flex items-center justify-center mx-auto mb-3 shadow-sm">
            <span className="text-white font-bold text-lg">N</span>
          </div>
          <h1 className="text-xl font-bold text-slate-900">Welcome back</h1>
          <p className="text-slate-500 text-sm">Sign in to NanoCredit AI</p>
        </div>

        {error && (
          <p className="text-red-600 text-xs bg-red-50 border border-red-200 rounded-lg px-3 py-2">{error}</p>
        )}

        {/* Google button */}
        <button onClick={handleGoogleLogin}
          className="w-full flex items-center justify-center gap-3 px-4 py-2.5 rounded-xl border border-slate-200 bg-white text-slate-700 text-sm font-medium hover:bg-slate-50 hover:border-slate-300 active:scale-[0.98] transition-all shadow-sm">
          <GoogleIcon />
          Continue with Google
        </button>

        {/* Divider */}
        <div className="flex items-center gap-3">
          <div className="flex-1 h-px bg-slate-100" />
          <span className="text-xs text-slate-400">or</span>
          <div className="flex-1 h-px bg-slate-100" />
        </div>

        {/* Email/password form */}
        <form onSubmit={handleSubmit} className="space-y-3">
          <div>
            <label className="label-text">Email</label>
            <input type="email" required className="input-field"
              value={form.email} onChange={e => setForm({ ...form, email: e.target.value })}
              placeholder="you@example.com" />
          </div>
          <div>
            <label className="label-text">Password</label>
            <input type="password" required className="input-field"
              value={form.password} onChange={e => setForm({ ...form, password: e.target.value })}
              placeholder="••••••••" />
          </div>
          <button type="submit" disabled={loading} className="btn-primary w-full mt-1">
            {loading ? <><Loader2 className="animate-spin" size={16} /> Signing in...</> : 'Sign In'}
          </button>
        </form>

        <p className="text-center text-xs text-slate-500">
          Don't have an account?{' '}
          <Link to="/signup" className="text-brand-600 font-semibold hover:underline">Sign up</Link>
        </p>
      </div>
    </div>
  );
}
