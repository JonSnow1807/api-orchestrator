import { useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { toast } from 'react-hot-toast';

const useKeyboardShortcuts = (actions = {}) => {
  const navigate = useNavigate();

  // Default shortcuts that work globally
  const defaultShortcuts = {
    // Navigation shortcuts
    'cmd+k,ctrl+k': () => {
      document.getElementById('global-search')?.focus();
      toast('Search activated', { icon: '🔍' });
    },
    'cmd+shift+p,ctrl+shift+p': () => {
      document.getElementById('command-palette')?.click();
      toast('Command palette opened', { icon: '🎨' });
    },
    'g h': () => {
      navigate('/');
      toast('Home', { icon: '🏠' });
    },
    'g p': () => {
      navigate('/projects');
      toast('Projects', { icon: '📁' });
    },
    'g c': () => {
      navigate('/collections');
      toast('Collections', { icon: '📚' });
    },
    'g m': () => {
      navigate('/monitoring');
      toast('Monitoring', { icon: '📊' });
    },
    'g s': () => {
      navigate('/settings');
      toast('Settings', { icon: '⚙️' });
    },
    
    // Action shortcuts
    'cmd+n,ctrl+n': () => {
      document.getElementById('new-request')?.click();
      toast('New request', { icon: '➕' });
    },
    'cmd+s,ctrl+s': (e) => {
      e.preventDefault();
      document.getElementById('save-request')?.click();
      toast.success('Saved');
    },
    'cmd+enter,ctrl+enter': () => {
      document.getElementById('send-request')?.click();
      toast('Request sent', { icon: '🚀' });
    },
    'cmd+d,ctrl+d': (e) => {
      e.preventDefault();
      document.getElementById('duplicate-request')?.click();
      toast('Duplicated', { icon: '📋' });
    },
    'cmd+/,ctrl+/': (e) => {
      e.preventDefault();
      document.getElementById('toggle-sidebar')?.click();
    },
    
    // View shortcuts
    'cmd+1,ctrl+1': () => {
      document.querySelector('[data-tab="params"]')?.click();
    },
    'cmd+2,ctrl+2': () => {
      document.querySelector('[data-tab="headers"]')?.click();
    },
    'cmd+3,ctrl+3': () => {
      document.querySelector('[data-tab="body"]')?.click();
    },
    'cmd+4,ctrl+4': () => {
      document.querySelector('[data-tab="auth"]')?.click();
    },
    
    // Help
    '?': () => {
      if (document.activeElement.tagName !== 'INPUT' && 
          document.activeElement.tagName !== 'TEXTAREA') {
        document.getElementById('shortcuts-help')?.click();
        toast('Keyboard shortcuts', { icon: '⌨️' });
      }
    },
    
    // Escape actions
    'escape': () => {
      // Close any open modals
      document.querySelector('[data-modal-close]')?.click();
      // Unfocus any focused elements
      document.activeElement?.blur();
    }
  };

  // Merge default shortcuts with custom actions
  const shortcuts = { ...defaultShortcuts, ...actions };

  const handleKeyPress = useCallback((event) => {
    // Don't trigger shortcuts when typing in inputs (unless it's a global shortcut like cmd+s)
    const isInput = ['INPUT', 'TEXTAREA', 'SELECT'].includes(event.target.tagName);
    const isGlobalShortcut = event.metaKey || event.ctrlKey;
    
    if (isInput && !isGlobalShortcut) {
      return;
    }

    // Build the key combination string
    const keys = [];
    if (event.metaKey) keys.push('cmd');
    if (event.ctrlKey) keys.push('ctrl');
    if (event.altKey) keys.push('alt');
    if (event.shiftKey) keys.push('shift');
    
    // Get the actual key
    let key = event.key.toLowerCase();
    if (key === ' ') key = 'space';
    if (key === 'arrowup') key = 'up';
    if (key === 'arrowdown') key = 'down';
    if (key === 'arrowleft') key = 'left';
    if (key === 'arrowright') key = 'right';
    
    keys.push(key);
    const keyCombo = keys.join('+');

    // Check for matching shortcuts
    for (const [shortcut, action] of Object.entries(shortcuts)) {
      const shortcuts = shortcut.split(',');
      if (shortcuts.some(s => s.trim() === keyCombo)) {
        action(event);
        return;
      }
    }
  }, [shortcuts]);

  // Handle key sequences (like 'g h' for go home)
  const keySequence = useCallback(() => {
    let sequence = [];
    let sequenceTimer;

    return (event) => {
      const key = event.key.toLowerCase();
      
      // Clear sequence after 1 second
      clearTimeout(sequenceTimer);
      sequenceTimer = setTimeout(() => {
        sequence = [];
      }, 1000);

      // Add to sequence
      sequence.push(key);
      const sequenceStr = sequence.join(' ');

      // Check for matching sequences
      for (const [shortcut, action] of Object.entries(shortcuts)) {
        if (shortcut === sequenceStr) {
          action(event);
          sequence = [];
          clearTimeout(sequenceTimer);
          return;
        }
      }

      // If sequence is getting too long, reset
      if (sequence.length > 3) {
        sequence = [key];
      }
    };
  }, [shortcuts]);

  const sequenceHandler = useCallback(keySequence(), [keySequence]);

  useEffect(() => {
    // Add both handlers
    window.addEventListener('keydown', handleKeyPress);
    window.addEventListener('keypress', sequenceHandler);

    return () => {
      window.removeEventListener('keydown', handleKeyPress);
      window.removeEventListener('keypress', sequenceHandler);
    };
  }, [handleKeyPress, sequenceHandler]);

  // Return a function to programmatically trigger shortcuts
  const triggerShortcut = (shortcut) => {
    const action = shortcuts[shortcut];
    if (action) {
      action(new KeyboardEvent('keydown'));
    }
  };

  return { triggerShortcut };
};

export default useKeyboardShortcuts;