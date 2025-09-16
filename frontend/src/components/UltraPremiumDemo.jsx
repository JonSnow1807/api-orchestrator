import React, { useState } from 'react';
import {
  Bot,
  Zap,
  Shield,
  CheckCircle,
  AlertTriangle,
  Clock,
  Brain,
  Settings,
  Play,
  Pause
} from 'lucide-react';

const UltraPremiumDemo = () => {
  const [isSimulating, setIsSimulating] = useState(false);
  const [simulationStep, setSimulationStep] = useState(0);
  const [analysisResults, setAnalysisResults] = useState(null);

  const simulateAutonomousAgent = async () => {
    setIsSimulating(true);
    setSimulationStep(0);

    const steps = [
      { text: "🤖 AI Agent analyzing endpoint...", delay: 1000 },
      { text: "🔍 LLM creating security analysis plan...", delay: 1500 },
      { text: "⚡ Executing vulnerability scan...", delay: 2000 },
      { text: "🛡️ Auto-fixing security headers...", delay: 1000 },
      { text: "✅ Analysis complete!", delay: 500 }
    ];

    for (let i = 0; i < steps.length; i++) {
      setTimeout(() => {
        setSimulationStep(i + 1);
        if (i === steps.length - 1) {
          setAnalysisResults({
            vulnerabilities_found: 3,
            vulnerabilities_fixed: 2,
            execution_time: 4.2,
            confidence_score: 0.89,
            actions_taken: [
              "Added X-Content-Type-Options header",
              "Implemented X-Frame-Options protection",
              "Fixed authentication validation"
            ]
          });
          setIsSimulating(false);
        }
      }, steps.slice(0, i + 1).reduce((acc, step) => acc + step.delay, 0));
    }
  };

  const resetDemo = () => {
    setSimulationStep(0);
    setAnalysisResults(null);
    setIsSimulating(false);
  };

  return (
    <div className="max-w-6xl mx-auto p-6 bg-gray-900 text-white">
      {/* Header */}
      <div className="text-center mb-8">
        <div className="inline-flex items-center gap-2 px-4 py-2 bg-blue-600/20 border border-blue-500/30 rounded-full text-blue-400 text-sm mb-4">
          <Bot className="w-4 h-4" />
          <span>Ultra Premium - AI Workforce</span>
        </div>

        <h1 className="text-4xl font-bold text-transparent bg-clip-text bg-gradient-to-r from-blue-400 to-purple-400 mb-4">
          Autonomous AI Agents
        </h1>
        <p className="text-xl text-gray-400 max-w-3xl mx-auto">
          Watch our AI agents automatically analyze, decide, and fix security issues in real-time.
          No human intervention required.
        </p>
      </div>

      {/* Demo Interface */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 mb-8">
        {/* Control Panel */}
        <div className="bg-gray-800/50 border border-gray-700 rounded-xl p-6">
          <h3 className="text-xl font-bold mb-4 flex items-center gap-2">
            <Settings className="w-5 h-5 text-blue-400" />
            AI Agent Control Panel
          </h3>

          <div className="space-y-4">
            <div className="flex items-center justify-between p-3 bg-gray-700/50 rounded-lg">
              <span>Autonomous Security Agent</span>
              <div className="flex items-center gap-2">
                <div className="w-2 h-2 bg-green-400 rounded-full"></div>
                <span className="text-green-400 text-sm">Online</span>
              </div>
            </div>

            <div className="p-3 bg-gray-700/30 rounded-lg">
              <div className="text-sm text-gray-400 mb-2">Target Endpoint:</div>
              <div className="font-mono text-sm">POST /api/auth/login</div>
            </div>

            <div className="flex gap-3">
              <button
                onClick={simulateAutonomousAgent}
                disabled={isSimulating}
                className="flex-1 flex items-center justify-center gap-2 px-4 py-3 bg-gradient-to-r from-blue-600 to-purple-600 text-white rounded-lg hover:opacity-90 transition disabled:opacity-50"
              >
                {isSimulating ? (
                  <>
                    <Pause className="w-4 h-4" />
                    Analyzing...
                  </>
                ) : (
                  <>
                    <Play className="w-4 h-4" />
                    Start AI Analysis
                  </>
                )}
              </button>

              <button
                onClick={resetDemo}
                className="px-4 py-3 bg-gray-700 hover:bg-gray-600 rounded-lg transition"
              >
                Reset
              </button>
            </div>
          </div>
        </div>

        {/* Live Activity Feed */}
        <div className="bg-gray-800/50 border border-gray-700 rounded-xl p-6">
          <h3 className="text-xl font-bold mb-4 flex items-center gap-2">
            <Brain className="w-5 h-5 text-purple-400" />
            AI Decision Making
          </h3>

          <div className="space-y-3 h-64 overflow-y-auto">
            {simulationStep >= 1 && (
              <div className="flex items-start gap-3 p-3 bg-blue-900/20 border border-blue-500/30 rounded-lg">
                <Bot className="w-5 h-5 text-blue-400 mt-0.5" />
                <div className="flex-1">
                  <div className="text-sm text-blue-400">LLM Decision Engine</div>
                  <div className="text-sm">"I've identified a login endpoint. I'll scan for authentication vulnerabilities and check security headers."</div>
                </div>
              </div>
            )}

            {simulationStep >= 2 && (
              <div className="flex items-start gap-3 p-3 bg-yellow-900/20 border border-yellow-500/30 rounded-lg">
                <AlertTriangle className="w-5 h-5 text-yellow-400 mt-0.5" />
                <div className="flex-1">
                  <div className="text-sm text-yellow-400">Security Analysis</div>
                  <div className="text-sm">"Found 3 security issues: Missing security headers, weak authentication validation, no rate limiting."</div>
                </div>
              </div>
            )}

            {simulationStep >= 3 && (
              <div className="flex items-start gap-3 p-3 bg-purple-900/20 border border-purple-500/30 rounded-lg">
                <Zap className="w-5 h-5 text-purple-400 mt-0.5" />
                <div className="flex-1">
                  <div className="text-sm text-purple-400">Autonomous Decision</div>
                  <div className="text-sm">"Risk assessment: LOW for header fixes, MEDIUM for auth changes. Auto-executing safe fixes, requesting approval for auth changes."</div>
                </div>
              </div>
            )}

            {simulationStep >= 4 && (
              <div className="flex items-start gap-3 p-3 bg-green-900/20 border border-green-500/30 rounded-lg">
                <CheckCircle className="w-5 h-5 text-green-400 mt-0.5" />
                <div className="flex-1">
                  <div className="text-sm text-green-400">Auto-Execution</div>
                  <div className="text-sm">"Applied security headers automatically. Authentication fix queued for approval."</div>
                </div>
              </div>
            )}

            {!isSimulating && simulationStep === 0 && (
              <div className="flex items-center justify-center h-full text-gray-500">
                Click "Start AI Analysis" to see autonomous agents in action
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Results Panel */}
      {analysisResults && (
        <div className="bg-gradient-to-r from-green-900/20 to-blue-900/20 border border-green-500/30 rounded-xl p-6 mb-8">
          <h3 className="text-xl font-bold mb-4 flex items-center gap-2">
            <CheckCircle className="w-5 h-5 text-green-400" />
            Autonomous Analysis Complete
          </h3>

          <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
            <div className="text-center">
              <div className="text-2xl font-bold text-red-400">{analysisResults.vulnerabilities_found}</div>
              <div className="text-sm text-gray-400">Issues Found</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-green-400">{analysisResults.vulnerabilities_fixed}</div>
              <div className="text-sm text-gray-400">Auto-Fixed</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-blue-400">{analysisResults.execution_time}s</div>
              <div className="text-sm text-gray-400">Execution Time</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-purple-400">{Math.round(analysisResults.confidence_score * 100)}%</div>
              <div className="text-sm text-gray-400">AI Confidence</div>
            </div>
          </div>

          <div>
            <h4 className="font-bold mb-2">Actions Taken Automatically:</h4>
            <ul className="space-y-1">
              {analysisResults.actions_taken.map((action, index) => (
                <li key={index} className="flex items-center gap-2 text-sm">
                  <CheckCircle className="w-4 h-4 text-green-400" />
                  {action}
                </li>
              ))}
            </ul>
          </div>
        </div>
      )}

      {/* Feature Comparison */}
      <div className="bg-gray-800/50 border border-gray-700 rounded-xl p-6">
        <h3 className="text-xl font-bold mb-6 text-center">Ultra Premium vs Traditional API Testing</h3>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div>
            <h4 className="font-bold text-red-400 mb-3">❌ Traditional Tools (Postman, etc.)</h4>
            <ul className="space-y-2 text-sm">
              <li className="flex items-start gap-2">
                <Clock className="w-4 h-4 text-red-400 mt-0.5" />
                Manual analysis and fixes (hours of work)
              </li>
              <li className="flex items-start gap-2">
                <AlertTriangle className="w-4 h-4 text-red-400 mt-0.5" />
                Human expertise required for security
              </li>
              <li className="flex items-start gap-2">
                <Settings className="w-4 h-4 text-red-400 mt-0.5" />
                No automated decision making
              </li>
            </ul>
          </div>

          <div>
            <h4 className="font-bold text-green-400 mb-3">✅ Ultra Premium AI Workforce</h4>
            <ul className="space-y-2 text-sm">
              <li className="flex items-start gap-2">
                <Zap className="w-4 h-4 text-green-400 mt-0.5" />
                Autonomous analysis and fixes (seconds)
              </li>
              <li className="flex items-start gap-2">
                <Shield className="w-4 h-4 text-green-400 mt-0.5" />
                Expert-level AI security analysis
              </li>
              <li className="flex items-start gap-2">
                <Brain className="w-4 h-4 text-green-400 mt-0.5" />
                Intelligent decision making with LLM
              </li>
            </ul>
          </div>
        </div>
      </div>

      {/* CTA */}
      <div className="text-center mt-8">
        <p className="text-gray-400 mb-4">
          Ready to let AI handle your API security and optimization?
        </p>
        <button className="px-8 py-3 bg-gradient-to-r from-blue-600 to-purple-600 text-white rounded-lg hover:opacity-90 transition">
          Upgrade to Ultra Premium - $299/month
        </button>
        <p className="text-sm text-gray-500 mt-2">
          30-day free trial • Cancel anytime • Full refund guarantee
        </p>
      </div>
    </div>
  );
};

export default UltraPremiumDemo;