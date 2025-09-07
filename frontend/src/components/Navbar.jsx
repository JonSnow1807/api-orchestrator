import React from 'react';
import { Link, useNavigate, useLocation } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { 
  Zap, 
  Home,
  LogIn,
  LogOut,
  User,
  LayoutDashboard,
  FileText,
  CreditCard
} from 'lucide-react';

const Navbar = () => {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();

  const handleLogout = () => {
    logout();
    navigate('/');
  };

  const isActive = (path) => {
    return location.pathname === path;
  };

  return (
    <nav className="fixed top-0 w-full bg-gray-900/95 backdrop-blur-md z-50 border-b border-gray-800">
      <div className="max-w-7xl mx-auto px-6 py-4">
        <div className="flex items-center justify-between">
          {/* Logo */}
          <Link to="/" className="flex items-center space-x-2 hover:opacity-90 transition">
            <Zap className="w-8 h-8 text-purple-500" />
            <span className="text-xl font-bold text-white">API Orchestrator</span>
          </Link>

          {/* Navigation Links */}
          <div className="flex items-center space-x-6">
            {!user ? (
              // Public Navigation
              <>
                <Link 
                  to="/" 
                  className={`flex items-center space-x-1 transition ${
                    isActive('/') ? 'text-purple-400' : 'text-gray-300 hover:text-white'
                  }`}
                >
                  <Home className="w-4 h-4" />
                  <span>Home</span>
                </Link>
                <Link 
                  to="/docs" 
                  className={`flex items-center space-x-1 transition ${
                    isActive('/docs') ? 'text-purple-400' : 'text-gray-300 hover:text-white'
                  }`}
                  onClick={(e) => {
                    e.preventDefault();
                    window.open('https://streamapi.dev/docs', '_blank');
                  }}
                >
                  <FileText className="w-4 h-4" />
                  <span>API Docs</span>
                </Link>
                <div className="flex items-center space-x-3 ml-4">
                  <Link
                    to="/login"
                    className="px-4 py-2 text-purple-400 border border-purple-400 rounded-lg hover:bg-purple-400 hover:text-white transition"
                  >
                    <span className="flex items-center space-x-1">
                      <LogIn className="w-4 h-4" />
                      <span>Login</span>
                    </span>
                  </Link>
                  <Link
                    to="/register"
                    className="px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 transition"
                  >
                    Get Started
                  </Link>
                </div>
              </>
            ) : (
              // Authenticated Navigation
              <>
                <Link 
                  to="/dashboard" 
                  className={`flex items-center space-x-1 transition ${
                    isActive('/dashboard') ? 'text-purple-400' : 'text-gray-300 hover:text-white'
                  }`}
                >
                  <LayoutDashboard className="w-4 h-4" />
                  <span>Dashboard</span>
                </Link>
                <Link 
                  to="/profile" 
                  className={`flex items-center space-x-1 transition ${
                    isActive('/profile') ? 'text-purple-400' : 'text-gray-300 hover:text-white'
                  }`}
                >
                  <User className="w-4 h-4" />
                  <span>Profile</span>
                </Link>
                <Link 
                  to="/billing" 
                  className={`flex items-center space-x-1 transition ${
                    isActive('/billing') ? 'text-purple-400' : 'text-gray-300 hover:text-white'
                  }`}
                >
                  <CreditCard className="w-4 h-4" />
                  <span>Billing</span>
                </Link>
                <div className="flex items-center space-x-3 ml-4">
                  <span className="text-gray-400 text-sm">
                    {user.email}
                  </span>
                  <button
                    onClick={handleLogout}
                    className="px-4 py-2 text-red-400 border border-red-400 rounded-lg hover:bg-red-400 hover:text-white transition"
                  >
                    <span className="flex items-center space-x-1">
                      <LogOut className="w-4 h-4" />
                      <span>Logout</span>
                    </span>
                  </button>
                </div>
              </>
            )}
          </div>
        </div>
      </div>
    </nav>
  );
};

export default Navbar;