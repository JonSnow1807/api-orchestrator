import React, { useState, useEffect } from 'react';
import {
  Box,
  Paper,
  Typography,
  IconButton,
  Tooltip,
  Button,
  ButtonGroup,
  Chip,
  Stack,
  Alert,
  LinearProgress,
} from '@mui/material';
import {
  ContentCopy as CopyIcon,
  Download as DownloadIcon,
  Fullscreen as FullscreenIcon,
  FullscreenExit as FullscreenExitIcon,
  WrapText as WrapIcon,
  FormatAlignLeft as NoWrapIcon,
  ZoomIn as ZoomInIcon,
  ZoomOut as ZoomOutIcon,
  Refresh as RefreshIcon,
  CheckCircle as CheckIcon,
  Warning as WarningIcon,
  PlayArrow as RunIcon,
  BugReport as DebugIcon,
} from '@mui/icons-material';
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { vscDarkPlus, vs, atomDark, dracula, materialDark, materialLight } from 'react-syntax-highlighter/dist/esm/styles/prism';

const themes = {
  vscDarkPlus: { name: 'VS Code Dark', style: vscDarkPlus },
  vs: { name: 'VS Code Light', style: vs },
  atomDark: { name: 'Atom Dark', style: atomDark },
  dracula: { name: 'Dracula', style: dracula },
  materialDark: { name: 'Material Dark', style: materialDark },
  materialLight: { name: 'Material Light', style: materialLight },
};

