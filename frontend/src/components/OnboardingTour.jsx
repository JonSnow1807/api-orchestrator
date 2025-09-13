import React, { useState, useEffect } from 'react';
import { X, ChevronRight, ChevronLeft, Sparkles } from 'lucide-react';

const OnboardingTour = ({ onComplete }) => {
  const [currentStep, setCurrentStep] = useState(0);
  const [isVisible, setIsVisible] = useState(false);

  const tourSteps = [
    {
      id: 'welcome',
      title: 'Welcome to API Orchestrator! 🚀',
      description: 'The ultimate POSTMAN KILLER with AI-powered features. Let\'s take a quick tour to get you started.',
      target: null,
      position: 'center'
    },
    {
      id: 'dashboard',
      title: 'Your Command Center',
      description: 'The dashboard gives you an overview of all your projects, recent activity, and quick actions.',
      target: '.dashboard-overview',
      position: 'bottom'
    },
    {
      id: 'create-project',
      title: 'Create Your First Project',
      description: 'Click here to create a new API testing project. We support REST, GraphQL, WebSocket, and more!',
      target: '.create-project-btn',
      position: 'bottom'
    },
    {
      id: 'ai-features',
      title: 'AI-Powered Testing',
      description: 'Use natural language to create tests! Just describe what you want to test in plain English.',
      target: '.natural-language-tab',
      position: 'right'
    },
    {
      id: 'visualization',
      title: 'Data Visualization',
      description: 'Visualize your API responses with 8 different chart types. Perfect for understanding complex data.',
      target: '.visualization-tab',
      position: 'right'
    },
    {
      id: 'mock-servers',
      title: 'Instant Mock Servers',
      description: 'Create mock servers instantly from your API specs. Great for frontend development!',
      target: '.mock-server-tab',
      position: 'right'
    },
    {
      id: 'team',
      title: 'Collaborate with Your Team',
      description: 'Invite team members, share workspaces, and collaborate in real-time.',
      target: '.team-management',
      position: 'left'
    },
    {
      id: 'complete',
      title: 'You\'re All Set! 🎉',
      description: 'You now know the basics. Explore the platform and discover more powerful features!',
      target: null,
      position: 'center'
    }
  ];

  useEffect(() => {
    // Check if user has seen the tour
    const hasSeenTour = localStorage.getItem('hasSeenTour');
    if (!hasSeenTour) {
      setTimeout(() => setIsVisible(true), 1000);
    }
  }, []);

  const handleNext = () => {
    if (currentStep < tourSteps.length - 1) {
      setCurrentStep(currentStep + 1);
    } else {
      handleComplete();
    }
  };

  const handlePrevious = () => {
    if (currentStep > 0) {
      setCurrentStep(currentStep - 1);
    }
  };

  const handleSkip = () => {
    handleComplete();
  };

  const handleComplete = () => {
    localStorage.setItem('hasSeenTour', 'true');
    setIsVisible(false);
    if (onComplete) onComplete();
  };

  if (!isVisible) return null;

  const currentTourStep = tourSteps[currentStep];
  const isFirstStep = currentStep === 0;
  const isLastStep = currentStep === tourSteps.length - 1;

  return (
    <>
      {/* Overlay */}
      <div className="fixed inset-0 bg-black/60 z-[9998] transition-opacity" />

      {/* Tour Modal */}
      <div 
        className={`fixed z-[9999] ${
          currentTourStep.position === 'center' 
            ? 'top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2'
            : 'top-20 left-1/2 transform -translate-x-1/2'
        }`}
      >
        <div className="bg-gray-800 rounded-xl shadow-2xl border border-purple-500/30 p-6 max-w-md">
          {/* Header */}
          <div className="flex items-start justify-between mb-4">
            <div className="flex items-center space-x-2">
              <Sparkles className="w-5 h-5 text-purple-400" />
              <h3 className="text-lg font-semibold text-white">
                {currentTourStep.title}
              </h3>
            </div>
            <button
              onClick={handleSkip}
              className="text-gray-400 hover:text-white transition-colors"
              aria-label="Close tour"
            >
              <X className="w-5 h-5" />
            </button>
          </div>

          {/* Content */}
          <p className="text-gray-300 mb-6">
            {currentTourStep.description}
          </p>

          {/* Progress */}
          <div className="flex items-center justify-center space-x-1 mb-4">
            {tourSteps.map((_, index) => (
              <div
                key={index}
                className={`h-1.5 transition-all ${
                  index === currentStep
                    ? 'w-8 bg-purple-500'
                    : index < currentStep
                    ? 'w-1.5 bg-purple-400'
                    : 'w-1.5 bg-gray-600'
                } rounded-full`}
              />
            ))}
          </div>

          {/* Actions */}
          <div className="flex items-center justify-between">
            <button
              onClick={handleSkip}
              className="text-sm text-gray-400 hover:text-white transition-colors"
            >
              Skip tour
            </button>

            <div className="flex items-center space-x-2">
              {!isFirstStep && (
                <button
                  onClick={handlePrevious}
                  className="flex items-center space-x-1 px-3 py-1.5 text-gray-300 hover:text-white transition-colors"
                >
                  <ChevronLeft className="w-4 h-4" />
                  <span>Back</span>
                </button>
              )}

              <button
                onClick={handleNext}
                className="flex items-center space-x-1 px-4 py-1.5 bg-purple-600 hover:bg-purple-700 text-white rounded-lg transition-colors"
              >
                <span>{isLastStep ? 'Get Started' : 'Next'}</span>
                {!isLastStep && <ChevronRight className="w-4 h-4" />}
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* Highlight target element */}
      {currentTourStep.target && (
        <style>{`
          ${currentTourStep.target} {
            position: relative;
            z-index: 9997;
            box-shadow: 0 0 0 4px rgba(168, 85, 247, 0.4);
            border-radius: 8px;
          }
        `}</style>
      )}
    </>
  );
};

export default OnboardingTour;