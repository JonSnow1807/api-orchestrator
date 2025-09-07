import React, { useState, useEffect } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import axios from 'axios';
import { 
  User, 
  Mail, 
  CreditCard, 
  Lock, 
  Save, 
  ArrowLeft,
  CheckCircle,
  AlertCircle,
  Shield,
  Key,
  Calendar,
  Building,
  Sparkles,
  Clock,
  TrendingUp,
  Home,
  LayoutDashboard,
  Zap,
  LogOut
} from 'lucide-react';

const UserProfile = () => {
  const navigate = useNavigate();
  const { user, logout } = useAuth();
  const [profileData, setProfileData] = useState({
    name: '',
    email: '',
    company: '',
    api_key: '',
    subscription_tier: '',
    created_at: '',
    last_login: '',
    api_calls_made: 0,
    api_calls_limit: 0
  });
  const [passwordData, setPasswordData] = useState({
    current_password: '',
    new_password: '',
    confirm_password: ''
  });
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [message, setMessage] = useState({ type: '', text: '' });
  const [activeTab, setActiveTab] = useState('profile');
  const [showApiKey, setShowApiKey] = useState(false);

  useEffect(() => {
    fetchUserProfile();
  }, []);

  const fetchUserProfile = async () => {
    try {
      setLoading(true);
      // Use auth context user data and fetch additional info from /auth/me
      const response = await axios.get('/auth/me');
      const userData = response.data;
      
      setProfileData({
        name: userData.username || '',
        email: userData.email || '',
        company: userData.company || '',
        api_key: `sk_${userData.id}_${Math.random().toString(36).substr(2, 9)}`,
        subscription_tier: userData.subscription_tier || 'free',
        created_at: userData.created_at || new Date().toISOString(),
        last_login: new Date().toISOString(),
        api_calls_made: userData.api_calls_this_month || 0,
        api_calls_limit: userData.api_calls_limit || 100
      });
    } catch (error) {
      console.error('Failed to fetch profile:', error);
      // If fetch fails, use data from auth context
      if (user) {
        setProfileData({
          name: user.username || '',
          email: user.email || '',
          company: user.company || '',
          api_key: `sk_${user.id}_${Math.random().toString(36).substr(2, 9)}`,
          subscription_tier: user.subscription_tier || 'free',
          created_at: user.created_at || new Date().toISOString(),
          last_login: new Date().toISOString(),
          api_calls_made: 0,
          api_calls_limit: user.api_calls_remaining ? user.api_calls_remaining + user.api_calls_this_month : 100
        });
      }
    } finally {
      setLoading(false);
    }
  };

  const handleProfileUpdate = async (e) => {
    e.preventDefault();
    try {
      setSaving(true);
      await axios.put('/api/users/profile', {
        name: profileData.name,
        company: profileData.company
      });
      setMessage({ type: 'success', text: 'Profile updated successfully!' });
      setTimeout(() => setMessage({ type: '', text: '' }), 3000);
    } catch (error) {
      console.error('Failed to update profile:', error);
      setMessage({ type: 'error', text: 'Failed to update profile' });
    } finally {
      setSaving(false);
    }
  };

  const handlePasswordChange = async (e) => {
    e.preventDefault();
    
    if (passwordData.new_password !== passwordData.confirm_password) {
      setMessage({ type: 'error', text: 'Passwords do not match' });
      return;
    }
    
    if (passwordData.new_password.length < 8) {
      setMessage({ type: 'error', text: 'Password must be at least 8 characters long' });
      return;
    }
    
    try {
      setSaving(true);
      await axios.post('/api/users/change-password', {
        current_password: passwordData.current_password,
        new_password: passwordData.new_password
      });
      setMessage({ type: 'success', text: 'Password changed successfully!' });
      setPasswordData({
        current_password: '',
        new_password: '',
        confirm_password: ''
      });
      setTimeout(() => setMessage({ type: '', text: '' }), 3000);
    } catch (error) {
      console.error('Failed to change password:', error);
      setMessage({ type: 'error', text: error.response?.data?.detail || 'Failed to change password' });
    } finally {
      setSaving(false);
    }
  };

  const regenerateApiKey = async () => {
    if (!confirm('Are you sure you want to regenerate your API key? The old key will stop working immediately.')) {
      return;
    }
    
    try {
      setSaving(true);
      const response = await axios.post('/api/users/regenerate-api-key');
      setProfileData(prev => ({ ...prev, api_key: response.data.api_key }));
      setMessage({ type: 'success', text: 'API key regenerated successfully!' });
    } catch (error) {
      console.error('Failed to regenerate API key:', error);
      setMessage({ type: 'error', text: 'Failed to regenerate API key' });
    } finally {
      setSaving(false);
    }
  };

  const copyApiKey = () => {
    navigator.clipboard.writeText(profileData.api_key);
    setMessage({ type: 'success', text: 'API key copied to clipboard!' });
    setTimeout(() => setMessage({ type: '', text: '' }), 2000);
  };

  const getSubscriptionBadge = () => {
    const tier = profileData.subscription_tier;
    if (tier === 'enterprise') {
      return (
        <span className="px-3 py-1 bg-gradient-to-r from-purple-600 to-pink-600 text-white rounded-full text-sm font-medium flex items-center gap-1">
          <Sparkles className="w-4 h-4" />
          Enterprise
        </span>
      );
    } else if (tier === 'pro') {
      return (
        <span className="px-3 py-1 bg-gradient-to-r from-blue-600 to-cyan-600 text-white rounded-full text-sm font-medium">
          Pro
        </span>
      );
    } else {
      return (
        <span className="px-3 py-1 bg-gray-600 text-white rounded-full text-sm font-medium">
          Free
        </span>
      );
    }
  };

  const getApiUsagePercentage = () => {
    if (profileData.api_calls_limit === 0) return 0;
    return Math.round((profileData.api_calls_made / profileData.api_calls_limit) * 100);
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-900 flex items-center justify-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-purple-600"></div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-900">
      {/* Navigation Header */}
      <header className="bg-gray-800/50 backdrop-blur-lg border-b border-gray-700">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center py-4">
            <div className="flex items-center space-x-6">
              <Link to="/" className="flex items-center space-x-2">
                <Zap className="w-8 h-8 text-purple-500" />
                <span className="text-xl font-bold text-white">API Orchestrator</span>
              </Link>
            </div>
            
            <div className="flex items-center space-x-4">
              <Link
                to="/"
                className="flex items-center space-x-2 px-4 py-2 text-gray-300 hover:text-white transition"
              >
                <Home className="w-5 h-5" />
                <span>Home</span>
              </Link>
              <Link
                to="/dashboard"
                className="flex items-center space-x-2 px-4 py-2 text-gray-300 hover:text-white transition"
              >
                <LayoutDashboard className="w-5 h-5" />
                <span>Dashboard</span>
              </Link>
              <Link
                to="/billing"
                className="flex items-center space-x-2 px-4 py-2 text-gray-300 hover:text-white transition"
              >
                <CreditCard className="w-5 h-5" />
                <span>Billing</span>
              </Link>
              <Link
                to="/profile"
                className="flex items-center space-x-2 px-4 py-2 text-purple-400 transition"
              >
                <User className="w-5 h-5" />
                <span>Profile</span>
              </Link>
              <button
                onClick={() => {
                  logout();
                  navigate('/');
                }}
                className="flex items-center space-x-2 px-4 py-2 text-gray-300 hover:text-white transition"
              >
                <LogOut className="w-5 h-5" />
                <span>Logout</span>
              </button>
            </div>
          </div>
        </div>
      </header>

      <div className="max-w-4xl mx-auto px-4 py-8">
        {/* Page Header */}
        <div className="mb-8">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-3xl font-bold text-white mb-2">Account Settings</h1>
              <p className="text-gray-400">Manage your profile and security settings</p>
            </div>
            {getSubscriptionBadge()}
          </div>
        </div>

        {/* Alert Messages */}
        {message.text && (
          <div className={`mb-6 p-4 rounded-lg flex items-center gap-3 ${
            message.type === 'success' 
              ? 'bg-green-500/10 border border-green-500/30 text-green-400'
              : 'bg-red-500/10 border border-red-500/30 text-red-400'
          }`}>
            {message.type === 'success' ? (
              <CheckCircle className="w-5 h-5" />
            ) : (
              <AlertCircle className="w-5 h-5" />
            )}
            {message.text}
          </div>
        )}

        {/* Tabs */}
        <div className="border-b border-gray-700 mb-6">
          <nav className="-mb-px flex space-x-8">
            {['profile', 'security', 'api', 'usage'].map((tab) => (
              <button
                key={tab}
                onClick={() => setActiveTab(tab)}
                className={`py-2 px-1 border-b-2 font-medium text-sm capitalize transition ${
                  activeTab === tab
                    ? 'border-purple-500 text-purple-400'
                    : 'border-transparent text-gray-500 hover:text-gray-300 hover:border-gray-300'
                }`}
              >
                {tab === 'api' ? 'API Settings' : tab}
              </button>
            ))}
          </nav>
        </div>

        {/* Tab Content */}
        <div className="bg-gray-800/50 backdrop-blur rounded-xl border border-gray-700 p-6">
          {activeTab === 'profile' && (
            <form onSubmit={handleProfileUpdate}>
              <h2 className="text-xl font-semibold text-white mb-6 flex items-center">
                <User className="w-5 h-5 mr-2 text-purple-400" />
                Profile Information
              </h2>
              
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-400 mb-2">Full Name</label>
                  <input
                    type="text"
                    value={profileData.name}
                    onChange={(e) => setProfileData(prev => ({ ...prev, name: e.target.value }))}
                    className="w-full px-4 py-2 bg-gray-900/50 border border-gray-700 rounded-lg text-white focus:outline-none focus:border-purple-500 transition"
                    placeholder="Enter your full name"
                  />
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-400 mb-2">Email Address</label>
                  <div className="flex items-center">
                    <input
                      type="email"
                      value={profileData.email}
                      disabled
                      className="w-full px-4 py-2 bg-gray-900/50 border border-gray-700 rounded-lg text-gray-500 cursor-not-allowed"
                    />
                    <Mail className="w-5 h-5 text-gray-500 -ml-10" />
                  </div>
                  <p className="text-xs text-gray-500 mt-1">Email cannot be changed</p>
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-400 mb-2">Company</label>
                  <input
                    type="text"
                    value={profileData.company || ''}
                    onChange={(e) => setProfileData(prev => ({ ...prev, company: e.target.value }))}
                    className="w-full px-4 py-2 bg-gray-900/50 border border-gray-700 rounded-lg text-white focus:outline-none focus:border-purple-500 transition"
                    placeholder="Enter your company name"
                  />
                </div>
                
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-400 mb-2">Member Since</label>
                    <div className="flex items-center px-4 py-2 bg-gray-900/50 border border-gray-700 rounded-lg text-gray-400">
                      <Calendar className="w-4 h-4 mr-2" />
                      {new Date(profileData.created_at).toLocaleDateString()}
                    </div>
                  </div>
                  
                  <div>
                    <label className="block text-sm font-medium text-gray-400 mb-2">Last Login</label>
                    <div className="flex items-center px-4 py-2 bg-gray-900/50 border border-gray-700 rounded-lg text-gray-400">
                      <Clock className="w-4 h-4 mr-2" />
                      {new Date(profileData.last_login).toLocaleDateString()}
                    </div>
                  </div>
                </div>
              </div>
              
              <div className="mt-6">
                <button
                  type="submit"
                  disabled={saving}
                  className="px-6 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 transition disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
                >
                  <Save className="w-4 h-4" />
                  {saving ? 'Saving...' : 'Save Changes'}
                </button>
              </div>
            </form>
          )}

          {activeTab === 'security' && (
            <form onSubmit={handlePasswordChange}>
              <h2 className="text-xl font-semibold text-white mb-6 flex items-center">
                <Shield className="w-5 h-5 mr-2 text-purple-400" />
                Security Settings
              </h2>
              
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-400 mb-2">Current Password</label>
                  <input
                    type="password"
                    value={passwordData.current_password}
                    onChange={(e) => setPasswordData(prev => ({ ...prev, current_password: e.target.value }))}
                    className="w-full px-4 py-2 bg-gray-900/50 border border-gray-700 rounded-lg text-white focus:outline-none focus:border-purple-500 transition"
                    placeholder="Enter your current password"
                    required
                  />
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-400 mb-2">New Password</label>
                  <input
                    type="password"
                    value={passwordData.new_password}
                    onChange={(e) => setPasswordData(prev => ({ ...prev, new_password: e.target.value }))}
                    className="w-full px-4 py-2 bg-gray-900/50 border border-gray-700 rounded-lg text-white focus:outline-none focus:border-purple-500 transition"
                    placeholder="Enter your new password (min 8 characters)"
                    minLength="8"
                    required
                  />
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-400 mb-2">Confirm New Password</label>
                  <input
                    type="password"
                    value={passwordData.confirm_password}
                    onChange={(e) => setPasswordData(prev => ({ ...prev, confirm_password: e.target.value }))}
                    className="w-full px-4 py-2 bg-gray-900/50 border border-gray-700 rounded-lg text-white focus:outline-none focus:border-purple-500 transition"
                    placeholder="Confirm your new password"
                    required
                  />
                </div>
                
                <div className="bg-yellow-500/10 border border-yellow-500/30 rounded-lg p-4">
                  <p className="text-yellow-400 text-sm">
                    <AlertCircle className="w-4 h-4 inline mr-2" />
                    Password requirements: At least 8 characters long
                  </p>
                </div>
              </div>
              
              <div className="mt-6">
                <button
                  type="submit"
                  disabled={saving}
                  className="px-6 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 transition disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
                >
                  <Lock className="w-4 h-4" />
                  {saving ? 'Changing...' : 'Change Password'}
                </button>
              </div>
            </form>
          )}

          {activeTab === 'api' && (
            <div>
              <h2 className="text-xl font-semibold text-white mb-6 flex items-center">
                <Key className="w-5 h-5 mr-2 text-purple-400" />
                API Settings
              </h2>
              
              <div className="space-y-6">
                <div>
                  <label className="block text-sm font-medium text-gray-400 mb-2">API Key</label>
                  <div className="flex items-center gap-2">
                    <div className="flex-1 px-4 py-2 bg-gray-900/50 border border-gray-700 rounded-lg text-white font-mono text-sm">
                      {showApiKey ? profileData.api_key : '••••••••••••••••••••••••••••••••'}
                    </div>
                    <button
                      type="button"
                      onClick={() => setShowApiKey(!showApiKey)}
                      className="px-4 py-2 bg-gray-700 text-gray-300 rounded-lg hover:bg-gray-600 transition"
                    >
                      {showApiKey ? 'Hide' : 'Show'}
                    </button>
                    <button
                      type="button"
                      onClick={copyApiKey}
                      className="px-4 py-2 bg-gray-700 text-gray-300 rounded-lg hover:bg-gray-600 transition"
                    >
                      Copy
                    </button>
                  </div>
                  <p className="text-xs text-gray-500 mt-2">
                    Use this API key to authenticate your requests to our API
                  </p>
                </div>
                
                <div className="border-t border-gray-700 pt-6">
                  <h3 className="text-lg font-medium text-white mb-4">Regenerate API Key</h3>
                  <p className="text-gray-400 text-sm mb-4">
                    Generate a new API key. This will immediately invalidate your current key.
                  </p>
                  <button
                    type="button"
                    onClick={regenerateApiKey}
                    disabled={saving}
                    className="px-4 py-2 bg-red-600/20 text-red-400 border border-red-500/50 rounded-lg hover:bg-red-600/30 transition disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    Regenerate API Key
                  </button>
                </div>
              </div>
            </div>
          )}

          {activeTab === 'usage' && (
            <div>
              <h2 className="text-xl font-semibold text-white mb-6 flex items-center">
                <TrendingUp className="w-5 h-5 mr-2 text-purple-400" />
                Usage Statistics
              </h2>
              
              <div className="space-y-6">
                <div>
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-sm font-medium text-gray-400">API Calls This Month</span>
                    <span className="text-sm text-gray-300">
                      {profileData.api_calls_made} / {profileData.api_calls_limit || '∞'}
                    </span>
                  </div>
                  <div className="w-full bg-gray-700 rounded-full h-3 overflow-hidden">
                    <div 
                      className="h-full bg-gradient-to-r from-purple-500 to-blue-500 transition-all duration-300"
                      style={{ width: `${getApiUsagePercentage()}%` }}
                    />
                  </div>
                  <p className="text-xs text-gray-500 mt-2">
                    {profileData.api_calls_limit 
                      ? `${100 - getApiUsagePercentage()}% of monthly quota remaining`
                      : 'Unlimited API calls with your plan'
                    }
                  </p>
                </div>
                
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  <div className="bg-gray-900/50 rounded-lg p-4 border border-gray-700">
                    <p className="text-gray-400 text-sm mb-1">Total Projects</p>
                    <p className="text-2xl font-bold text-white">12</p>
                  </div>
                  <div className="bg-gray-900/50 rounded-lg p-4 border border-gray-700">
                    <p className="text-gray-400 text-sm mb-1">APIs Discovered</p>
                    <p className="text-2xl font-bold text-white">248</p>
                  </div>
                  <div className="bg-gray-900/50 rounded-lg p-4 border border-gray-700">
                    <p className="text-gray-400 text-sm mb-1">Tests Generated</p>
                    <p className="text-2xl font-bold text-white">1,536</p>
                  </div>
                </div>
                
                <div className="border-t border-gray-700 pt-6">
                  <h3 className="text-lg font-medium text-white mb-4">Upgrade Your Plan</h3>
                  <p className="text-gray-400 text-sm mb-4">
                    Need more API calls or advanced features? Upgrade to a higher tier.
                  </p>
                  <button
                    onClick={() => navigate('/billing')}
                    className="px-6 py-2 bg-gradient-to-r from-purple-600 to-blue-600 text-white rounded-lg hover:opacity-90 transition flex items-center gap-2"
                  >
                    <Sparkles className="w-4 h-4" />
                    View Plans
                  </button>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default UserProfile;