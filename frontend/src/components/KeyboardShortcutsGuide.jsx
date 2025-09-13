import React from 'react';

const KeyboardShortcutsGuide = ({ isOpen, onClose }) => {
  if (!isOpen) return null;

  const isMac = navigator.platform.includes('Mac');
  const modKey = isMac ? '⌘' : 'Ctrl';

  const shortcuts = [
    { category: 'Navigation', items: [
      { keys: `${modKey} K`, description: 'Search' },
      { keys: `${modKey} Shift P`, description: 'Command Palette' },
      { keys: 'G H', description: 'Go to Home' },
      { keys: 'G P', description: 'Go to Projects' },
      { keys: 'G C', description: 'Go to Collections' },
      { keys: 'G M', description: 'Go to Monitoring' },
      { keys: 'G S', description: 'Go to Settings' },
    ]},
    { category: 'Actions', items: [
      { keys: `${modKey} N`, description: 'New Request' },
      { keys: `${modKey} S`, description: 'Save' },
      { keys: `${modKey} Enter`, description: 'Send Request' },
      { keys: `${modKey} D`, description: 'Duplicate' },
      { keys: `${modKey} /`, description: 'Toggle Sidebar' },
    ]},
    { category: 'Tabs', items: [
      { keys: `${modKey} 1`, description: 'Parameters Tab' },
      { keys: `${modKey} 2`, description: 'Headers Tab' },
      { keys: `${modKey} 3`, description: 'Body Tab' },
      { keys: `${modKey} 4`, description: 'Auth Tab' },
    ]},
    { category: 'General', items: [
      { keys: '?', description: 'Show This Guide' },
      { keys: 'Esc', description: 'Close Modal / Unfocus' },
    ]}
  ];

  return (
    <div className="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4">
      <div className="bg-gray-800 rounded-xl p-6 max-w-3xl max-h-[80vh] overflow-auto">
        <div className="flex items-center justify-between mb-6">
          <h2 className="text-2xl font-semibold text-white">Keyboard Shortcuts</h2>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-white transition p-2"
            aria-label="Close"
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {shortcuts.map((section) => (
            <div key={section.category} className="space-y-3">
              <h3 className="text-sm font-medium text-purple-400 uppercase tracking-wider">
                {section.category}
              </h3>
              <div className="space-y-2">
                {section.items.map((shortcut) => (
                  <div
                    key={shortcut.keys}
                    className="flex items-center justify-between py-1.5 px-2 rounded hover:bg-gray-700/50 transition"
                  >
                    <span className="text-gray-300 text-sm">{shortcut.description}</span>
                    <kbd className="px-2 py-1 bg-gray-700 text-gray-300 rounded text-xs font-mono border border-gray-600">
                      {shortcut.keys}
                    </kbd>
                  </div>
                ))}
              </div>
            </div>
          ))}
        </div>

        <div className="mt-6 pt-4 border-t border-gray-700">
          <p className="text-sm text-gray-400 text-center">
            Press <kbd className="px-2 py-0.5 bg-gray-700 text-gray-300 rounded text-xs font-mono">?</kbd> anytime to show this guide
          </p>
        </div>
      </div>
    </div>
  );
};

export default KeyboardShortcutsGuide;