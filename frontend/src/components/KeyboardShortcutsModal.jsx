import React from 'react';
import { XMarkIcon } from '@heroicons/react/24/outline';

const KeyboardShortcutsModal = ({ isOpen, onClose }) => {
  if (!isOpen) return null;

  const shortcuts = [
    {
      category: 'Navigation',
      items: [
        { keys: ['⌘', 'K'], description: 'Open search' },
        { keys: ['⌘', '⇧', 'P'], description: 'Command palette' },
        { keys: ['G', 'H'], description: 'Go to Home' },
        { keys: ['G', 'P'], description: 'Go to Projects' },
        { keys: ['G', 'C'], description: 'Go to Collections' },
        { keys: ['G', 'M'], description: 'Go to Monitoring' },
        { keys: ['G', 'S'], description: 'Go to Settings' },
      ]
    },
    {
      category: 'Actions',
      items: [
        { keys: ['⌘', 'N'], description: 'New request' },
        { keys: ['⌘', 'S'], description: 'Save request' },
        { keys: ['⌘', '↵'], description: 'Send request' },
        { keys: ['⌘', 'D'], description: 'Duplicate request' },
        { keys: ['⌘', '/'], description: 'Toggle sidebar' },
        { keys: ['ESC'], description: 'Close modal / Unfocus' },
      ]
    },
    {
      category: 'Request Tabs',
      items: [
        { keys: ['⌘', '1'], description: 'Parameters tab' },
        { keys: ['⌘', '2'], description: 'Headers tab' },
        { keys: ['⌘', '3'], description: 'Body tab' },
        { keys: ['⌘', '4'], description: 'Auth tab' },
      ]
    },
    {
      category: 'Help',
      items: [
        { keys: ['?'], description: 'Show keyboard shortcuts' },
      ]
    }
  ];

  const isWindows = navigator.platform.indexOf('Win') > -1;

  const renderKey = (key) => {
    // Replace Mac symbols with Windows equivalents
    if (isWindows) {
      if (key === '⌘') return 'Ctrl';
      if (key === '⇧') return 'Shift';
      if (key === '⌥') return 'Alt';
      if (key === '↵') return 'Enter';
    }
    return key;
  };

  return (
    <div className="fixed inset-0 z-50 overflow-y-auto">
      <div className="flex items-center justify-center min-h-screen px-4">
        {/* Backdrop */}
        <div 
          className="fixed inset-0 bg-black bg-opacity-50 transition-opacity"
          onClick={onClose}
        />

        {/* Modal */}
        <div className="relative bg-white dark:bg-gray-900 rounded-xl shadow-2xl max-w-2xl w-full max-h-[80vh] overflow-hidden">
          {/* Header */}
          <div className="flex items-center justify-between px-6 py-4 border-b border-gray-200 dark:border-gray-700">
            <h2 className="text-xl font-semibold text-gray-900 dark:text-white">
              Keyboard Shortcuts
            </h2>
            <button
              onClick={onClose}
              data-modal-close
              className="text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 transition-colors"
            >
              <XMarkIcon className="w-5 h-5" />
            </button>
          </div>

          {/* Content */}
          <div className="px-6 py-4 overflow-y-auto max-h-[calc(80vh-120px)]">
            <div className="space-y-6">
              {shortcuts.map((section) => (
                <div key={section.category}>
                  <h3 className="text-sm font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider mb-3">
                    {section.category}
                  </h3>
                  <div className="space-y-2">
                    {section.items.map((item, index) => (
                      <div 
                        key={index}
                        className="flex items-center justify-between py-2 px-3 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-800 transition-colors"
                      >
                        <span className="text-sm text-gray-700 dark:text-gray-300">
                          {item.description}
                        </span>
                        <div className="flex items-center gap-1">
                          {item.keys.map((key, keyIndex) => (
                            <React.Fragment key={keyIndex}>
                              {keyIndex > 0 && (
                                <span className="text-gray-400 text-xs mx-1">+</span>
                              )}
                              <kbd className="px-2 py-1 text-xs font-semibold text-gray-800 bg-gray-100 border border-gray-200 rounded-md dark:bg-gray-800 dark:text-gray-100 dark:border-gray-700">
                                {renderKey(key)}
                              </kbd>
                            </React.Fragment>
                          ))}
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              ))}
            </div>

            {/* Pro tip */}
            <div className="mt-6 p-4 bg-blue-50 dark:bg-blue-900/20 rounded-lg">
              <p className="text-sm text-blue-700 dark:text-blue-300">
                <strong>Pro tip:</strong> Press <kbd className="px-1 py-0.5 text-xs font-semibold bg-blue-100 dark:bg-blue-800 rounded">?</kbd> anytime to view these shortcuts.
              </p>
            </div>
          </div>

          {/* Footer */}
          <div className="px-6 py-3 bg-gray-50 dark:bg-gray-800 border-t border-gray-200 dark:border-gray-700">
            <p className="text-xs text-gray-500 dark:text-gray-400 text-center">
              {isWindows ? 'Windows/Linux' : 'macOS'} shortcuts shown. 
              Some shortcuts may vary based on your browser.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default KeyboardShortcutsModal;