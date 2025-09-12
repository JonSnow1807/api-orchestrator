import React, { useState, useEffect } from 'react';
import { 
  ShieldCheckIcon,
  LockClosedIcon,
  CloudIcon,
  CpuChipIcon,
  EyeSlashIcon,
  CheckBadgeIcon,
  ExclamationTriangleIcon,
  InformationCircleIcon,
  ArrowPathIcon
} from '@heroicons/react/24/outline';

const PrivacyAI = ({ data, onProcessed, onAnonymized }) => {
  const [aiMode, setAiMode] = useState('HYBRID');
  const [dataClassification, setDataClassification] = useState('INTERNAL');
  const [complianceStatus, setComplianceStatus] = useState({});
  const [anonymizedData, setAnonymizedData] = useState(null);
  const [processing, setProcessing] = useState(false);
  const [activeTab, setActiveTab] = useState('overview');
  const [prompt, setPrompt] = useState('');
  const [result, setResult] = useState(null);

  const aiModes = {
    CLOUD: {
      name: 'Cloud AI',
      description: 'Process with cloud AI services',
      icon: <CloudIcon className="h-6 w-6" />,
      color: 'blue',
      security: 'medium'
    },
    LOCAL: {
      name: 'Local AI',
      description: 'Process locally with Ollama/Llama2',
      icon: <CpuChipIcon className="h-6 w-6" />,
      color: 'green',
      security: 'high'
    },
    HYBRID: {
      name: 'Hybrid Mode',
      description: 'Sensitive data local, public data cloud',
      icon: <ArrowPathIcon className="h-6 w-6" />,
      color: 'purple',
      security: 'high'
    },
    DISABLED: {
      name: 'AI Disabled',
      description: 'No AI processing',
      icon: <EyeSlashIcon className="h-6 w-6" />,
      color: 'gray',
      security: 'maximum'
    }
  };

  const dataClassifications = {
    PUBLIC: {
      name: 'Public',
      description: 'Non-sensitive, public information',
      color: 'green',
      icon: '🌍'
    },
    INTERNAL: {
      name: 'Internal',
      description: 'Internal use only',
      color: 'yellow',
      icon: '🏢'
    },
    CONFIDENTIAL: {
      name: 'Confidential',
      description: 'Sensitive business data',
      color: 'orange',
      icon: '🔒'
    },
    RESTRICTED: {
      name: 'Restricted',
      description: 'Highly sensitive, PII/PHI',
      color: 'red',
      icon: '🔐'
    }
  };

  const regulations = ['GDPR', 'HIPAA', 'SOC2', 'PCI_DSS'];

  useEffect(() => {
    checkCompliance();
  }, []);

  const checkCompliance = async () => {
    const status = {};
    for (const regulation of regulations) {
      try {
        const token = localStorage.getItem('token');
        const response = await fetch(`/api/v5/privacy-ai/compliance-check?regulation=${regulation}`, {
          headers: {
            'Authorization': `Bearer ${token}`
          }
        });
        
        if (response.ok) {
          const data = await response.json();
          status[regulation] = data.compliant;
        }
      } catch (error) {
        console.error(`Failed to check ${regulation} compliance:`, error);
        status[regulation] = false;
      }
    }
    setComplianceStatus(status);
  };

  const processWithPrivacyAI = async () => {
    if (!prompt || !data) return;
    
    setProcessing(true);
    try {
      const token = localStorage.getItem('token');
      const response = await fetch('/api/v5/privacy-ai/process', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({
          prompt,
          data,
          mode: aiMode,
          classification: dataClassification
        })
      });
      
      if (response.ok) {
        const result = await response.json();
        setResult(result.result);
        
        if (onProcessed) {
          onProcessed(result.result);
        }
      }
    } catch (error) {
      console.error('Failed to process with AI:', error);
    } finally {
      setProcessing(false);
    }
  };

  const anonymizeData = async () => {
    if (!data) return;
    
    setProcessing(true);
    try {
      const token = localStorage.getItem('token');
      const response = await fetch('/api/v5/privacy-ai/anonymize', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({ data })
      });
      
      if (response.ok) {
        const result = await response.json();
        setAnonymizedData(result.anonymized);
        
        if (onAnonymized) {
          onAnonymized(result.anonymized);
        }
      }
    } catch (error) {
      console.error('Failed to anonymize data:', error);
    } finally {
      setProcessing(false);
    }
  };

  const getSecurityLevel = (mode) => {
    const levels = {
      'maximum': { text: 'Maximum Security', color: 'text-green-400' },
      'high': { text: 'High Security', color: 'text-blue-400' },
      'medium': { text: 'Medium Security', color: 'text-yellow-400' },
      'low': { text: 'Low Security', color: 'text-red-400' }
    };
    return levels[aiModes[mode].security];
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="bg-gray-800 rounded-lg p-6">
        <div className="flex items-center justify-between">
          <div className="flex items-center">
            <ShieldCheckIcon className="h-8 w-8 text-green-400 mr-3" />
            <div>
              <h2 className="text-2xl font-bold text-white">Privacy-First AI</h2>
              <p className="text-gray-400 mt-1">
                Your data never trains our models • GDPR/HIPAA compliant
              </p>
            </div>
          </div>
          <div className="flex items-center space-x-2">
            <span className="text-sm text-gray-400">Security Level:</span>
            <span className={`font-medium ${getSecurityLevel(aiMode).color}`}>
              {getSecurityLevel(aiMode).text}
            </span>
          </div>
        </div>
      </div>

      {/* Tabs */}
      <div className="border-b border-gray-700">
        <nav className="flex space-x-8">
          {['overview', 'process', 'anonymize', 'compliance'].map((tab) => (
            <button
              key={tab}
              onClick={() => setActiveTab(tab)}
              className={`py-2 px-1 border-b-2 font-medium text-sm capitalize ${
                activeTab === tab
                  ? 'border-green-500 text-green-400'
                  : 'border-transparent text-gray-400 hover:text-gray-300'
              }`}
            >
              {tab}
            </button>
          ))}
        </nav>
      </div>

      {/* Overview Tab */}
      {activeTab === 'overview' && (
        <div className="space-y-6">
          {/* AI Mode Selection */}
          <div className="bg-gray-800 rounded-lg p-6">
            <h3 className="text-lg font-semibold text-white mb-4">AI Processing Mode</h3>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              {Object.entries(aiModes).map(([key, mode]) => (
                <button
                  key={key}
                  onClick={() => setAiMode(key)}
                  className={`p-4 rounded-lg border-2 transition-all ${
                    aiMode === key
                      ? `border-${mode.color}-500 bg-${mode.color}-500/10`
                      : 'border-gray-600 bg-gray-700 hover:border-gray-500'
                  }`}
                >
                  <div className={`text-${mode.color}-400 mb-2`}>
                    {mode.icon}
                  </div>
                  <div className="text-white font-medium">{mode.name}</div>
                  <div className="text-gray-400 text-xs mt-2">{mode.description}</div>
                </button>
              ))}
            </div>
          </div>

          {/* Data Classification */}
          <div className="bg-gray-800 rounded-lg p-6">
            <h3 className="text-lg font-semibold text-white mb-4">Data Classification</h3>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              {Object.entries(dataClassifications).map(([key, classification]) => (
                <button
                  key={key}
                  onClick={() => setDataClassification(key)}
                  className={`p-4 rounded-lg border-2 transition-all ${
                    dataClassification === key
                      ? `border-${classification.color}-500 bg-${classification.color}-500/10`
                      : 'border-gray-600 bg-gray-700 hover:border-gray-500'
                  }`}
                >
                  <div className="text-2xl mb-2">{classification.icon}</div>
                  <div className="text-white font-medium">{classification.name}</div>
                  <div className="text-gray-400 text-xs mt-2">{classification.description}</div>
                </button>
              ))}
            </div>
          </div>

          {/* Privacy Features */}
          <div className="bg-gray-800 rounded-lg p-6">
            <h3 className="text-lg font-semibold text-white mb-4">Privacy Features</h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="bg-gray-700 rounded-lg p-4">
                <div className="flex items-start">
                  <LockClosedIcon className="h-5 w-5 text-green-400 mt-0.5 mr-3" />
                  <div>
                    <h4 className="text-white font-medium">Data Never Trains Models</h4>
                    <p className="text-gray-400 text-sm mt-1">
                      Your data is never used to train or improve AI models
                    </p>
                  </div>
                </div>
              </div>
              
              <div className="bg-gray-700 rounded-lg p-4">
                <div className="flex items-start">
                  <EyeSlashIcon className="h-5 w-5 text-green-400 mt-0.5 mr-3" />
                  <div>
                    <h4 className="text-white font-medium">Auto-Anonymization</h4>
                    <p className="text-gray-400 text-sm mt-1">
                      Automatically removes PII before processing
                    </p>
                  </div>
                </div>
              </div>
              
              <div className="bg-gray-700 rounded-lg p-4">
                <div className="flex items-start">
                  <CpuChipIcon className="h-5 w-5 text-green-400 mt-0.5 mr-3" />
                  <div>
                    <h4 className="text-white font-medium">Local AI Option</h4>
                    <p className="text-gray-400 text-sm mt-1">
                      Process sensitive data locally with Ollama/Llama2
                    </p>
                  </div>
                </div>
              </div>
              
              <div className="bg-gray-700 rounded-lg p-4">
                <div className="flex items-start">
                  <ShieldCheckIcon className="h-5 w-5 text-green-400 mt-0.5 mr-3" />
                  <div>
                    <h4 className="text-white font-medium">Compliance Built-in</h4>
                    <p className="text-gray-400 text-sm mt-1">
                      GDPR, HIPAA, SOC2, PCI-DSS compliant by design
                    </p>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Process Tab */}
      {activeTab === 'process' && (
        <div className="bg-gray-800 rounded-lg p-6">
          <h3 className="text-lg font-semibold text-white mb-4">Process Data with Privacy AI</h3>
          
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">
                AI Prompt
              </label>
              <textarea
                value={prompt}
                onChange={(e) => setPrompt(e.target.value)}
                placeholder="Describe what you want the AI to do with your data..."
                className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-lg text-white focus:outline-none focus:border-green-500"
                rows="4"
              />
            </div>
            
            <div className="flex items-center space-x-4">
              <div className="flex items-center">
                <span className="text-sm text-gray-400 mr-2">Mode:</span>
                <span className="text-white font-medium">{aiModes[aiMode].name}</span>
              </div>
              <div className="flex items-center">
                <span className="text-sm text-gray-400 mr-2">Classification:</span>
                <span className="text-white font-medium">{dataClassifications[dataClassification].name}</span>
              </div>
            </div>
            
            <button
              onClick={processWithPrivacyAI}
              disabled={processing || !prompt}
              className="px-6 py-3 bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center"
            >
              {processing ? (
                <>
                  <ArrowPathIcon className="h-5 w-5 mr-2 animate-spin" />
                  Processing...
                </>
              ) : (
                <>
                  <ShieldCheckIcon className="h-5 w-5 mr-2" />
                  Process with Privacy AI
                </>
              )}
            </button>
            
            {result && (
              <div className="mt-6 bg-gray-700 rounded-lg p-4">
                <h4 className="text-white font-medium mb-2">AI Result</h4>
                <pre className="text-gray-300 text-sm overflow-x-auto">
                  {JSON.stringify(result, null, 2)}
                </pre>
              </div>
            )}
          </div>
          
          <div className="mt-6 bg-blue-500/10 border border-blue-500/20 rounded-lg p-4">
            <div className="flex items-start">
              <InformationCircleIcon className="h-5 w-5 text-blue-400 mt-0.5 mr-3" />
              <div className="text-sm text-blue-200">
                {aiMode === 'LOCAL' && (
                  <span>Processing locally with Ollama. No data leaves your machine.</span>
                )}
                {aiMode === 'CLOUD' && (
                  <span>Processing in the cloud. Data is encrypted and never stored.</span>
                )}
                {aiMode === 'HYBRID' && (
                  <span>Sensitive data processed locally, public data in the cloud.</span>
                )}
                {aiMode === 'DISABLED' && (
                  <span>AI processing is disabled. Only basic operations available.</span>
                )}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Anonymize Tab */}
      {activeTab === 'anonymize' && (
        <div className="bg-gray-800 rounded-lg p-6">
          <h3 className="text-lg font-semibold text-white mb-4">Data Anonymization</h3>
          
          <div className="space-y-4">
            <div className="bg-gray-700 rounded-lg p-4">
              <h4 className="text-white font-medium mb-3">Automatic Detection & Removal</h4>
              <div className="space-y-2 text-sm">
                <div className="flex items-center text-gray-300">
                  <CheckBadgeIcon className="h-4 w-4 text-green-400 mr-2" />
                  Email addresses
                </div>
                <div className="flex items-center text-gray-300">
                  <CheckBadgeIcon className="h-4 w-4 text-green-400 mr-2" />
                  Phone numbers
                </div>
                <div className="flex items-center text-gray-300">
                  <CheckBadgeIcon className="h-4 w-4 text-green-400 mr-2" />
                  Social Security Numbers
                </div>
                <div className="flex items-center text-gray-300">
                  <CheckBadgeIcon className="h-4 w-4 text-green-400 mr-2" />
                  Credit card numbers
                </div>
                <div className="flex items-center text-gray-300">
                  <CheckBadgeIcon className="h-4 w-4 text-green-400 mr-2" />
                  IP addresses
                </div>
                <div className="flex items-center text-gray-300">
                  <CheckBadgeIcon className="h-4 w-4 text-green-400 mr-2" />
                  Names and addresses
                </div>
              </div>
            </div>
            
            <button
              onClick={anonymizeData}
              disabled={processing || !data}
              className="px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center"
            >
              {processing ? (
                <>
                  <ArrowPathIcon className="h-5 w-5 mr-2 animate-spin" />
                  Anonymizing...
                </>
              ) : (
                <>
                  <EyeSlashIcon className="h-5 w-5 mr-2" />
                  Anonymize Data
                </>
              )}
            </button>
            
            {anonymizedData && (
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 mt-6">
                <div className="bg-gray-700 rounded-lg p-4">
                  <h4 className="text-white font-medium mb-2">Original Data</h4>
                  <pre className="text-gray-300 text-xs overflow-x-auto">
                    {JSON.stringify(data, null, 2)}
                  </pre>
                </div>
                <div className="bg-gray-700 rounded-lg p-4">
                  <h4 className="text-white font-medium mb-2">Anonymized Data</h4>
                  <pre className="text-gray-300 text-xs overflow-x-auto">
                    {JSON.stringify(anonymizedData, null, 2)}
                  </pre>
                </div>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Compliance Tab */}
      {activeTab === 'compliance' && (
        <div className="bg-gray-800 rounded-lg p-6">
          <h3 className="text-lg font-semibold text-white mb-4">Compliance Status</h3>
          
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {regulations.map((regulation) => (
              <div key={regulation} className="bg-gray-700 rounded-lg p-4">
                <div className="flex items-center justify-between">
                  <div className="flex items-center">
                    {complianceStatus[regulation] ? (
                      <CheckBadgeIcon className="h-6 w-6 text-green-400 mr-3" />
                    ) : (
                      <ExclamationTriangleIcon className="h-6 w-6 text-yellow-400 mr-3" />
                    )}
                    <div>
                      <h4 className="text-white font-medium">{regulation}</h4>
                      <p className="text-gray-400 text-sm">
                        {complianceStatus[regulation] ? 'Compliant' : 'Review Required'}
                      </p>
                    </div>
                  </div>
                  <button className="text-blue-400 hover:text-blue-300 text-sm">
                    View Details
                  </button>
                </div>
              </div>
            ))}
          </div>
          
          <div className="mt-6 bg-green-500/10 border border-green-500/20 rounded-lg p-4">
            <div className="flex items-start">
              <CheckBadgeIcon className="h-5 w-5 text-green-400 mt-0.5 mr-3" />
              <div>
                <h4 className="text-green-200 font-medium">Privacy by Design</h4>
                <p className="text-green-200/80 text-sm mt-1">
                  All features are built with privacy and compliance as core principles.
                  Your data protection is our top priority.
                </p>
              </div>
            </div>
          </div>
          
          <div className="mt-4 space-y-3">
            <div className="bg-gray-700 rounded-lg p-3">
              <div className="flex items-center justify-between">
                <span className="text-gray-300">Data Retention</span>
                <span className="text-white font-medium">No persistent storage</span>
              </div>
            </div>
            <div className="bg-gray-700 rounded-lg p-3">
              <div className="flex items-center justify-between">
                <span className="text-gray-300">Data Encryption</span>
                <span className="text-white font-medium">AES-256 at rest, TLS in transit</span>
              </div>
            </div>
            <div className="bg-gray-700 rounded-lg p-3">
              <div className="flex items-center justify-between">
                <span className="text-gray-300">Audit Logging</span>
                <span className="text-white font-medium">Full audit trail maintained</span>
              </div>
            </div>
            <div className="bg-gray-700 rounded-lg p-3">
              <div className="flex items-center justify-between">
                <span className="text-gray-300">User Consent</span>
                <span className="text-white font-medium">Explicit consent required</span>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default PrivacyAI;