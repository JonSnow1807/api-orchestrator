import React from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { Check, X, Zap, ArrowRight, Star, Shield, Rocket, Crown } from 'lucide-react';
import { useAuth } from '../contexts/AuthContext';

const PricingPage = () => {
  const { user } = useAuth();
  const navigate = useNavigate();

  const plans = [
    {
      name: 'Free',
      price: '$0',
      period: '/month',
      description: 'Perfect for individuals',
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
      ],
      cta: 'Get Started',
      popular: false,
    },
    {
      name: 'Starter',
      price: '$29',
      period: '/month',
      description: 'For growing teams',
      features: [
        '1,000 API calls/month',
        '10 Projects',
        '3 Mock Servers',
        'AI-Powered Analysis',
        'All Export Formats',
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
        'Priority Support',
        'Unlimited Team Members',
        'Webhooks & Integrations',
        'API Versioning',
        'Custom Branding',
      ],
      limitations: [],
      cta: 'Get Started',
      popular: false,
    },
    {
      name: 'AI Workforce',
      price: '$299',
      period: '/month',
      description: 'Autonomous AI agents for your APIs',
      features: [
        'Everything in Growth',
        '🤖 Autonomous AI Agents',
        '🔧 Auto-fix Security Issues',
        '⚡ Auto-generate & Run Tests',
        '🎯 Predictive Optimization',
        '🛠️ AI Code Generation',
        '📊 24/7 AI Monitoring',
        '🔄 Cross-agent Coordination',
        'Priority AI Support',
      ],
      limitations: [],
      cta: 'Start AI Beta',
      popular: true,
      badge: '🚀 NEW',
      highlight: true,
    },
    {
      name: 'Enterprise',
      price: 'Custom',
      period: '',
      description: 'For large organizations',
      features: [
        'Everything in AI Workforce',
        'Unlimited API calls',
        'Custom AI Models',
        'Dedicated Support',
        'SSO & SAML',
        'SLA Guarantee',
        'On-premise Option',
        'Custom Integrations',
      ],
      limitations: [],
      cta: 'Contact Sales',
      popular: false,
    },
  ];

  const handlePlanAction = (plan) => {
    if (!user) {
      if (plan.name === 'Free') {
        navigate('/register');
      } else if (plan.name === 'Enterprise') {
        window.location.href = 'mailto:sales@streamapi.dev?subject=Enterprise Plan Inquiry';
      } else if (plan.name === 'AI Workforce') {
        window.location.href = 'mailto:sales@streamapi.dev?subject=AI Workforce Beta Access Request';
      } else {
        // For paid plans, save the plan and redirect to register
        navigate('/register', { state: { selectedPlan: plan.name, redirectToBilling: true } });
      }
    } else {
      navigate('/billing');
    }
  };

  return (
    <div className="min-h-screen bg-gray-900">
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
                  <span className="px-3 py-1 bg-purple-600/20 text-purple-400 text-sm rounded-full border border-purple-500/30 whitespace-nowrap">
                    Current: {(user.subscription_tier || 'Free').charAt(0).toUpperCase() + (user.subscription_tier || 'free').slice(1)}
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
      <div className="relative overflow-hidden">
        {/* Background gradient effect */}
        <div className="absolute inset-0 bg-gradient-to-br from-purple-900/20 via-transparent to-blue-900/20"></div>
        
        <div className="relative text-center py-16">
          <div className="inline-flex items-center gap-2 px-4 py-2 bg-purple-600/10 border border-purple-500/30 rounded-full text-purple-400 text-sm mb-6">
            <Star className="w-4 h-4" />
            <span>Trusted by 10,000+ developers</span>
          </div>
          
          <h1 className="text-5xl font-bold text-transparent bg-clip-text bg-gradient-to-r from-purple-400 to-blue-400 mb-4">
            Simple, Transparent Pricing
          </h1>
          <p className="text-xl text-gray-400 max-w-2xl mx-auto">
            Start free and scale as you grow. No credit card required.
          </p>
        </div>
      </div>

      {/* Pricing Cards */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 pb-20 -mt-8">
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          {plans.map((plan, index) => (
            <div
              key={plan.name}
              className={`relative ${plan.popular ? 'lg:-mt-4' : ''}`}
            >
              {/* Popular badge - with higher z-index */}
              {plan.popular && (
                <div className="absolute -top-5 left-0 right-0 flex justify-center z-10">
                  <div className="px-4 py-1 bg-gradient-to-r from-purple-600 to-blue-600 text-white text-xs font-bold rounded-full shadow-lg">
                    {plan.badge || 'MOST POPULAR'}
                  </div>
                </div>
              )}
              
              {/* Card */}
              <div className={`
                relative h-full rounded-2xl p-6
                ${plan.highlight
                  ? 'bg-gradient-to-b from-blue-900/40 to-purple-900/40 border-2 border-blue-400 shadow-2xl shadow-blue-500/25'
                  : plan.popular
                    ? 'bg-gradient-to-b from-purple-900/30 to-gray-800/50 border-2 border-purple-500 shadow-2xl shadow-purple-500/20'
                    : 'bg-gray-800/50 border border-gray-700 hover:border-gray-600'
                }
                backdrop-blur-lg transition-all duration-300
                hover:transform hover:scale-[1.02]
              `}>
                {/* Plan header */}
                <div className="mb-6">
                  <h3 className="text-2xl font-bold text-white mb-2">
                    {plan.name}
                  </h3>
                  <p className="text-gray-400 text-sm mb-4">{plan.description}</p>
                  <div className="flex items-baseline">
                    <span className="text-4xl font-bold text-white">{plan.price}</span>
                    {plan.period && (
                      <span className="text-gray-400 ml-1">{plan.period}</span>
                    )}
                  </div>
                </div>

                {/* Features */}
                <div className="space-y-3 mb-8">
                  {plan.features.map((feature, idx) => (
                    <div key={idx} className="flex items-start gap-3">
                      <div className="w-5 h-5 rounded-full bg-green-500/20 flex items-center justify-center flex-shrink-0 mt-0.5">
                        <Check className="w-3 h-3 text-green-400" />
                      </div>
                      <span className="text-gray-300 text-sm">{feature}</span>
                    </div>
                  ))}
                  {plan.limitations.map((limitation, idx) => (
                    <div key={idx} className="flex items-start gap-3 opacity-50">
                      <div className="w-5 h-5 rounded-full bg-gray-700 flex items-center justify-center flex-shrink-0 mt-0.5">
                        <X className="w-3 h-3 text-gray-500" />
                      </div>
                      <span className="text-gray-500 text-sm line-through">{limitation}</span>
                    </div>
                  ))}
                </div>

                {/* CTA Button */}
                <button
                  onClick={() => handlePlanAction(plan)}
                  className={`
                    w-full py-3 rounded-lg font-semibold transition-all duration-300
                    flex items-center justify-center gap-2
                    ${plan.popular
                      ? 'bg-gradient-to-r from-purple-600 to-blue-600 text-white hover:opacity-90 shadow-lg'
                      : plan.name === 'Enterprise'
                      ? 'bg-gray-700/50 text-purple-400 border border-purple-500/30 hover:bg-purple-600/20'
                      : 'bg-gray-700/50 text-gray-300 hover:bg-gray-700 hover:text-white'
                    }
                  `}
                >
                  {plan.cta}
                  <ArrowRight className="w-4 h-4" />
                </button>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Features comparison */}
      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 pb-20">
        <div className="text-center mb-12">
          <h2 className="text-3xl font-bold text-white mb-4">
            Why Teams Choose API Orchestrator
          </h2>
          <p className="text-gray-400">
            Everything you need to build, test, and document APIs faster
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <div className="bg-gray-800/30 backdrop-blur-lg rounded-xl p-6 border border-gray-700">
            <div className="w-12 h-12 bg-purple-600/20 rounded-lg flex items-center justify-center mb-4">
              <Zap className="w-6 h-6 text-purple-400" />
            </div>
            <h3 className="text-lg font-semibold text-white mb-2">AI-Powered</h3>
            <p className="text-gray-400 text-sm">
              Automatic API discovery and documentation with advanced AI analysis
            </p>
          </div>

          <div className="bg-gray-800/30 backdrop-blur-lg rounded-xl p-6 border border-gray-700">
            <div className="w-12 h-12 bg-blue-600/20 rounded-lg flex items-center justify-center mb-4">
              <Shield className="w-6 h-6 text-blue-400" />
            </div>
            <h3 className="text-lg font-semibold text-white mb-2">Enterprise Security</h3>
            <p className="text-gray-400 text-sm">
              SOC2 compliant with end-to-end encryption and SSO support
            </p>
          </div>

          <div className="bg-gray-800/30 backdrop-blur-lg rounded-xl p-6 border border-gray-700">
            <div className="w-12 h-12 bg-green-600/20 rounded-lg flex items-center justify-center mb-4">
              <Rocket className="w-6 h-6 text-green-400" />
            </div>
            <h3 className="text-lg font-semibold text-white mb-2">Instant Setup</h3>
            <p className="text-gray-400 text-sm">
              Get started in seconds with automatic project detection
            </p>
          </div>
        </div>
      </div>

      {/* FAQ Section */}
      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 pb-20">
        <h2 className="text-3xl font-bold text-white text-center mb-8">
          Frequently Asked Questions
        </h2>
        
        <div className="space-y-4">
          <details className="group bg-gray-800/30 backdrop-blur-lg rounded-lg border border-gray-700">
            <summary className="flex items-center justify-between p-6 cursor-pointer">
              <h3 className="text-lg font-semibold text-white">
                Can I change plans anytime?
              </h3>
              <span className="text-gray-400 group-open:rotate-180 transition-transform">
                <ChevronDown className="w-5 h-5" />
              </span>
            </summary>
            <div className="px-6 pb-6">
              <p className="text-gray-400">
                Yes! You can upgrade or downgrade your plan at any time. Changes take effect immediately and you'll be pro-rated for the billing period.
              </p>
            </div>
          </details>
          
          <details className="group bg-gray-800/30 backdrop-blur-lg rounded-lg border border-gray-700">
            <summary className="flex items-center justify-between p-6 cursor-pointer">
              <h3 className="text-lg font-semibold text-white">
                Is there a free trial?
              </h3>
              <span className="text-gray-400 group-open:rotate-180 transition-transform">
                <ChevronDown className="w-5 h-5" />
              </span>
            </summary>
            <div className="px-6 pb-6">
              <p className="text-gray-400">
                Yes, all paid plans come with a 14-day free trial. No credit card required to start your trial.
              </p>
            </div>
          </details>
          
          <details className="group bg-gray-800/30 backdrop-blur-lg rounded-lg border border-gray-700">
            <summary className="flex items-center justify-between p-6 cursor-pointer">
              <h3 className="text-lg font-semibold text-white">
                What happens if I exceed my limits?
              </h3>
              <span className="text-gray-400 group-open:rotate-180 transition-transform">
                <ChevronDown className="w-5 h-5" />
              </span>
            </summary>
            <div className="px-6 pb-6">
              <p className="text-gray-400">
                We'll notify you when you're approaching your limits. You can enable overage billing for paid plans or upgrade to a higher tier.
              </p>
            </div>
          </details>
        </div>
      </div>

      {/* CTA Section */}
      {!user && (
        <div className="border-t border-gray-800">
          <div className="max-w-4xl mx-auto text-center px-4 py-16">
            <h2 className="text-3xl font-bold text-white mb-4">
              Ready to Supercharge Your API Development?
            </h2>
            <p className="text-xl text-gray-400 mb-8">
              Join thousands of developers building better APIs with AI
            </p>
            <div className="flex justify-center gap-4">
              <Link
                to="/register"
                className="inline-flex items-center gap-2 px-8 py-3 bg-gradient-to-r from-purple-600 to-blue-600 text-white font-semibold rounded-lg hover:opacity-90 transition"
              >
                Start Free Today
                <ArrowRight className="w-5 h-5" />
              </Link>
              <Link
                to="/login"
                className="inline-flex items-center gap-2 px-8 py-3 bg-gray-800 text-gray-300 font-semibold rounded-lg hover:bg-gray-700 hover:text-white transition border border-gray-700"
              >
                Sign In
              </Link>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

// Add missing import
const ChevronDown = () => (
  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
  </svg>
);

export default PricingPage;