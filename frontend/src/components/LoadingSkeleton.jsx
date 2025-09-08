import React from 'react';

const LoadingSkeleton = ({ 
  variant = 'text', 
  width = '100%', 
  height = '20px',
  className = '',
  count = 1,
  animate = true
}) => {
  const baseClasses = `bg-gray-700/50 rounded ${animate ? 'animate-pulse-slow' : ''} ${className}`;
  
  const variants = {
    text: 'h-4 rounded',
    title: 'h-8 rounded',
    avatar: 'w-10 h-10 rounded-full',
    thumbnail: 'w-full h-48 rounded-lg',
    card: 'w-full h-32 rounded-lg',
    button: 'h-10 w-24 rounded-lg',
    paragraph: 'space-y-2'
  };

  const renderSkeleton = () => {
    if (variant === 'paragraph') {
      return (
        <div className={variants[variant]}>
          <div className={`${baseClasses} h-4 w-full`} />
          <div className={`${baseClasses} h-4 w-full`} />
          <div className={`${baseClasses} h-4 w-3/4`} />
        </div>
      );
    }

    return (
      <div 
        className={`${baseClasses} ${variants[variant] || ''}`}
        style={{ width, height }}
      />
    );
  };

  if (count > 1) {
    return (
      <div className="space-y-2">
        {Array.from({ length: count }).map((_, index) => (
          <div key={index}>{renderSkeleton()}</div>
        ))}
      </div>
    );
  }

  return renderSkeleton();
};

// Composite skeleton components for common patterns
export const CardSkeleton = ({ animate = true }) => (
  <div className={`bg-gray-800/50 rounded-lg p-6 border border-gray-700 ${animate ? 'animate-pulse-slow' : ''}`}>
    <div className="flex items-start justify-between mb-4">
      <LoadingSkeleton variant="title" width="60%" animate={false} />
      <LoadingSkeleton variant="avatar" animate={false} />
    </div>
    <LoadingSkeleton variant="paragraph" animate={false} />
    <div className="flex space-x-2 mt-4">
      <LoadingSkeleton variant="button" animate={false} />
      <LoadingSkeleton variant="button" animate={false} />
    </div>
  </div>
);

export const ListItemSkeleton = ({ animate = true }) => (
  <div className={`flex items-center space-x-4 p-4 bg-gray-800/50 rounded-lg border border-gray-700 ${animate ? 'animate-pulse-slow' : ''}`}>
    <LoadingSkeleton variant="avatar" animate={false} />
    <div className="flex-1 space-y-2">
      <LoadingSkeleton variant="text" width="40%" animate={false} />
      <LoadingSkeleton variant="text" width="60%" animate={false} />
    </div>
    <LoadingSkeleton variant="button" animate={false} />
  </div>
);

export const TableRowSkeleton = ({ columns = 4, animate = true }) => (
  <tr className={animate ? 'animate-pulse-slow' : ''}>
    {Array.from({ length: columns }).map((_, index) => (
      <td key={index} className="px-6 py-4">
        <LoadingSkeleton variant="text" animate={false} />
      </td>
    ))}
  </tr>
);

export default LoadingSkeleton;