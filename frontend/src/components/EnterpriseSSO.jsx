import React, { useState, useEffect } from 'react';
import { Shield, Users, Settings, CheckCircle, XCircle, Key, Globe, AlertTriangle } from 'lucide-react';

const EnterpriseSSO = () => {
  const [ssoProviders, setSsoProviders] = useState([]);
  const [enterpriseStatus, setEnterpriseStatus] = useState(null);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState('overview');

  useEffect(() => {
    fetchEnterpriseStatus();
    fetchSSOProviders();
  }, []);

  const fetchEnterpriseStatus = async () => {
    try {
      const response = await fetch('/api/auth/sso/status', {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        }
      });
      if (response.ok) {
        const data = await response.json();
        setEnterpriseStatus(data);
      }
    } catch (error) {
      console.error('Failed to fetch enterprise status:', error);
    }
  };

  const fetchSSOProviders = async () => {
    try {
      const response = await fetch('/api/auth/sso/providers', {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        }
      });
      if (response.ok) {
        const data = await response.json();
        setSsoProviders(data.providers);
      }
    } catch (error) {
      console.error('Failed to fetch SSO providers:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleSSOLogin = (provider) => {
    const authUrl = provider.type === 'saml'
      ? `/api/auth/sso/saml/${provider.id}/login`
      : `/api/auth/sso/oidc/${provider.id}/login`;

    window.location.href = authUrl;
  };

  const FeatureCard = ({ title, description, available, icon: Icon }) => (
    <div className={`p-4 rounded-lg border ${available ? 'border-green-200 bg-green-50' : 'border-gray-200 bg-gray-50'}`}>
      <div className="flex items-center space-x-3">
        <Icon className={`w-5 h-5 ${available ? 'text-green-600' : 'text-gray-400'}`} />
        <div className="flex-1">
          <h3 className={`font-medium ${available ? 'text-green-900' : 'text-gray-600'}`}>
            {title}
          </h3>
          <p className={`text-sm ${available ? 'text-green-700' : 'text-gray-500'}`}>
            {description}
          </p>
        </div>
        {available ? (
          <CheckCircle className="w-5 h-5 text-green-600" />
        ) : (
          <XCircle className="w-5 h-5 text-gray-400" />
        )}
      </div>
    </div>
  );

  const ProviderCard = ({ provider }) => (
    <div className="bg-white rounded-lg border border-gray-200 p-6">
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center space-x-3">
          <div className={`w-10 h-10 rounded-full flex items-center justify-center ${
            provider.type === 'saml' ? 'bg-blue-100 text-blue-600' : 'bg-purple-100 text-purple-600'
          }`}>
            {provider.type === 'saml' ? <Shield className="w-5 h-5" /> : <Key className="w-5 h-5" />}
          </div>
          <div>
            <h3 className="font-semibold text-gray-900">{provider.name}</h3>
            <p className="text-sm text-gray-500">{provider.type.toUpperCase()}</p>
          </div>
        </div>
        <div className={`px-3 py-1 rounded-full text-xs font-medium ${
          provider.enabled ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'
        }`}>
          {provider.enabled ? 'Active' : 'Inactive'}
        </div>
      </div>

      <div className="space-y-3 mb-4">
        <div className="flex items-center text-sm text-gray-600">
          <Globe className="w-4 h-4 mr-2" />
          <span>{provider.domains.length} configured domains</span>
        </div>
        <div className="flex flex-wrap gap-1">
          {provider.domains.map(domain => (
            <span key={domain} className="px-2 py-1 bg-gray-100 text-gray-700 text-xs rounded">
              @{domain}
            </span>
          ))}
        </div>
      </div>

      {provider.enabled && (
        <button
          onClick={() => handleSSOLogin(provider)}
          className="w-full bg-blue-600 hover:bg-blue-700 text-white py-2 px-4 rounded-md text-sm font-medium transition-colors"
        >
          Test SSO Login
        </button>
      )}
    </div>
  );

  if (loading) {
    return (
      <div className="max-w-6xl mx-auto p-6">
        <div className="animate-pulse space-y-6">
          <div className="h-8 bg-gray-200 rounded w-1/3"></div>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            {[1, 2, 3].map(i => (
              <div key={i} className="h-32 bg-gray-200 rounded"></div>
            ))}
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-6xl mx-auto p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Enterprise SSO</h1>
          <p className="text-gray-600 mt-1">Single Sign-On configuration and management</p>
        </div>
        {enterpriseStatus?.is_enterprise_user && (
          <div className="flex items-center space-x-2 bg-green-100 text-green-800 px-3 py-1 rounded-full">
            <Shield className="w-4 h-4" />
            <span className="text-sm font-medium">Enterprise User</span>
          </div>
        )}
      </div>

      {/* Enterprise Status Alert */}
      {!enterpriseStatus?.is_enterprise_user && (
        <div className="bg-amber-50 border border-amber-200 rounded-lg p-4">
          <div className="flex items-center space-x-3">
            <AlertTriangle className="w-5 h-5 text-amber-600" />
            <div>
              <h3 className="font-medium text-amber-900">Enterprise Features Available</h3>
              <p className="text-sm text-amber-700">
                Configure SSO to unlock enterprise features and enhanced security for your team.
              </p>
            </div>
          </div>
        </div>
      )}

      {/* Tabs */}
      <div className="border-b border-gray-200">
        <nav className="-mb-px flex space-x-8">
          {[
            { id: 'overview', name: 'Overview', icon: Shield },
            { id: 'providers', name: 'SSO Providers', icon: Key },
            { id: 'features', name: 'Enterprise Features', icon: Settings }
          ].map(tab => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`flex items-center space-x-2 py-2 px-1 border-b-2 font-medium text-sm ${
                activeTab === tab.id
                  ? 'border-blue-500 text-blue-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
            >
              <tab.icon className="w-4 h-4" />
              <span>{tab.name}</span>
            </button>
          ))}
        </nav>
      </div>

      {/* Tab Content */}
      {activeTab === 'overview' && (
        <div className="space-y-6">
          {/* Stats Cards */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <div className="bg-white p-6 rounded-lg border border-gray-200">
              <div className="flex items-center">
                <div className="p-2 bg-blue-100 rounded-lg">
                  <Shield className="w-6 h-6 text-blue-600" />
                </div>
                <div className="ml-4">
                  <p className="text-sm font-medium text-gray-600">SSO Providers</p>
                  <p className="text-2xl font-semibold text-gray-900">{ssoProviders.length}</p>
                </div>
              </div>
            </div>

            <div className="bg-white p-6 rounded-lg border border-gray-200">
              <div className="flex items-center">
                <div className="p-2 bg-green-100 rounded-lg">
                  <Users className="w-6 h-6 text-green-600" />
                </div>
                <div className="ml-4">
                  <p className="text-sm font-medium text-gray-600">Enterprise Users</p>
                  <p className="text-2xl font-semibold text-gray-900">
                    {enterpriseStatus?.is_enterprise_user ? '1+' : '0'}
                  </p>
                </div>
              </div>
            </div>

            <div className="bg-white p-6 rounded-lg border border-gray-200">
              <div className="flex items-center">
                <div className="p-2 bg-purple-100 rounded-lg">
                  <Settings className="w-6 h-6 text-purple-600" />
                </div>
                <div className="ml-4">
                  <p className="text-sm font-medium text-gray-600">Security Level</p>
                  <p className="text-2xl font-semibold text-gray-900">
                    {enterpriseStatus?.is_enterprise_user ? 'High' : 'Standard'}
                  </p>
                </div>
              </div>
            </div>
          </div>

          {/* Configuration Guide */}
          <div className="bg-white rounded-lg border border-gray-200 p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">SSO Configuration Guide</h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div>
                <h4 className="font-medium text-gray-900 mb-2">SAML 2.0 Setup</h4>
                <ol className="text-sm text-gray-600 space-y-2 list-decimal list-inside">
                  <li>Configure your Identity Provider (IdP)</li>
                  <li>Add environment variables for SAML settings</li>
                  <li>Test the authentication flow</li>
                  <li>Enable for your domain</li>
                </ol>
              </div>
              <div>
                <h4 className="font-medium text-gray-900 mb-2">OIDC/OAuth2 Setup</h4>
                <ol className="text-sm text-gray-600 space-y-2 list-decimal list-inside">
                  <li>Register OAuth application with your provider</li>
                  <li>Configure client ID and secret</li>
                  <li>Set up redirect URIs</li>
                  <li>Test and activate</li>
                </ol>
              </div>
            </div>
          </div>
        </div>
      )}

      {activeTab === 'providers' && (
        <div className="space-y-6">
          {ssoProviders.length === 0 ? (
            <div className="text-center py-12">
              <Shield className="w-12 h-12 text-gray-400 mx-auto mb-4" />
              <h3 className="text-lg font-medium text-gray-900 mb-2">No SSO Providers Configured</h3>
              <p className="text-gray-600 mb-4">
                Configure SAML or OIDC providers to enable enterprise authentication.
              </p>
              <div className="bg-gray-50 rounded-lg p-4 max-w-2xl mx-auto text-left">
                <h4 className="font-medium text-gray-900 mb-2">Environment Variables Example:</h4>
                <pre className="text-xs text-gray-700 overflow-x-auto">
{`# SAML Configuration
SAML_PROVIDERS='{"company-saml": {
  "name": "Company SAML",
  "domains": ["company.com"],
  "sp_entity_id": "api-orchestrator",
  "sp_acs_url": "https://your-domain.com/api/auth/sso/saml/company-saml/acs",
  "idp_entity_id": "https://company.okta.com",
  "idp_sso_url": "https://company.okta.com/app/saml/login",
  "idp_cert": "-----BEGIN CERTIFICATE-----..."
}}'

# OIDC Configuration
OIDC_PROVIDERS='{"company-oidc": {
  "name": "Company OIDC",
  "domains": ["company.com"],
  "client_id": "your-client-id",
  "client_secret": "your-client-secret",
  "discovery_url": "https://company.auth0.com/.well-known/openid-configuration"
}}'`}
                </pre>
              </div>
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {ssoProviders.map(provider => (
                <ProviderCard key={provider.id} provider={provider} />
              ))}
            </div>
          )}
        </div>
      )}

      {activeTab === 'features' && enterpriseStatus && (
        <div className="space-y-6">
          <div className="bg-white rounded-lg border border-gray-200 p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">Enterprise Features</h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <FeatureCard
                title="Single Sign-On"
                description="SAML 2.0 and OIDC authentication"
                available={enterpriseStatus.features.sso_enabled}
                icon={Shield}
              />
              <FeatureCard
                title="Advanced Features"
                description="AI analysis, advanced testing, monitoring"
                available={enterpriseStatus.features.advanced_features}
                icon={Settings}
              />
              <FeatureCard
                title="Team Collaboration"
                description="Multi-user workspaces and sharing"
                available={enterpriseStatus.features.team_features}
                icon={Users}
              />
              <FeatureCard
                title="Unlimited APIs"
                description="No limits on API projects and calls"
                available={enterpriseStatus.features.unlimited_apis}
                icon={Globe}
              />
            </div>
          </div>

          {enterpriseStatus.is_enterprise_user && (
            <div className="bg-green-50 border border-green-200 rounded-lg p-6">
              <div className="flex items-center space-x-3 mb-4">
                <CheckCircle className="w-6 h-6 text-green-600" />
                <h3 className="text-lg font-semibold text-green-900">Enterprise Features Active</h3>
              </div>
              <p className="text-green-800 mb-4">
                You're authenticated via <strong>{enterpriseStatus.sso_provider}</strong> and have access to all enterprise features.
              </p>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                <div className="text-center">
                  <div className="font-semibold text-green-900">Unlimited</div>
                  <div className="text-green-700">API Calls</div>
                </div>
                <div className="text-center">
                  <div className="font-semibold text-green-900">Advanced</div>
                  <div className="text-green-700">AI Analysis</div>
                </div>
                <div className="text-center">
                  <div className="font-semibold text-green-900">Team</div>
                  <div className="text-green-700">Collaboration</div>
                </div>
                <div className="text-center">
                  <div className="font-semibold text-green-900">Priority</div>
                  <div className="text-green-700">Support</div>
                </div>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default EnterpriseSSO;