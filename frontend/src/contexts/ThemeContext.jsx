import React, { createContext, useContext, useState, useEffect } from 'react';
import { useColorMode, ColorModeProvider, ColorModeScript } from '@chakra-ui/react';

const ThemeContext = createContext();

export const useTheme = () => {
  const context = useContext(ThemeContext);
  if (context === undefined) {
    throw new Error('useTheme must be used within a ThemeProvider');
  }
  return context;
};

export const ThemeProvider = ({ children }) => {
  const { colorMode, toggleColorMode, setColorMode } = useColorMode();
  const [systemPreference, setSystemPreference] = useState('light');

  // Detect system preference
  useEffect(() => {
    const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)');
    setSystemPreference(mediaQuery.matches ? 'dark' : 'light');

    const handleChange = (e) => {
      setSystemPreference(e.matches ? 'dark' : 'light');
    };

    mediaQuery.addEventListener('change', handleChange);
    return () => mediaQuery.removeEventListener('change', handleChange);
  }, []);

  // Theme configurations
  const themes = {
    light: {
      name: 'Light',
      icon: '☀️',
      colors: {
        primary: '#2B6CB0',
        secondary: '#4299E1',
        background: '#FFFFFF',
        surface: '#F7FAFC',
        text: '#1A202C',
        textSecondary: '#4A5568',
        border: '#E2E8F0',
        accent: '#3182CE'
      }
    },
    dark: {
      name: 'Dark',
      icon: '🌙',
      colors: {
        primary: '#63B3ED',
        secondary: '#4299E1',
        background: '#1A202C',
        surface: '#2D3748',
        text: '#FFFFFF',
        textSecondary: '#A0AEC0',
        border: '#4A5568',
        accent: '#63B3ED'
      }
    },
    auto: {
      name: 'Auto',
      icon: '🔄',
      colors: systemPreference === 'dark' ? {
        primary: '#63B3ED',
        secondary: '#4299E1',
        background: '#1A202C',
        surface: '#2D3748',
        text: '#FFFFFF',
        textSecondary: '#A0AEC0',
        border: '#4A5568',
        accent: '#63B3ED'
      } : {
        primary: '#2B6CB0',
        secondary: '#4299E1',
        background: '#FFFFFF',
        surface: '#F7FAFC',
        text: '#1A202C',
        textSecondary: '#4A5568',
        border: '#E2E8F0',
        accent: '#3182CE'
      }
    }
  };

  const [themeMode, setThemeMode] = useState(() => {
    const stored = localStorage.getItem('theme-mode');
    return stored || 'auto';
  });

  // Update color mode based on theme mode
  useEffect(() => {
    let targetMode;
    if (themeMode === 'auto') {
      targetMode = systemPreference;
    } else {
      targetMode = themeMode;
    }

    if (colorMode !== targetMode) {
      setColorMode(targetMode);
    }

    localStorage.setItem('theme-mode', themeMode);
  }, [themeMode, systemPreference, colorMode, setColorMode]);

  const currentTheme = themes[themeMode] || themes.auto;

  const switchTheme = (mode) => {
    setThemeMode(mode);
  };

  const toggleTheme = () => {
    if (themeMode === 'light') {
      setThemeMode('dark');
    } else if (themeMode === 'dark') {
      setThemeMode('auto');
    } else {
      setThemeMode('light');
    }
  };

  const value = {
    themeMode,
    colorMode,
    currentTheme,
    themes,
    systemPreference,
    switchTheme,
    toggleTheme,
    toggleColorMode,
    isDark: colorMode === 'dark',
    isLight: colorMode === 'light',
    isAuto: themeMode === 'auto'
  };

  return (
    <ThemeContext.Provider value={value}>
      {children}
    </ThemeContext.Provider>
  );
};

// Theme toggle component
export const ThemeToggle = ({ size = 'md', showLabel = false }) => {
  const { themeMode, themes, toggleTheme } = useTheme();

  return (
    <button
      onClick={toggleTheme}
      className={`
        inline-flex items-center justify-center rounded-lg border-2 transition-all duration-200
        ${size === 'sm' ? 'w-8 h-8 text-sm' : size === 'lg' ? 'w-12 h-12 text-lg' : 'w-10 h-10 text-base'}
        hover:scale-105 active:scale-95
        border-gray-300 dark:border-gray-600
        bg-white dark:bg-gray-800
        text-gray-700 dark:text-gray-300
        hover:bg-gray-50 dark:hover:bg-gray-700
        focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2
      `}
      title={`Current: ${themes[themeMode]?.name || 'Auto'} - Click to switch`}
    >
      <span className="transition-transform duration-200 hover:rotate-12">
        {themes[themeMode]?.icon || '🔄'}
      </span>
      {showLabel && (
        <span className="ml-2 text-sm font-medium">
          {themes[themeMode]?.name || 'Auto'}
        </span>
      )}
    </button>
  );
};

// Theme selector dropdown
export const ThemeSelector = () => {
  const { themeMode, themes, switchTheme } = useTheme();

  return (
    <div className="relative">
      <select
        value={themeMode}
        onChange={(e) => switchTheme(e.target.value)}
        className="
          appearance-none bg-white dark:bg-gray-800 border border-gray-300 dark:border-gray-600
          text-gray-700 dark:text-gray-300 py-2 px-4 pr-8 rounded-lg
          focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent
          hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors duration-200
        "
      >
        {Object.entries(themes).map(([key, theme]) => (
          <option key={key} value={key}>
            {theme.icon} {theme.name}
          </option>
        ))}
      </select>
      <div className="pointer-events-none absolute inset-y-0 right-0 flex items-center px-2 text-gray-700 dark:text-gray-300">
        <svg className="fill-current h-4 w-4" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20">
          <path d="M9.293 12.95l.707.707L15.657 8l-1.414-1.414L10 10.828 5.757 6.586 4.343 8z" />
        </svg>
      </div>
    </div>
  );
};

export default ThemeContext;