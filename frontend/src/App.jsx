import { useState } from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate, Link, useNavigate } from 'react-router-dom';
import { AuthProvider, useAuth } from './context/AuthContext';
import ApplicationForm from './pages/ApplicationForm';
import ResultDashboard from './pages/ResultDashboard';
import Login from './pages/Login';
import Signup from './pages/Signup';
import History from './pages/History';
import AdminDashboard from './pages/AdminDashboard';
import { LogOut, History as HistoryIcon, LayoutDashboard } from 'lucide-react';

function ProtectedRoute({ children, adminOnly = false }) {
  const { user, loading } = useAuth();
  if (loading) return <div className="text-center py-20 text-gray-400">Loading...</div>;
  if (!user) return <Navigate to="/login" replace />;
  if (adminOnly && user.role !== 'admin') return <Navigate to="/" replace />;
  return children;
}

function Navbar() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const handleLogout = () => { logout(); navigate('/login'); };

  return (
    <nav className="bg-white border-b border-slate-100 sticky top-0 z-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between h-14 items-center">

          {/* Logo */}
          <Link to="/" className="flex items-center gap-2.5">
            <div className="w-7 h-7 rounded-lg bg-brand-600 flex items-center justify-center shadow-sm">
              <span className="text-white font-bold text-sm">N</span>
            </div>
            <span className="text-base font-bold text-slate-900 tracking-tight">
              NanoCredit <span className="text-brand-600">AI</span>
            </span>
          </Link>

          {/* Nav links */}
          {user && (
            <div className="flex items-center gap-1">
              {user.role === 'admin' && (
                <Link to="/admin" className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-sm text-slate-600 hover:bg-slate-50 hover:text-slate-900 transition-colors">
                  <LayoutDashboard size={15} /> Admin
                </Link>
              )}
              <Link to="/history" className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-sm text-slate-600 hover:bg-slate-50 hover:text-slate-900 transition-colors">
                <HistoryIcon size={15} /> History
              </Link>
              <div className="w-px h-4 bg-slate-200 mx-1" />
              <span className="text-sm text-slate-500 hidden sm:block px-2">{user.name}</span>
              <button onClick={handleLogout} className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-sm text-slate-500 hover:bg-red-50 hover:text-red-600 transition-colors">
                <LogOut size={15} />
              </button>
            </div>
          )}
        </div>
      </div>
    </nav>
  );
}

function AppRoutes() {
  const [scoringResult, setScoringResult] = useState(null);

  return (
    <>
      <Navbar />
      <main className="max-w-7xl mx-auto py-8 px-4 sm:px-6 lg:px-8">
        <Routes>
          <Route path="/login" element={<Login />} />
          <Route path="/signup" element={<Signup />} />
          <Route path="/" element={
            <ProtectedRoute>
              <ApplicationForm setScoringResult={setScoringResult} />
            </ProtectedRoute>
          } />
          <Route path="/result" element={
            <ProtectedRoute>
              {scoringResult ? <ResultDashboard result={scoringResult} /> : <Navigate to="/" replace />}
            </ProtectedRoute>
          } />
          <Route path="/history" element={
            <ProtectedRoute>
              <History />
            </ProtectedRoute>
          } />
          <Route path="/admin" element={
            <ProtectedRoute adminOnly>
              <AdminDashboard />
            </ProtectedRoute>
          } />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </main>
    </>
  );
}

export default function App() {
  return (
    <AuthProvider>
      <Router>
        <div className="min-h-screen bg-gray-50 font-sans">
          <AppRoutes />
        </div>
      </Router>
    </AuthProvider>
  );
}
