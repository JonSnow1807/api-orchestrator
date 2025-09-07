import React from 'react';
import { useNavigate } from 'react-router-dom';
import { 
  Zap, 
  Code2, 
  Shield, 
  Cpu, 
  Globe, 
  BarChart3,
  ArrowRight,
  CheckCircle,
  Sparkles,
  Rocket,
  FileCode,
  TestTube,
  Server,
  Brain,
  Users,
  Lock,
  Github,
  Cloud,
  Database,
  Activity
} from 'lucide-react';

const LandingPage = () => {
  const navigate = useNavigate();

  const features = [
    {
      icon: <Brain className="w-6 h-6" />,
      title: "AI-Powered Discovery",
      description: "Automatically discover and analyze APIs from code, URLs, or documentation using advanced AI"
    },
    {
      icon: <FileCode className="w-6 h-6" />,
      title: "OpenAPI Generation",
      description: "Generate comprehensive OpenAPI specifications automatically from discovered endpoints"
    },
    {
      icon: <TestTube className="w-6 h-6" />,
      title: "Automated Testing",
      description: "Create and execute test suites automatically with intelligent test case generation"
    },
    {
      icon: <Shield className="w-6 h-6" />,
      title: "Security Analysis",
      description: "AI-powered security vulnerability detection and compliance checking (GDPR, HIPAA, SOC2)"
    },
    {
      icon: <Server className="w-6 h-6" />,
      title: "Mock Servers",
      description: "Instantly generate mock servers from OpenAPI specs for rapid prototyping"
    },
    {
      icon: <Activity className="w-6 h-6" />,
      title: "Real-time Monitoring",
      description: "WebSocket-powered live updates for orchestration progress and API health"
    }
  ];

  const techStack = [
    { name: "FastAPI", category: "Backend" },
    { name: "React", category: "Frontend" },
    { name: "PostgreSQL", category: "Database" },
    { name: "Claude AI", category: "AI Engine" },
    { name: "Docker", category: "Container" },
    { name: "Railway", category: "Deployment" }
  ];

  const stats = [
    { value: "100+", label: "APIs Analyzed" },
    { value: "5 sec", label: "Avg Discovery Time" },
    { value: "99.9%", label: "Uptime" },
    { value: "Enterprise", label: "Ready" }
  ];

  return (
    <Layout>
      <div className="min-h-screen bg-gradient-to-b from-gray-900 via-purple-900/20 to-gray-900 text-white">
        {/* Hero Section */}
        <section className="pt-20 pb-20 px-6">
        <div className="max-w-7xl mx-auto text-center">
          <div className="inline-flex items-center px-4 py-2 bg-purple-500/20 rounded-full mb-6">
            <Sparkles className="w-4 h-4 text-purple-400 mr-2" />
            <span className="text-purple-400 text-sm font-medium">AI-Powered API Management Platform</span>
          </div>
          
          <h1 className="text-5xl md:text-7xl font-bold mb-6 bg-gradient-to-r from-white to-purple-400 bg-clip-text text-transparent">
            Orchestrate Your APIs
            <br />
            <span className="text-4xl md:text-6xl">With AI Intelligence</span>
          </h1>
          
          <p className="text-xl text-gray-300 mb-8 max-w-3xl mx-auto">
            Discover, document, test, and analyze APIs automatically using advanced AI. 
            Transform your API development workflow with our multi-agent orchestration system.
          </p>

          <div className="flex items-center justify-center space-x-4 mb-12">
            <button
              onClick={() => navigate('/register')}
              className="px-8 py-4 bg-purple-600 text-white rounded-lg hover:bg-purple-700 transition transform hover:scale-105 flex items-center space-x-2"
            >
              <Rocket className="w-5 h-5" />
              <span>Start Free Trial</span>
            </button>
            <button
              onClick={() => navigate('/login')}
              className="px-8 py-4 bg-gray-800 text-white rounded-lg hover:bg-gray-700 transition flex items-center space-x-2"
            >
              <span>View Demo</span>
              <ArrowRight className="w-5 h-5" />
            </button>
          </div>

          <p className="text-gray-400 text-sm">
            Demo Account: demo@example.com / Demo123!
          </p>
        </div>
      </section>

      {/* Stats Section */}
      <section className="py-12 border-y border-gray-800">
        <div className="max-w-7xl mx-auto px-6">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-8">
            {stats.map((stat, index) => (
              <div key={index} className="text-center">
                <div className="text-3xl font-bold text-purple-400">{stat.value}</div>
                <div className="text-gray-400 mt-1">{stat.label}</div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Features Section */}
      <section id="features" className="py-20 px-6">
        <div className="max-w-7xl mx-auto">
          <div className="text-center mb-12">
            <h2 className="text-4xl font-bold mb-4">Powerful Features</h2>
            <p className="text-gray-400 text-lg">Everything you need to manage APIs efficiently</p>
          </div>

          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-8">
            {features.map((feature, index) => (
              <div 
                key={index}
                className="bg-gray-800/50 backdrop-blur p-6 rounded-xl border border-gray-700 hover:border-purple-500 transition group"
              >
                <div className="w-12 h-12 bg-purple-500/20 rounded-lg flex items-center justify-center mb-4 group-hover:bg-purple-500/30 transition">
                  <div className="text-purple-400">{feature.icon}</div>
                </div>
                <h3 className="text-xl font-semibold mb-2">{feature.title}</h3>
                <p className="text-gray-400">{feature.description}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* How It Works Section */}
      <section id="how-it-works" className="py-20 px-6 bg-gray-800/30">
        <div className="max-w-7xl mx-auto">
          <div className="text-center mb-12">
            <h2 className="text-4xl font-bold mb-4">How It Works</h2>
            <p className="text-gray-400 text-lg">Simple, powerful, and automated</p>
          </div>

          <div className="grid md:grid-cols-4 gap-8">
            {[
              { step: "1", title: "Input Source", desc: "Provide code, URL, or upload files" },
              { step: "2", title: "AI Discovery", desc: "Our AI agents analyze and discover APIs" },
              { step: "3", title: "Generate Specs", desc: "Automatic OpenAPI specification creation" },
              { step: "4", title: "Test & Deploy", desc: "Run tests and deploy mock servers" }
            ].map((item, index) => (
              <div key={index} className="text-center">
                <div className="w-16 h-16 bg-purple-600 rounded-full flex items-center justify-center text-2xl font-bold mx-auto mb-4">
                  {item.step}
                </div>
                <h3 className="text-lg font-semibold mb-2">{item.title}</h3>
                <p className="text-gray-400 text-sm">{item.desc}</p>
                {index < 3 && (
                  <ArrowRight className="w-6 h-6 text-purple-400 mx-auto mt-4 hidden md:block" />
                )}
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Technology Stack */}
      <section id="tech" className="py-20 px-6">
        <div className="max-w-7xl mx-auto">
          <div className="text-center mb-12">
            <h2 className="text-4xl font-bold mb-4">Built with Modern Tech</h2>
            <p className="text-gray-400 text-lg">Enterprise-grade technology stack</p>
          </div>

          <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-6">
            {techStack.map((tech, index) => (
              <div key={index} className="bg-gray-800/50 p-4 rounded-lg text-center">
                <div className="font-semibold">{tech.name}</div>
                <div className="text-gray-500 text-sm">{tech.category}</div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="py-20 px-6 bg-gradient-to-r from-purple-600/20 to-blue-600/20">
        <div className="max-w-4xl mx-auto text-center">
          <h2 className="text-4xl font-bold mb-4">Ready to Transform Your API Workflow?</h2>
          <p className="text-xl text-gray-300 mb-8">
            Join developers who are already using AI to orchestrate their APIs
          </p>
          <div className="flex items-center justify-center space-x-4">
            <button
              onClick={() => navigate('/register')}
              className="px-8 py-4 bg-purple-600 text-white rounded-lg hover:bg-purple-700 transition transform hover:scale-105"
            >
              Start Free Trial
            </button>
            <button
              onClick={() => window.open('https://github.com/JonSnow1807/api-orchestrator', '_blank')}
              className="px-8 py-4 bg-gray-800 text-white rounded-lg hover:bg-gray-700 transition flex items-center space-x-2"
            >
              <Github className="w-5 h-5" />
              <span>View on GitHub</span>
            </button>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="py-8 px-6 border-t border-gray-800">
        <div className="max-w-7xl mx-auto text-center text-gray-400">
          <p>© 2025 API Orchestrator. Built with ❤️ using Claude AI</p>
          <p className="mt-2 text-sm">
            Powered by FastAPI, React, and Claude Opus 4.1
          </p>
        </div>
      </footer>
      </div>
    </Layout>
  );
};

export default LandingPage;