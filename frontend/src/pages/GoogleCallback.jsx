import { useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';

export default function GoogleCallback() {
  const { login } = useAuth();
  const navigate  = useNavigate();

  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    const token  = params.get('token');
    const error  = params.get('error');

    if (error || !token) {
      navigate('/login?error=google_failed');
      return;
    }

    // Decode user info from JWT payload (no extra request needed)
    try {
      const payload = JSON.parse(atob(token.split('.')[1]));
      // Fetch full user info to get name/avatar
      fetch('/auth/me', { headers: { Authorization: `Bearer ${token}` } })
        .then(r => r.json())
        .then(user => {
          login(token, user);
          navigate(user.role === 'admin' ? '/admin' : '/');
        })
        .catch(() => navigate('/login?error=google_failed'));
    } catch {
      navigate('/login?error=google_failed');
    }
  }, []);

  return (
    <div className="min-h-screen flex items-center justify-center bg-slate-50">
      <div className="text-center space-y-3">
        <div className="w-8 h-8 border-2 border-brand-600 border-t-transparent rounded-full animate-spin mx-auto" />
        <p className="text-sm text-slate-500">Completing sign in...</p>
      </div>
    </div>
  );
}
