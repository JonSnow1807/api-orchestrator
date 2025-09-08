import React from 'react';
import { Loader2 } from 'lucide-react';

const LoadingSpinner = ({ 
  size = 'default', 
  message = 'Loading...', 
  fullScreen = false,
  inline = false 
}) => {
  const sizeClasses = {
    small: 'w-4 h-4',
    default: 'w-8 h-8',
    large: 'w-12 h-12',
    xlarge: 'w-16 h-16'
  };

  const spinner = (
    <div className={`flex ${inline ? 'inline-flex' : 'flex-col'} items-center justify-center ${inline ? 'space-x-2' : 'space-y-3'}`}>
      <Loader2 className={`${sizeClasses[size]} text-purple-500 animate-spin`} />
      {message && (
        <p className={`text-gray-400 ${size === 'small' ? 'text-xs' : size === 'large' || size === 'xlarge' ? 'text-lg' : 'text-sm'}`}>
          {message}
        </p>
      )}
    </div>
  );

  if (fullScreen) {
    return (
      <div className="fixed inset-0 bg-gray-900/50 backdrop-blur-sm flex items-center justify-center z-50">
        {spinner}
      </div>
    );
  }

  return spinner;
};

export default LoadingSpinner;