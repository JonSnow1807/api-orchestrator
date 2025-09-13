import React, { useState, useEffect } from 'react';
import { Type, Plus, Minus } from 'lucide-react';

const FontSizeControl = () => {
  const [fontSize, setFontSize] = useState(() => {
    // Load saved font size or default to 'medium'
    return localStorage.getItem('fontSize') || 'medium';
  });

  const fontSizeClasses = {
    small: 'text-sm',
    medium: 'text-base',
    large: 'text-lg',
    xlarge: 'text-xl'
  };

  const fontSizeScale = {
    small: 0.875,
    medium: 1,
    large: 1.125,
    xlarge: 1.25
  };

  useEffect(() => {
    // Apply font size to root element
    const scale = fontSizeScale[fontSize];
    document.documentElement.style.fontSize = `${16 * scale}px`;
    localStorage.setItem('fontSize', fontSize);
  }, [fontSize]);

  const increaseFontSize = () => {
    const sizes = Object.keys(fontSizeClasses);
    const currentIndex = sizes.indexOf(fontSize);
    if (currentIndex < sizes.length - 1) {
      setFontSize(sizes[currentIndex + 1]);
    }
  };

  const decreaseFontSize = () => {
    const sizes = Object.keys(fontSizeClasses);
    const currentIndex = sizes.indexOf(fontSize);
    if (currentIndex > 0) {
      setFontSize(sizes[currentIndex - 1]);
    }
  };

  const resetFontSize = () => {
    setFontSize('medium');
  };

  return (
    <div className="flex items-center space-x-2 p-2 bg-gray-800 rounded-lg">
      <button
        onClick={decreaseFontSize}
        disabled={fontSize === 'small'}
        className="p-1 text-gray-400 hover:text-white disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
        aria-label="Decrease font size"
        title="Decrease font size"
      >
        <Minus className="w-4 h-4" />
      </button>

      <button
        onClick={resetFontSize}
        className="flex items-center space-x-1 px-2 py-1 text-gray-400 hover:text-white transition-colors"
        aria-label="Reset font size"
        title="Reset font size"
      >
        <Type className="w-4 h-4" />
        <span className="text-xs">{fontSize}</span>
      </button>

      <button
        onClick={increaseFontSize}
        disabled={fontSize === 'xlarge'}
        className="p-1 text-gray-400 hover:text-white disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
        aria-label="Increase font size"
        title="Increase font size"
      >
        <Plus className="w-4 h-4" />
      </button>
    </div>
  );
};

export default FontSizeControl;