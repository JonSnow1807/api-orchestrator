import React, { useState, useEffect } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import axios from 'axios';
import { loadStripe } from '@stripe/stripe-js';
import { getApiUrl } from '../config';
import {
  CreditCard,
  Check,
  X,
  TrendingUp,
  Zap,
  Shield,
  Users,
  BarChart3,
  AlertCircle,
  Download,
  Loader2,
  Home,
  LayoutDashboard,
  User,
  LogOut
} from 'lucide-react';

// Initialize Stripe - use production key from environment
const STRIPE_KEY = import.meta.env.VITE_STRIPE_PUBLISHABLE_KEY;
if (!STRIPE_KEY) {
  console.error('Stripe publishable key is missing. Please set VITE_STRIPE_PUBLISHABLE_KEY in .env');
}
const stripePromise = STRIPE_KEY ? loadStripe(STRIPE_KEY) : null;

const Billing = () => {
  const navigate = useNavigate();
  const { user, logout } = useAuth();
  const [loading, setLoading] = useState(true);
  const [billingInfo, setBillingInfo] = useState(null);
  const [pricingTiers, setPricingTiers] = useState(null);
  const [selectedTier, setSelectedTier] = useState(null);
  const [processing, setProcessing] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');

  useEffect(() => {
    fetchBillingInfo();
    fetchPricingTiers();
  }, []);

  const fetchBillingInfo = async () => {
    try {
      const token = localStorage.getItem('access_token');
      const response = await axios.get(getApiUrl('/api/billing/info'), {
        headers: { Authorization: `Bearer ${token}` }
      });
      setBillingInfo(response.data);
    } catch (error) {
      console.error('Error fetching billing info:', error);
      setError('Failed to load billing information');
    }
  };

  const fetchPricingTiers = async () => {
    try {
      const response = await axios.get(getApiUrl('/api/billing/pricing'));
      setPricingTiers(response.data.tiers);
      setLoading(false);
    } catch (error) {
      console.error('Error fetching pricing:', error);
      setLoading(false);
    }
  };

  const handleSubscribe = async (tier) => {
    console.log('Subscribing to tier:', tier);
    
    // Get tier details for confirmation
    const tierConfig = pricingTiers?.[tier];
    if (!tierConfig) {
      setError('Invalid subscription tier');
      return;
    }
    
    // Skip confirmation and go straight to checkout
    setProcessing(true);
    setError('');
    
    try {
      const token = localStorage.getItem('access_token');
      if (!token) {
        setError('Please login to subscribe');
        navigate('/login');
        return;
      }
      
      // Create subscription
      console.log('Calling subscription API...');
      const response = await axios.post(
        getApiUrl('/api/billing/subscription'),
        { tier },
        { headers: { Authorization: `Bearer ${token}` } }
      );
      
      console.log('Subscription response:', response.data);
      
      if (response.data.checkout_url) {
        // Redirect to Stripe Checkout
        console.log('Redirecting to Stripe Checkout...');
        window.location.href = response.data.checkout_url;
      } else if (response.data.client_secret) {
        // Real Stripe payment flow (for existing customers)
        if (!stripePromise) {
          setError('Payment system is not configured.');
          return;
        }
        const stripe = await stripePromise;
        const result = await stripe.confirmCardPayment(response.data.client_secret);
        
        if (result.error) {
          setError(result.error.message);
        } else {
          setSuccess('Subscription updated successfully!');
          fetchBillingInfo();
        }
      } else {
        // Demo mode - no payment needed
        setSuccess(`✅ Demo subscription to ${tierConfig.name} tier activated! (No payment required in test mode)`);
        fetchBillingInfo();
        
        // Refresh pricing tiers to update UI
        setTimeout(() => {
          fetchPricingTiers();
        }, 1000);
      }
    } catch (error) {
      console.error('Subscription error:', error);
      const errorMessage = error.response?.data?.detail || error.message || 'Failed to update subscription';
      setError(errorMessage);
    } finally {
      setProcessing(false);
    }
  };

  const handleCancelSubscription = async () => {
    if (!window.confirm('Are you sure you want to cancel your subscription?')) return;
    
    setProcessing(true);
    try {
      const token = localStorage.getItem('access_token');
      await axios.delete(getApiUrl('/api/billing/subscription'), {
        headers: { Authorization: `Bearer ${token}` }
      });
      setSuccess('Subscription will be canceled at the end of the billing period');
      fetchBillingInfo();
    } catch (error) {
      setError('Failed to cancel subscription');
    } finally {
      setProcessing(false);
    }
  };

  const formatPrice = (price) => {
    if (price === 0) return 'Free';
    return `$${price}/month`;
  };

  const getTierFeatures = (tier) => {
    const features = {
      free: [
        '1,000 API calls/month',
        '3 projects',
        '1 team member',
        'Basic discovery & testing',
        'Community support'
      ],
      starter: [
        '10,000 API calls/month',
        '10 projects',
        '3 team members',
        'AI-powered analysis',
        'Mock servers',
        'Export/Import',
        'Email support'
      ],
      professional: [
        '100,000 API calls/month',
        '50 projects',
        '10 team members',
        'Advanced AI insights',
        'Custom integrations',
        'Priority support',
        'API analytics dashboard'
      ],
      enterprise: [
        'Unlimited API calls',
        'Unlimited projects',
        'Unlimited team members',
        'SSO/SAML authentication',
        'SLA guarantees',
        'Dedicated support',
        'Custom deployment',
        'Audit logs',
        'Custom AI models'
      ]
    };
    
    return features[tier] || [];
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <Loader2 className="w-8 h-8 animate-spin text-blue-500" />
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
                className="flex items-center space-x-2 px-4 py-2 text-purple-400 transition"
              >
                <CreditCard className="w-5 h-5" />
                <span>Billing</span>
              </Link>
              <Link
                to="/profile"
                className="flex items-center space-x-2 px-4 py-2 text-gray-300 hover:text-white transition"
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

      <div className="max-w-7xl mx-auto py-12 px-4 sm:px-6 lg:px-8">
        {/* Page Header */}
        <div className="text-center mb-12">
          <h1 className="text-4xl font-bold text-transparent bg-clip-text bg-gradient-to-r from-purple-400 to-blue-400 mb-4">
            Manage Your Subscription
          </h1>
          <p className="text-xl text-gray-400">
            Scale your API operations with flexible pricing
          </p>
          {/* Demo Mode Banner - Only show if using test key */}
          {STRIPE_KEY && STRIPE_KEY.startsWith('pk_test_') && (
            <div className="mt-4 inline-flex items-center gap-2 px-4 py-2 bg-yellow-100 text-yellow-800 rounded-lg">
              <AlertCircle className="w-5 h-5" />
              <span className="font-semibold">Test Mode Active</span>
              <span className="text-sm">- Using Stripe test environment</span>
            </div>
          )}
        </div>

        {/* Alerts */}
        {error && (
          <div className="mb-6 p-4 bg-red-500/10 border border-red-500/50 rounded-lg flex items-center">
            <AlertCircle className="w-5 h-5 text-red-400 mr-2" />
            <span className="text-red-400">{error}</span>
          </div>
        )}
        
        {success && (
          <div className="mb-6 p-4 bg-green-500/10 border border-green-500/50 rounded-lg flex items-center">
            <Check className="w-5 h-5 text-green-400 mr-2" />
            <span className="text-green-400">{success}</span>
          </div>
        )}

        {/* Current Usage */}
        {billingInfo && (
          <div className="bg-gray-800/50 backdrop-blur rounded-lg border border-gray-700 p-6 mb-8">
            <h2 className="text-2xl font-semibold text-white mb-4">Current Usage</h2>
            <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
              <div>
                <p className="text-sm text-gray-400">Current Plan</p>
                <p className="text-2xl font-bold text-white capitalize">{billingInfo.subscription.tier}</p>
              </div>
              <div>
                <p className="text-sm text-gray-400">API Calls This Month</p>
                <p className="text-2xl font-bold text-white">
                  {billingInfo.usage.api_calls.toLocaleString()}
                  {billingInfo.limits.api_calls !== -1 && (
                    <span className="text-sm text-gray-500">
                      /{billingInfo.limits.api_calls.toLocaleString()}
                    </span>
                  )}
                </p>
              </div>
              <div>
                <p className="text-sm text-gray-400">AI Analyses</p>
                <p className="text-2xl font-bold text-white">{billingInfo.usage.ai_analyses}</p>
              </div>
              <div>
                <p className="text-sm text-gray-400">Total Cost</p>
                <p className="text-2xl font-bold text-white">${billingInfo.usage.total_cost.toFixed(2)}</p>
              </div>
            </div>
            
            {/* Usage Progress Bar */}
            {billingInfo.limits.api_calls !== -1 && (
              <div className="mt-4">
                <div className="flex justify-between text-sm text-gray-400 mb-1">
                  <span>API Usage</span>
                  <span>{Math.round((billingInfo.usage.api_calls / billingInfo.limits.api_calls) * 100)}%</span>
                </div>
                <div className="w-full bg-gray-700 rounded-full h-2">
                  <div 
                    className="bg-gradient-to-r from-purple-600 to-blue-600 h-2 rounded-full"
                    style={{ width: `${Math.min(100, (billingInfo.usage.api_calls / billingInfo.limits.api_calls) * 100)}%` }}
                  />
                </div>
              </div>
            )}
          </div>
        )}

        {/* Pricing Tiers */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
          {pricingTiers && Object.entries(pricingTiers).map(([tierName, tierConfig]) => {
            const isCurrentTier = billingInfo?.subscription.tier === tierName;
            const currentTierIndex = ['free', 'starter', 'professional', 'enterprise'].indexOf(billingInfo?.subscription.tier || 'free');
            const targetTierIndex = ['free', 'starter', 'professional', 'enterprise'].indexOf(tierName);
            const isDowngrade = targetTierIndex < currentTierIndex;
            const features = getTierFeatures(tierName);
            
            return (
              <div
                key={tierName}
                className={`bg-gray-800/50 backdrop-blur-lg rounded-2xl border ${
                  isCurrentTier ? 'border-purple-500 shadow-2xl shadow-purple-500/20' : 'border-gray-700'
                } ${tierName === 'professional' ? 'transform scale-105 border-purple-500' : ''} p-6 transition-all hover:border-gray-600`}
              >
                {tierName === 'professional' && (
                  <div className="bg-gradient-to-r from-purple-600 to-blue-600 text-white text-center py-1 px-3 rounded-full text-sm font-semibold mb-4">
                    MOST POPULAR
                  </div>
                )}
                
                <h3 className="text-2xl font-bold text-white capitalize mb-2">{tierConfig.name}</h3>
                <div className="text-3xl font-bold text-white mb-4">
                  {formatPrice(tierConfig.price)}
                </div>
                
                <ul className="space-y-3 mb-6">
                  {features.map((feature, index) => (
                    <li key={index} className="flex items-start">
                      <div className="w-5 h-5 rounded-full bg-green-500/20 flex items-center justify-center flex-shrink-0 mt-0.5">
                        <Check className="w-3 h-3 text-green-400" />
                      </div>
                      <span className="text-gray-300 ml-2">{feature}</span>
                    </li>
                  ))}
                </ul>
                
                {isCurrentTier ? (
                  <button
                    className="w-full py-2 px-4 bg-purple-600/20 text-purple-400 border border-purple-500/30 rounded-lg font-semibold"
                    disabled
                  >
                    Current Plan
                  </button>
                ) : (
                  <button
                    type="button"
                    onClick={(e) => {
                      e.preventDefault();
                      e.stopPropagation();
                      handleSubscribe(tierName);
                    }}
                    disabled={processing}
                    className={`w-full py-2 px-4 rounded-lg font-semibold transition-all ${
                      tierName === 'enterprise'
                        ? 'bg-gray-700/50 text-purple-400 border border-purple-500/30 hover:bg-purple-600/20'
                        : tierName === 'professional'
                        ? 'bg-gradient-to-r from-purple-600 to-blue-600 text-white hover:opacity-90'
                        : 'bg-gray-700/50 text-gray-300 hover:bg-gray-700 hover:text-white'
                    } disabled:opacity-50`}
                  >
                    {processing ? (
                      <Loader2 className="w-5 h-5 animate-spin mx-auto" />
                    ) : tierName === 'enterprise' ? (
                      'Contact Sales'
                    ) : isDowngrade ? (
                      'Downgrade'
                    ) : (
                      'Upgrade'
                    )}
                  </button>
                )}
              </div>
            );
          })}
        </div>

        {/* Usage-Based Pricing */}
        <div className="bg-white rounded-lg shadow-lg p-6 mb-8">
          <h2 className="text-2xl font-semibold mb-4">Usage-Based Pricing</h2>
          <p className="text-gray-600 mb-4">
            Pay only for what you use beyond your plan limits
          </p>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div className="border rounded-lg p-4">
              <p className="text-sm text-gray-500">Extra API Calls</p>
              <p className="text-xl font-bold">$0.001</p>
              <p className="text-xs text-gray-500">per call</p>
            </div>
            <div className="border rounded-lg p-4">
              <p className="text-sm text-gray-500">AI Analysis</p>
              <p className="text-xl font-bold">$0.10</p>
              <p className="text-xs text-gray-500">per analysis</p>
            </div>
            <div className="border rounded-lg p-4">
              <p className="text-sm text-gray-500">Mock Server</p>
              <p className="text-xl font-bold">$0.05</p>
              <p className="text-xs text-gray-500">per hour</p>
            </div>
            <div className="border rounded-lg p-4">
              <p className="text-sm text-gray-500">Export Operation</p>
              <p className="text-xl font-bold">$0.01</p>
              <p className="text-xs text-gray-500">per export</p>
            </div>
          </div>
        </div>

        {/* Payment Methods */}
        {billingInfo?.payment_methods.length > 0 && (
          <div className="bg-white rounded-lg shadow-lg p-6 mb-8">
            <h2 className="text-2xl font-semibold mb-4">Payment Methods</h2>
            <div className="space-y-3">
              {billingInfo.payment_methods.map((method) => (
                <div key={method.id} className="flex items-center justify-between p-3 border rounded-lg">
                  <div className="flex items-center">
                    <CreditCard className="w-5 h-5 text-gray-500 mr-3" />
                    <span className="font-medium">
                      {method.brand} •••• {method.last4}
                    </span>
                    <span className="text-sm text-gray-500 ml-3">
                      Expires {method.exp_month}/{method.exp_year}
                    </span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Invoices */}
        {billingInfo?.invoices.length > 0 && (
          <div className="bg-white rounded-lg shadow-lg p-6">
            <h2 className="text-2xl font-semibold mb-4">Recent Invoices</h2>
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead>
                  <tr className="border-b">
                    <th className="text-left py-2">Date</th>
                    <th className="text-left py-2">Invoice</th>
                    <th className="text-left py-2">Amount</th>
                    <th className="text-left py-2">Status</th>
                    <th className="text-left py-2">Action</th>
                  </tr>
                </thead>
                <tbody>
                  {billingInfo.invoices.map((invoice) => (
                    <tr key={invoice.id} className="border-b">
                      <td className="py-2">{new Date(invoice.date).toLocaleDateString()}</td>
                      <td className="py-2">{invoice.number || invoice.id.slice(-8)}</td>
                      <td className="py-2">${invoice.amount.toFixed(2)}</td>
                      <td className="py-2">
                        <span className={`px-2 py-1 rounded-full text-xs ${
                          invoice.status === 'paid' 
                            ? 'bg-green-100 text-green-700'
                            : 'bg-yellow-100 text-yellow-700'
                        }`}>
                          {invoice.status}
                        </span>
                      </td>
                      <td className="py-2">
                        {invoice.pdf_url && (
                          <a
                            href={invoice.pdf_url}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="text-blue-600 hover:underline flex items-center"
                          >
                            <Download className="w-4 h-4 mr-1" />
                            Download
                          </a>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}

        {/* Cancel Subscription */}
        {billingInfo?.subscription.tier !== 'free' && (
          <div className="mt-8 text-center">
            <button
              onClick={handleCancelSubscription}
              disabled={processing}
              className="text-red-600 hover:text-red-700 font-medium"
            >
              Cancel Subscription
            </button>
          </div>
        )}
      </div>
    </div>
  );
};

export default Billing;