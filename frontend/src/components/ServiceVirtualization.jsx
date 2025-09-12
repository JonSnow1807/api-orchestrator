import React, { useState, useEffect } from 'react';
import { 
  ServerIcon,
  PlayIcon,
  StopIcon,
  CogIcon,
  BeakerIcon,
  ArrowPathIcon,
  DocumentDuplicateIcon,
  ExclamationTriangleIcon,
  SignalIcon,
  CircleStackIcon
} from '@heroicons/react/24/outline';

const ServiceVirtualization = ({ openApiSpec, projectId, onServiceCreated }) => {
  const [services, setServices] = useState([]);
  const [selectedService, setSelectedService] = useState(null);
  const [behavior, setBehavior] = useState('STATIC');
  const [activeTab, setActiveTab] = useState('services');
  const [mockEndpoints, setMockEndpoints] = useState([]);
  const [recording, setRecording] = useState(false);
  const [chaosConfig, setChaosConfig] = useState({
    failureRate: 0.1,
    latencyMin: 0,
    latencyMax: 5000,
    errorCodes: [500, 502, 503]
  });

  const mockBehaviors = {
    STATIC: {
      name: 'Static',
      description: 'Fixed responses for each endpoint',
      icon: '📌',
      color: 'blue'
    },
    DYNAMIC: {
      name: 'Dynamic',
      description: 'Template-based responses with variables',
      icon: '🎲',
      color: 'green'
    },
    STATEFUL: {
      name: 'Stateful',
      description: 'CRUD operations with persistent state',
      icon: '💾',
      color: 'purple'
    },
    CONDITIONAL: {
      name: 'Conditional',
      description: 'Rule-based responses',
      icon: '🔀',
      color: 'yellow'
    },
    PROXY: {
      name: 'Proxy',
      description: 'Forward to real API',
      icon: '🔄',
      color: 'cyan'
    },
    CHAOS: {
      name: 'Chaos',
      description: 'Random failures for testing',
      icon: '🌪️',
      color: 'red'
    },
    RECORD: {
      name: 'Record',
      description: 'Capture real responses',
      icon: '⏺️',
      color: 'orange'
    },
    REPLAY: {
      name: 'Replay',
      description: 'Playback recorded responses',
      icon: '▶️',
      color: 'indigo'
    }
  };

  useEffect(() => {
    fetchServices();
  }, [projectId]);

  const fetchServices = async () => {
    try {
      const token = localStorage.getItem('token');
      const response = await fetch('/api/v5/virtualization/services', {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });
      
      if (response.ok) {
        const data = await response.json();
        setServices(data.services || []);
      }
    } catch (error) {
      console.error('Failed to fetch services:', error);
    }
  };

  const createVirtualService = async () => {
    try {
      const token = localStorage.getItem('token');
      const response = await fetch('/api/v5/virtualization/create-service', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({
          name: `Mock Service ${services.length + 1}`,
          openapi_spec: openApiSpec,
          behavior: behavior
        })
      });
      
      if (response.ok) {
        const data = await response.json();
        setServices([...services, data.service]);
        setSelectedService(data.service);
        
        if (onServiceCreated) {
          onServiceCreated(data.service);
        }
      }
    } catch (error) {
      console.error('Failed to create service:', error);
    }
  };

  const setBehaviorForService = async (serviceId, newBehavior) => {
    try {
      const token = localStorage.getItem('token');
      const response = await fetch('/api/v5/virtualization/set-behavior', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({
          service_id: serviceId,
          behavior: newBehavior,
          options: newBehavior === 'CHAOS' ? chaosConfig : {}
        })
      });
      
      if (response.ok) {
        setBehavior(newBehavior);
        // Update service in list
        setServices(services.map(s => 
          s.id === serviceId ? { ...s, behavior: newBehavior } : s
        ));
      }
    } catch (error) {
      console.error('Failed to set behavior:', error);
    }
  };

  const startRecording = async () => {
    if (!selectedService) return;
    
    try {
      const token = localStorage.getItem('token');
      const targetUrl = prompt('Enter the target API URL to record from:');
      
      if (!targetUrl) return;
      
      const response = await fetch('/api/v5/virtualization/record', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({
          service_id: selectedService.id,
          target_url: targetUrl
        })
      });
      
      if (response.ok) {
        setRecording(true);
      }
    } catch (error) {
      console.error('Failed to start recording:', error);
    }
  };

  const configureChaos = async () => {
    if (!selectedService) return;
    
    try {
      const token = localStorage.getItem('token');
      const response = await fetch('/api/v5/virtualization/chaos', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({
          service_id: selectedService.id,
          ...chaosConfig
        })
      });
      
      if (response.ok) {
        alert('Chaos configuration applied!');
      }
    } catch (error) {
      console.error('Failed to configure chaos:', error);
    }
  };

  const addMockEndpoint = async (method, path, response) => {
    if (!selectedService) return;
    
    try {
      const token = localStorage.getItem('token');
      const res = await fetch('/api/v5/virtualization/add-mock', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({
          service_id: selectedService.id,
          method,
          path,
          response,
          status_code: 200
        })
      });
      
      if (res.ok) {
        const data = await res.json();
        setMockEndpoints([...mockEndpoints, data.endpoint]);
      }
    } catch (error) {
      console.error('Failed to add mock endpoint:', error);
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="bg-gray-800 rounded-lg p-6">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-2xl font-bold text-white flex items-center">
              <ServerIcon className="h-8 w-8 mr-3 text-blue-400" />
              Service Virtualization
            </h2>
            <p className="text-gray-400 mt-1">
              Mock entire API services with advanced behaviors
            </p>
          </div>
          <button
            onClick={createVirtualService}
            className="px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 flex items-center"
          >
            <ServerIcon className="h-5 w-5 mr-2" />
            Create Virtual Service
          </button>
        </div>
      </div>

      {/* Tabs */}
      <div className="border-b border-gray-700">
        <nav className="flex space-x-8">
          {['services', 'behaviors', 'chaos', 'recordings'].map((tab) => (
            <button
              key={tab}
              onClick={() => setActiveTab(tab)}
              className={`py-2 px-1 border-b-2 font-medium text-sm capitalize ${
                activeTab === tab
                  ? 'border-blue-500 text-blue-400'
                  : 'border-transparent text-gray-400 hover:text-gray-300'
              }`}
            >
              {tab}
            </button>
          ))}
        </nav>
      </div>

      {/* Services Tab */}
      {activeTab === 'services' && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Service List */}
          <div className="bg-gray-800 rounded-lg p-6">
            <h3 className="text-lg font-semibold text-white mb-4">Virtual Services</h3>
            <div className="space-y-3">
              {services.length > 0 ? (
                services.map((service) => (
                  <div
                    key={service.id}
                    onClick={() => setSelectedService(service)}
                    className={`bg-gray-700 rounded-lg p-4 cursor-pointer transition-all ${
                      selectedService?.id === service.id
                        ? 'ring-2 ring-blue-500'
                        : 'hover:bg-gray-600'
                    }`}
                  >
                    <div className="flex items-center justify-between">
                      <div className="flex items-center">
                        <div className="w-10 h-10 bg-blue-500/20 rounded-lg flex items-center justify-center mr-3">
                          <ServerIcon className="h-6 w-6 text-blue-400" />
                        </div>
                        <div>
                          <h4 className="text-white font-medium">{service.name}</h4>
                          <div className="flex items-center space-x-2 mt-1">
                            <span className="text-2xl">
                              {mockBehaviors[service.behavior]?.icon}
                            </span>
                            <span className="text-gray-400 text-sm">
                              {mockBehaviors[service.behavior]?.name}
                            </span>
                          </div>
                        </div>
                      </div>
                      <div className="flex items-center space-x-2">
                        {service.status === 'running' ? (
                          <button className="p-2 bg-red-600 text-white rounded hover:bg-red-700">
                            <StopIcon className="h-4 w-4" />
                          </button>
                        ) : (
                          <button className="p-2 bg-green-600 text-white rounded hover:bg-green-700">
                            <PlayIcon className="h-4 w-4" />
                          </button>
                        )}
                      </div>
                    </div>
                    {service.endpoints && (
                      <div className="mt-3 pt-3 border-t border-gray-600">
                        <span className="text-gray-400 text-sm">
                          {service.endpoints.length} endpoints
                        </span>
                      </div>
                    )}
                  </div>
                ))
              ) : (
                <div className="text-center py-12">
                  <ServerIcon className="h-12 w-12 text-gray-600 mx-auto mb-3" />
                  <p className="text-gray-400">No virtual services yet</p>
                  <p className="text-gray-500 text-sm mt-1">
                    Create a service to start mocking APIs
                  </p>
                </div>
              )}
            </div>
          </div>

          {/* Service Details */}
          {selectedService && (
            <div className="bg-gray-800 rounded-lg p-6">
              <h3 className="text-lg font-semibold text-white mb-4">Service Details</h3>
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-300 mb-2">
                    Service URL
                  </label>
                  <div className="bg-gray-700 rounded-lg p-3">
                    <code className="text-green-400">
                      http://localhost:8000/mock/{selectedService.id}
                    </code>
                  </div>
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-300 mb-2">
                    Endpoints
                  </label>
                  <div className="bg-gray-700 rounded-lg p-3 max-h-64 overflow-y-auto">
                    {mockEndpoints.length > 0 ? (
                      <div className="space-y-2">
                        {mockEndpoints.map((endpoint, index) => (
                          <div key={index} className="flex items-center justify-between py-1">
                            <span className="text-gray-300">
                              <span className={`font-mono text-xs px-2 py-1 rounded mr-2 ${
                                endpoint.method === 'GET' ? 'bg-green-500/20 text-green-400' :
                                endpoint.method === 'POST' ? 'bg-blue-500/20 text-blue-400' :
                                endpoint.method === 'PUT' ? 'bg-yellow-500/20 text-yellow-400' :
                                endpoint.method === 'DELETE' ? 'bg-red-500/20 text-red-400' :
                                'bg-gray-500/20 text-gray-400'
                              }`}>
                                {endpoint.method}
                              </span>
                              {endpoint.path}
                            </span>
                            <span className="text-gray-500 text-sm">
                              {endpoint.status_code}
                            </span>
                          </div>
                        ))}
                      </div>
                    ) : (
                      <p className="text-gray-500 text-sm">No endpoints configured</p>
                    )}
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>
      )}

      {/* Behaviors Tab */}
      {activeTab === 'behaviors' && (
        <div className="bg-gray-800 rounded-lg p-6">
          <h3 className="text-lg font-semibold text-white mb-4">Mock Behaviors</h3>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            {Object.entries(mockBehaviors).map(([key, config]) => (
              <button
                key={key}
                onClick={() => selectedService && setBehaviorForService(selectedService.id, key)}
                className={`p-4 rounded-lg border-2 transition-all ${
                  behavior === key
                    ? `border-${config.color}-500 bg-${config.color}-500/10`
                    : 'border-gray-600 bg-gray-700 hover:border-gray-500'
                }`}
              >
                <div className="text-3xl mb-2">{config.icon}</div>
                <div className="text-white font-medium">{config.name}</div>
                <div className="text-gray-400 text-xs mt-2">{config.description}</div>
              </button>
            ))}
          </div>

          {/* Behavior-specific configuration */}
          {behavior === 'RECORD' && (
            <div className="mt-6 bg-gray-700 rounded-lg p-4">
              <h4 className="text-white font-medium mb-3">Recording Configuration</h4>
              <button
                onClick={startRecording}
                disabled={recording}
                className="px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 disabled:opacity-50 flex items-center"
              >
                {recording ? (
                  <>
                    <div className="w-2 h-2 bg-white rounded-full mr-2 animate-pulse"></div>
                    Recording...
                  </>
                ) : (
                  <>
                    <CircleStackIcon className="h-4 w-4 mr-2" />
                    Start Recording
                  </>
                )}
              </button>
            </div>
          )}

          {behavior === 'STATEFUL' && (
            <div className="mt-6 bg-gray-700 rounded-lg p-4">
              <h4 className="text-white font-medium mb-3">Stateful Configuration</h4>
              <p className="text-gray-400 text-sm">
                This service will maintain state across requests, supporting full CRUD operations.
              </p>
              <div className="mt-3 space-y-2">
                <div className="flex items-center text-green-400">
                  <CheckCircleIcon className="h-4 w-4 mr-2" />
                  <span className="text-sm">POST creates new resources</span>
                </div>
                <div className="flex items-center text-green-400">
                  <CheckCircleIcon className="h-4 w-4 mr-2" />
                  <span className="text-sm">GET retrieves existing resources</span>
                </div>
                <div className="flex items-center text-green-400">
                  <CheckCircleIcon className="h-4 w-4 mr-2" />
                  <span className="text-sm">PUT/PATCH updates resources</span>
                </div>
                <div className="flex items-center text-green-400">
                  <CheckCircleIcon className="h-4 w-4 mr-2" />
                  <span className="text-sm">DELETE removes resources</span>
                </div>
              </div>
            </div>
          )}
        </div>
      )}

      {/* Chaos Tab */}
      {activeTab === 'chaos' && (
        <div className="bg-gray-800 rounded-lg p-6">
          <div className="flex items-center mb-6">
            <ExclamationTriangleIcon className="h-8 w-8 text-red-400 mr-3" />
            <div>
              <h3 className="text-lg font-semibold text-white">Chaos Engineering</h3>
              <p className="text-gray-400 text-sm">Test your application's resilience to failures</p>
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">
                Failure Rate
              </label>
              <input
                type="range"
                min="0"
                max="100"
                value={chaosConfig.failureRate * 100}
                onChange={(e) => setChaosConfig({
                  ...chaosConfig,
                  failureRate: e.target.value / 100
                })}
                className="w-full"
              />
              <span className="text-gray-400 text-sm">
                {Math.round(chaosConfig.failureRate * 100)}% of requests will fail
              </span>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">
                Latency Range (ms)
              </label>
              <div className="flex space-x-3">
                <input
                  type="number"
                  value={chaosConfig.latencyMin}
                  onChange={(e) => setChaosConfig({
                    ...chaosConfig,
                    latencyMin: parseInt(e.target.value)
                  })}
                  className="flex-1 px-3 py-2 bg-gray-700 border border-gray-600 rounded-lg text-white"
                  placeholder="Min"
                />
                <input
                  type="number"
                  value={chaosConfig.latencyMax}
                  onChange={(e) => setChaosConfig({
                    ...chaosConfig,
                    latencyMax: parseInt(e.target.value)
                  })}
                  className="flex-1 px-3 py-2 bg-gray-700 border border-gray-600 rounded-lg text-white"
                  placeholder="Max"
                />
              </div>
            </div>

            <div className="md:col-span-2">
              <label className="block text-sm font-medium text-gray-300 mb-2">
                Error Codes
              </label>
              <div className="flex flex-wrap gap-2">
                {[400, 401, 403, 404, 429, 500, 502, 503, 504].map((code) => (
                  <button
                    key={code}
                    onClick={() => {
                      const codes = chaosConfig.errorCodes.includes(code)
                        ? chaosConfig.errorCodes.filter(c => c !== code)
                        : [...chaosConfig.errorCodes, code];
                      setChaosConfig({ ...chaosConfig, errorCodes: codes });
                    }}
                    className={`px-3 py-1 rounded-lg ${
                      chaosConfig.errorCodes.includes(code)
                        ? 'bg-red-600 text-white'
                        : 'bg-gray-700 text-gray-300 hover:bg-gray-600'
                    }`}
                  >
                    {code}
                  </button>
                ))}
              </div>
            </div>

            <div className="md:col-span-2">
              <button
                onClick={configureChaos}
                className="px-6 py-3 bg-red-600 text-white rounded-lg hover:bg-red-700 flex items-center"
              >
                <ExclamationTriangleIcon className="h-5 w-5 mr-2" />
                Apply Chaos Configuration
              </button>
            </div>
          </div>

          <div className="mt-6 bg-yellow-500/10 border border-yellow-500/20 rounded-lg p-4">
            <div className="flex items-start">
              <ExclamationTriangleIcon className="h-5 w-5 text-yellow-400 mt-0.5 mr-3" />
              <div className="text-sm text-yellow-200">
                <strong>Warning:</strong> Chaos mode will intentionally cause failures in your mock service.
                This is useful for testing error handling and resilience, but should not be used in production.
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Recordings Tab */}
      {activeTab === 'recordings' && (
        <div className="bg-gray-800 rounded-lg p-6">
          <h3 className="text-lg font-semibold text-white mb-4">Recorded Sessions</h3>
          <div className="text-center py-12">
            <DocumentDuplicateIcon className="h-12 w-12 text-gray-600 mx-auto mb-3" />
            <p className="text-gray-400">No recordings yet</p>
            <p className="text-gray-500 text-sm mt-1">
              Use Record behavior to capture real API responses
            </p>
          </div>
        </div>
      )}
    </div>
  );
};

export default ServiceVirtualization;