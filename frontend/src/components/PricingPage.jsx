import React from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { Check, X, Zap, ArrowRight, Star, Shield, Rocket } from 'lucide-react';
import { useAuth } from '../contexts/AuthContext';

const PricingPage = () => {
  const { user } = useAuth();
  const navigate = useNavigate();

  const plans = [
    {
      name: 'Free',
      price: '$0',
      period: 'forever',
      description: 'Perfect for individual developers',
      features: [
        '100 API calls/month',
        '3 Projects',
        '1 Mock Server',
        'Basic API Discovery',
        'JSON Export',
        'Community Support',
      ],
      limitations: [
        'No AI Analysis',
        'No Team Collaboration',
        'No Custom Domains',
        'No Priority Support',
      ],
      cta: 'Get Started',
      popular: false,
      gradient: 'from-gray-600 to-gray-700',
    },
    {
      name: 'Starter',
      price: '$29',
      period: '/month',
      description: 'For growing teams and projects',
      features: [
        '1,000 API calls/month',
        '10 Projects',
        '3 Mock Servers',
        'AI-Powered Analysis',
        'Multiple Export Formats',
        'Email Support',
        'Team Collaboration',
        'Custom Domains',
      ],
      limitations: [
        'No Webhooks',
        'No SSO',
      ],
      cta: 'Start Free Trial',
      popular: true,
      gradient: 'from-purple-600 to-blue-600',
    },
    {
      name: 'Growth',
      price: '$99',
      period: '/month',
      description: 'For professional teams',
      features: [
        '10,000 API calls/month',
        '50 Projects',
        '10 Mock Servers',
        'Advanced AI Analysis',
        'All Export Formats',
        'Priority Support',
        'Unlimited Team Members',
        'Webhooks & Integrations',
        'API Versioning',
        'Custom Branding',
      ],
      limitations: [],
      cta: 'Start Free Trial',
      popular: false,
      gradient: 'from-blue-600 to-cyan-600',
    },
    {
      name: 'Enterprise',
      price: 'Custom',
      period: '',
      description: 'For large organizations',
      features: [
        'Unlimited API calls',
        'Unlimited Projects',
        'Unlimited Mock Servers',
        'Custom AI Models',
        'Dedicated Support',
        'SSO & SAML',
        'SLA Guarantee',
        'On-premise Deployment',
        'Custom Integrations',
        'Compliance Reports',
      ],
      limitations: [],
      cta: 'Contact Sales',
      popular: false,
      gradient: 'from-indigo-600 to-purple-600',
    },
  ];

  const handlePlanAction = (plan) => {
    if (!user) {
      // Not logged in - redirect to register/login
      if (plan.name === 'Free') {
        navigate('/register');
      } else if (plan.name === 'Enterprise') {
        // For enterprise, could open a contact form or mailto
        window.location.href = 'mailto:sales@streamapi.dev?subject=Enterprise Plan Inquiry';
      } else {
        // For paid plans, go to register with plan info
        navigate('/register', { state: { selectedPlan: plan.name } });
      }
    } else {
      // Logged in - go to billing page
      navigate('/billing');
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-900 via-purple-900/10 to-gray-900">
      {/* Header */}
      <header className="bg-gray-800/50 backdrop-blur-lg border-b border-gray-700">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center py-4">
            <Link to="/" className="flex items-center space-x-2">
              <Zap className="w-8 h-8 text-purple-500" />
              <h1 className="text-2xl font-bold text-white">API Orchestrator</h1>
            </Link>
            
            <div className="flex items-center space-x-4">
              {user ? (
                <>
                  <Link to="/dashboard" className="text-gray-300 hover:text-white transition">
                    Dashboard
                  </Link>
                  <Link to="/billing" className="text-gray-300 hover:text-white transition">
                    Manage Subscription
                  </Link>
                  <span className="px-3 py-1 bg-purple-600/20 text-purple-400 text-sm rounded-full border border-purple-500/30">
                    Current: {user.subscription_tier || 'Free'}
                  </span>
                </>
              ) : (
                <>
                  <Link to="/login" className="text-gray-300 hover:text-white transition">
                    Sign In
                  </Link>
                  <Link 
                    to="/register" 
                    className="px-4 py-2 bg-gradient-to-r from-purple-600 to-blue-600 text-white rounded-lg hover:opacity-90 transition"
                  >
                    Get Started Free
                  </Link>
                </>
              )}
            </div>
          </div>
        </div>
      </header>

      {/* Hero Section */}
      <div className="text-center py-16">
        <h1 className="text-5xl font-bold text-white mb-4">
          Choose Your Perfect Plan
        </h1>
        <p className="text-xl text-gray-300 max-w-2xl mx-auto">
          Start free and scale as you grow. No credit card required for free tier.
        </p>
        
        {/* Trust Badges */}
        <div className="flex justify-center items-center gap-8 mt-8">
          <div className="flex items-center gap-2 text-gray-400">
            <Shield className="w-5 h-5 text-green-400" />
            <span>SOC2 Compliant</span>
          </div>
          <div className="flex items-center gap-2 text-gray-400">
            <Star className="w-5 h-5 text-yellow-400" />
            <span>4.9/5 Rating</span>
          </div>
          <div className="flex items-center gap-2 text-gray-400">
            <Rocket className="w-5 h-5 text-blue-400" />
            <span>Used by 10,000+ Developers</span>
          </div>
        </div>
      </div>

      {/* Pricing Cards */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 pb-20">
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          {plans.map((plan) => (
            <div
              key={plan.name}
              className={`relative rounded-2xl bg-gray-800/50 backdrop-blur-lg border ${
                plan.popular ? 'border-purple-500 shadow-2xl shadow-purple-500/20' : 'border-gray-700'
              } p-6 hover:transform hover:scale-105 transition-all duration-300`}
            >
              {plan.popular && (
                <div className="absolute -top-4 left-1/2 transform -translate-x-1/2">
                  <span className="px-4 py-1 bg-gradient-to-r from-purple-600 to-blue-600 text-white text-sm font-semibold rounded-full">
                    MOST POPULAR
                  </span>
                </div>
              )}

              <div className="mb-6">
                <h3 className="text-2xl font-bold text-white mb-2">{plan.name}</h3>
                <div className="flex items-baseline mb-2">
                  <span className="text-4xl font-bold text-white">{plan.price}</span>
                  <span className="text-gray-400 ml-1">{plan.period}</span>
                </div>
                <p className="text-gray-400 text-sm">{plan.description}</p>
              </div>

              <div className="space-y-3 mb-6">
                {plan.features.map((feature, index) => (
                  <div key={index} className="flex items-start gap-2">
                    <Check className="w-5 h-5 text-green-400 flex-shrink-0 mt-0.5" />
                    <span className="text-gray-300 text-sm">{feature}</span>
                  </div>
                ))}
                {plan.limitations.map((limitation, index) => (
                  <div key={index} className="flex items-start gap-2">
                    <X className="w-5 h-5 text-gray-500 flex-shrink-0 mt-0.5" />
                    <span className="text-gray-500 text-sm line-through">{limitation}</span>
                  </div>
                ))}
              </div>

              <button
                onClick={() => handlePlanAction(plan)}
                className={`w-full py-3 rounded-lg font-semibold transition-all duration-300 ${
                  plan.popular
                    ? 'bg-gradient-to-r from-purple-600 to-blue-600 text-white hover:opacity-90'
                    : 'bg-gray-700 text-white hover:bg-gray-600'
                } flex items-center justify-center gap-2`}
              >
                {plan.cta}
                <ArrowRight className="w-4 h-4" />
              </button>
            </div>
          ))}
        </div>
      </div>

      {/* FAQ Section */}
      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 pb-20">
        <h2 className="text-3xl font-bold text-white text-center mb-8">
          Frequently Asked Questions
        </h2>
        
        <div className="space-y-4">
          <div className="bg-gray-800/50 backdrop-blur-lg rounded-lg p-6 border border-gray-700">
            <h3 className="text-lg font-semibold text-white mb-2">
              Can I change plans anytime?
            </h3>
            <p className="text-gray-400">
              Yes! You can upgrade or downgrade your plan at any time. Changes take effect immediately.
            </p>
          </div>
          
          <div className="bg-gray-800/50 backdrop-blur-lg rounded-lg p-6 border border-gray-700">
            <h3 className="text-lg font-semibold text-white mb-2">
              Is there a free trial for paid plans?
            </h3>
            <p className="text-gray-400">
              Yes, all paid plans come with a 14-day free trial. No credit card required to start.
            </p>
          </div>
          
          <div className="bg-gray-800/50 backdrop-blur-lg rounded-lg p-6 border border-gray-700">
            <h3 className="text-lg font-semibold text-white mb-2">
              What happens if I exceed my API call limit?
            </h3>
            <p className="text-gray-400">
              For paid plans, you can enable overage billing. For free plans, API calls will be blocked until the next month.
            </p>
          </div>
        </div>
      </div>

      {/* CTA Section */}
      {!user && (
        <div className="bg-gradient-to-r from-purple-600 to-blue-600 py-16">
          <div className="max-w-4xl mx-auto text-center px-4">
            <h2 className="text-3xl font-bold text-white mb-4">
              Ready to Transform Your API Development?
            </h2>
            <p className="text-xl text-white/90 mb-8">
              Join thousands of developers using AI to build better APIs faster.
            </p>
            <Link
              to="/register"
              className="inline-flex items-center gap-2 px-8 py-4 bg-white text-purple-600 font-bold rounded-lg hover:bg-gray-100 transition"
            >
              Start Free Today
              <ArrowRight className="w-5 h-5" />
            </Link>
          </div>
        </div>
      )}
    </div>
  );
};

export default PricingPage;