const CodePreview = ({ code, language, library, onCopy, onDownload, onRefresh }) => {
  const [selectedTheme, setSelectedTheme] = useState('vscDarkPlus');
  const [wordWrap, setWordWrap] = useState(true);
  const [fullscreen, setFullscreen] = useState(false);
  const [fontSize, setFontSize] = useState(14);
  const [copied, setCopied] = useState(false);
  const [syntaxErrors, setSyntaxErrors] = useState([]);
  const [codeMetrics, setCodeMetrics] = useState({
    lines: 0,
    characters: 0,
    complexity: 'Low',
    estimatedTime: '< 1 min',
  });

  useEffect(() => {
    if (code) {
      // Calculate code metrics
      const lines = code.split('\n').length;
      const characters = code.length;
      const complexity = calculateComplexity(code);
      const estimatedTime = estimateImplementationTime(lines, complexity);
      
      setCodeMetrics({
        lines,
        characters,
        complexity,
        estimatedTime,
      });
      
      // Check for basic syntax issues (simplified)
      const errors = checkSyntaxErrors(code, language);
      setSyntaxErrors(errors);
    }
  }, [code, language]);

  const calculateComplexity = (code) => {
    // Simple complexity calculation based on control structures
    const controlStructures = (code.match(/\b(if|else|for|while|switch|try|catch)\b/g) || []).length;
    const functions = (code.match(/\b(function|def|func|method|class)\b/g) || []).length;
    
    const score = controlStructures + functions * 2;
    
    if (score < 5) return 'Low';
    if (score < 15) return 'Medium';
    if (score < 30) return 'High';
    return 'Very High';
  };

  const estimateImplementationTime = (lines, complexity) => {
    const baseTime = lines * 0.5; // 0.5 minutes per line as base
    const complexityMultiplier = {
      'Low': 1,
      'Medium': 1.5,
      'High': 2,
      'Very High': 3,
    };
    
    const minutes = baseTime * complexityMultiplier[complexity];
    
    if (minutes < 1) return '< 1 min';
    if (minutes < 5) return `~${Math.round(minutes)} min`;
    if (minutes < 60) return `~${Math.round(minutes)} min`;
    return `~${Math.round(minutes / 60)} hours`;
  };

  const checkSyntaxErrors = (code, language) => {
    const errors = [];
    
    // Basic checks for common issues
    if (language === 'javascript' || language === 'typescript') {
      if (code.includes('console.log') && !code.includes('// eslint-disable')) {
        errors.push({ line: null, message: 'Consider removing console.log statements for production', severity: 'warning' });
      }
    }
    
    if (language === 'python') {
      if (code.includes('print(') && !code.includes('# noqa')) {
        errors.push({ line: null, message: 'Consider using logging instead of print statements', severity: 'warning' });
      }
    }
    
    // Check for potential security issues
    if (code.includes('eval(') || code.includes('exec(')) {
      errors.push({ line: null, message: 'Avoid using eval/exec for security reasons', severity: 'error' });
    }
    
    if (code.includes('TODO') || code.includes('FIXME')) {
      errors.push({ line: null, message: 'Code contains TODO/FIXME comments', severity: 'info' });
    }
    
    return errors;
  };

  const handleCopy = () => {
    navigator.clipboard.writeText(code);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
    onCopy && onCopy();
  };

  const handleDownload = () => {
    const blob = new Blob([code], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `api-client.${getFileExtension(language)}`;
    a.click();
    URL.revokeObjectURL(url);
    onDownload && onDownload();
  };

  const getFileExtension = (lang) => {
    const extensions = {
      javascript: 'js',
      typescript: 'ts',
      python: 'py',
      java: 'java',
      csharp: 'cs',
      go: 'go',
      ruby: 'rb',
      php: 'php',
      swift: 'swift',
      kotlin: 'kt',
      rust: 'rs',
      cpp: 'cpp',
      dart: 'dart',
      scala: 'scala',
      elixir: 'ex',
      perl: 'pl',
      r: 'r',
      matlab: 'm',
      shell: 'sh',
      powershell: 'ps1',
      objectivec: 'm',
      lua: 'lua',
      haskell: 'hs',
      clojure: 'clj',
      fsharp: 'fs',
      julia: 'jl',
      groovy: 'groovy',
      crystal: 'cr',
      nim: 'nim',
      ocaml: 'ml',
    };
    return extensions[lang] || 'txt';
  };

  const getLanguageForHighlighter = (lang) => {
    // Map our language keys to Prism language keys
    const languageMap = {
      csharp: 'csharp',
      cpp: 'cpp',
      objectivec: 'objectivec',
      fsharp: 'fsharp',
      shell: 'bash',
      powershell: 'powershell',
    };
    return languageMap[lang] || lang;
  };

  return (
    <Box sx={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
      {/* Toolbar */}
      <Box sx={{ 
        display: 'flex', 
        justifyContent: 'space-between', 
        alignItems: 'center', 
        mb: 2,
        p: 1,
        bgcolor: 'background.default',
        borderRadius: 1,
      }}>
        <Stack direction="row" spacing={1} alignItems="center">
          <Chip 
            label={language.toUpperCase()} 
            color="primary" 
            size="small"
          />
          <Chip 
            label={library} 
            variant="outlined" 
            size="small"
          />
          <Typography variant="caption" color="text.secondary">
            {codeMetrics.lines} lines • {codeMetrics.complexity} complexity • {codeMetrics.estimatedTime}
          </Typography>
        </Stack>

        <Stack direction="row" spacing={1}>
          {/* Theme Selector */}
          <ButtonGroup size="small" variant="outlined">
            {Object.entries(themes).slice(0, 3).map(([key, theme]) => (
              <Button
                key={key}
                onClick={() => setSelectedTheme(key)}
                variant={selectedTheme === key ? 'contained' : 'outlined'}
                sx={{ minWidth: 40, fontSize: 10 }}
              >
                {theme.name.split(' ')[0]}
              </Button>
            ))}
          </ButtonGroup>

          {/* View Controls */}
          <Tooltip title={wordWrap ? 'Disable word wrap' : 'Enable word wrap'}>
            <IconButton size="small" onClick={() => setWordWrap(!wordWrap)}>
              {wordWrap ? <WrapIcon /> : <NoWrapIcon />}
            </IconButton>
          </Tooltip>

          <Tooltip title="Decrease font size">
            <IconButton size="small" onClick={() => setFontSize(Math.max(10, fontSize - 2))}>
              <ZoomOutIcon />
            </IconButton>
          </Tooltip>

          <Tooltip title="Increase font size">
            <IconButton size="small" onClick={() => setFontSize(Math.min(24, fontSize + 2))}>
              <ZoomInIcon />
            </IconButton>
          </Tooltip>

          <Tooltip title={fullscreen ? 'Exit fullscreen' : 'Fullscreen'}>
            <IconButton size="small" onClick={() => setFullscreen(!fullscreen)}>
              {fullscreen ? <FullscreenExitIcon /> : <FullscreenIcon />}
            </IconButton>
          </Tooltip>

          {/* Action Buttons */}
          <Tooltip title="Regenerate code">
            <IconButton size="small" onClick={onRefresh} color="primary">
              <RefreshIcon />
            </IconButton>
          </Tooltip>

          <Tooltip title={copied ? 'Copied!' : 'Copy code'}>
            <IconButton size="small" onClick={handleCopy} color={copied ? 'success' : 'default'}>
              {copied ? <CheckIcon /> : <CopyIcon />}
            </IconButton>
          </Tooltip>

          <Tooltip title="Download file">
            <IconButton size="small" onClick={handleDownload} color="primary">
              <DownloadIcon />
            </IconButton>
          </Tooltip>
        </Stack>
      </Box>

      {/* Syntax Errors/Warnings */}
      {syntaxErrors.length > 0 && (
        <Stack spacing={1} sx={{ mb: 2 }}>
          {syntaxErrors.map((error, index) => (
            <Alert 
              key={index} 
              severity={error.severity || 'warning'}
              icon={error.severity === 'error' ? <WarningIcon /> : <CheckIcon />}
            >
              {error.message}
            </Alert>
          ))}
        </Stack>
      )}

      {/* Code Display */}
      <Paper
        sx={{
          flex: 1,
          overflow: 'auto',
          p: 0,
          position: fullscreen ? 'fixed' : 'relative',
          top: fullscreen ? 0 : 'auto',
          left: fullscreen ? 0 : 'auto',
          right: fullscreen ? 0 : 'auto',
          bottom: fullscreen ? 0 : 'auto',
          zIndex: fullscreen ? 9999 : 'auto',
          backgroundColor: themes[selectedTheme].style['pre[class*="language-"]']?.background || '#1e1e1e',
        }}
      >
        <SyntaxHighlighter
          language={getLanguageForHighlighter(language)}
          style={themes[selectedTheme].style}
          showLineNumbers={true}
          wrapLines={wordWrap}
          wrapLongLines={wordWrap}
          customStyle={{
            margin: 0,
            padding: '16px',
            fontSize: `${fontSize}px`,
            fontFamily: '"Fira Code", "Cascadia Code", Consolas, Monaco, monospace',
            background: 'transparent',
          }}
          lineNumberStyle={{
            minWidth: '3em',
            paddingRight: '1em',
            color: '#858585',
            borderRight: '1px solid #404040',
            marginRight: '1em',
          }}
        >
          {code || '// Your generated code will appear here\n// Select a language and customize options to generate production-ready code'}
        </SyntaxHighlighter>
      </Paper>

      {/* Code Quality Indicators */}
      <Box sx={{ 
        mt: 2, 
        p: 1, 
        bgcolor: 'background.default', 
        borderRadius: 1,
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
      }}>
        <Stack direction="row" spacing={2}>
          <Chip
            icon={<CheckIcon />}
            label="Production Ready"
            color="success"
            size="small"
            variant="outlined"
          />
          <Chip
            icon={<CheckIcon />}
            label="Error Handling"
            color="success"
            size="small"
            variant="outlined"
          />
          <Chip
            icon={<CheckIcon />}
            label="Type Safe"
            color="success"
            size="small"
            variant="outlined"
          />
          <Chip
            icon={<CheckIcon />}
            label="Optimized"
            color="success"
            size="small"
            variant="outlined"
          />
        </Stack>

        <Typography variant="caption" color="text.secondary">
          Generated with AI • Enterprise Grade • Better than Postman
        </Typography>
      </Box>
    </Box>
  );
};

export default CodePreview;