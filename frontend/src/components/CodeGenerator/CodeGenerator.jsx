import React, { useState, useEffect, useCallback } from 'react';
import {
  Box,
  Paper,
  Typography,
  Button,
  Grid,
  Alert,
  LinearProgress,
  Tabs,
  Tab,
  Chip,
  IconButton,
  Tooltip,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Snackbar,
  Badge,
  Divider,
  Stack,
} from '@mui/material';
import {
  Code as CodeIcon,
  Download as DownloadIcon,
  ContentCopy as CopyIcon,
  Settings as SettingsIcon,
  Star as StarIcon,
  StarBorder as StarBorderIcon,
  Search as SearchIcon,
  CloudDownload as CloudDownloadIcon,
  Description as DocsIcon,
  BugReport as TestIcon,
  Business as EnterpriseIcon,
  AutoAwesome as AIIcon,
  CheckCircle as CheckIcon,
  Warning as WarningIcon,
  Info as InfoIcon,
  GitHub as GitHubIcon,
  Folder as FolderIcon,
  Terminal as TerminalIcon,
} from '@mui/icons-material';
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { vscDarkPlus } from 'react-syntax-highlighter/dist/esm/styles/prism';
import LanguageSelector from './LanguageSelector';
import CodePreview from './CodePreview';
import CodeCustomizer from './CodeCustomizer';
import PackageManager from './PackageManager';
import DocumentationGen from './DocumentationGen';
import SDKDownloader from './SDKDownloader';
import { generateSDK } from '../../utils/codeGeneration';
import config from '../../config';

const CodeGenerator = ({ apiSpec, requestData, selectedEndpoint }) => {
  const [selectedLanguage, setSelectedLanguage] = useState('javascript');
  const [selectedLibrary, setSelectedLibrary] = useState('axios');
  const [generatedCode, setGeneratedCode] = useState('');
  const [packageFiles, setPackageFiles] = useState({});
  const [documentation, setDocumentation] = useState('');
  const [tests, setTests] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [activeTab, setActiveTab] = useState(0);
  const [favorites, setFavorites] = useState(() => {
    const saved = localStorage.getItem('codeGenFavorites');
    return saved ? JSON.parse(saved) : ['javascript', 'python', 'java'];
  });
  const [history, setHistory] = useState(() => {
    const saved = localStorage.getItem('codeGenHistory');
    return saved ? JSON.parse(saved) : [];
  });
  const [customOptions, setCustomOptions] = useState({
    async: true,
    errorHandling: 'advanced',
    authType: 'bearer',
    includeTests: true,
    includeDocs: true,
    includeDocker: false,
    includeCI: false,
    logging: 'production',
    retryPolicy: 'exponential',
    timeout: 30000,
    responseValidation: true,
    typeDefinitions: true,
    environmentConfig: true,
    securityBestPractices: true,
    rateLimit: true,
    streaming: false,
    websocket: false,
    fileHandling: false,
    caching: false,
    compression: true,
    monitoring: false,
    compliance: [],
  });
  const [showDownloadDialog, setShowDownloadDialog] = useState(false);
  const [snackbar, setSnackbar] = useState({ open: false, message: '', severity: 'success' });
  const [codeStats, setCodeStats] = useState({
    linesOfCode: 0,
    filesGenerated: 0,
    estimatedTime: '< 1 min',
    complexity: 'Medium',
  });

  // Generate code whenever parameters change
  useEffect(() => {
    if (apiSpec || requestData) {
      generateCode();
    }
  }, [selectedLanguage, selectedLibrary, customOptions, apiSpec, requestData]);

  // Update history
  useEffect(() => {
    if (selectedLanguage && !history.includes(selectedLanguage)) {
      const newHistory = [selectedLanguage, ...history.slice(0, 9)];
      setHistory(newHistory);
      localStorage.setItem('codeGenHistory', JSON.stringify(newHistory));
    }
  }, [selectedLanguage]);

  const generateCode = async () => {
    setLoading(true);
    setError(null);
    
    try {
      const response = await fetch(`${config.API_BASE_URL}/api/generate-code`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('token')}`,
        },
        body: JSON.stringify({
          apiSpec,
          requestData,
          selectedEndpoint,
          language: selectedLanguage,
          library: selectedLibrary,
          options: customOptions,
        }),
      });

      if (!response.ok) {
        throw new Error('Failed to generate code');
      }

      const data = await response.json();
      
      setGeneratedCode(data.code);
      setPackageFiles(data.packageFiles || {});
      setDocumentation(data.documentation || '');
      setTests(data.tests || '');
      setCodeStats({
        linesOfCode: data.code.split('\n').length,
        filesGenerated: Object.keys(data.packageFiles || {}).length + 2,
        estimatedTime: data.estimatedTime || '< 1 min',
        complexity: data.complexity || 'Medium',
      });
      
      // Show success notification for AI generation
      if (data.aiGenerated) {
        setSnackbar({
          open: true,
          message: 'AI-powered code generation completed successfully',
          severity: 'success',
        });
      }
    } catch (err) {
      console.error('Code generation error:', err);
      setError(err.message);
      
      // Fallback to local generation
      const fallbackCode = generateSDK(
        apiSpec || requestData,
        selectedLanguage,
        selectedLibrary,
        customOptions
      );
      
      setGeneratedCode(fallbackCode.code);
      setPackageFiles(fallbackCode.packageFiles || {});
      setDocumentation(fallbackCode.documentation || '');
      setTests(fallbackCode.tests || '');
      setCodeStats({
        linesOfCode: fallbackCode.code.split('\n').length,
        filesGenerated: Object.keys(fallbackCode.packageFiles || {}).length + 1,
        estimatedTime: '< 1 min',
        complexity: 'Medium',
      });
    } finally {
      setLoading(false);
    }
  };

  const handleCopyCode = () => {
    navigator.clipboard.writeText(generatedCode);
    setSnackbar({
      open: true,
      message: 'Code copied to clipboard',
      severity: 'success',
    });
  };

  const handleToggleFavorite = (language) => {
    const newFavorites = favorites.includes(language)
      ? favorites.filter(f => f !== language)
      : [...favorites, language];
    setFavorites(newFavorites);
    localStorage.setItem('codeGenFavorites', JSON.stringify(newFavorites));
  };

  const handleDownloadSDK = () => {
    setShowDownloadDialog(true);
  };

  const getLanguageIcon = (language) => {
    const icons = {
      javascript: '🟨',
      typescript: '🔷',
      python: '🐍',
      java: '☕',
      csharp: '🔵',
      go: '🐹',
      ruby: '💎',
      php: '🐘',
      swift: '🦉',
      kotlin: '🟣',
      rust: '🦀',
      cpp: '⚙️',
      dart: '🎯',
      scala: '🔴',
      elixir: '💧',
    };
    return icons[language] || '📝';
  };

  return (
    <Box sx={{ p: 3 }}>
      {/* Header with Stats */}
      <Paper sx={{ p: 3, mb: 3, background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)' }}>
        <Grid container spacing={3} alignItems="center">
          <Grid item xs={12} md={6}>
            <Typography variant="h4" sx={{ color: 'white', mb: 1, display: 'flex', alignItems: 'center', gap: 1 }}>
              <AIIcon sx={{ fontSize: 35 }} />
              Enterprise AI Code Generator
            </Typography>
            <Typography variant="body1" sx={{ color: 'rgba(255,255,255,0.9)' }}>
              Generate production-ready SDKs in 30+ languages with AI-powered intelligence
            </Typography>
          </Grid>
          <Grid item xs={12} md={6}>
            <Grid container spacing={2}>
              <Grid item xs={6} sm={3}>
                <Box sx={{ textAlign: 'center' }}>
                  <Typography variant="h4" sx={{ color: 'white' }}>
                    {codeStats.linesOfCode}
                  </Typography>
                  <Typography variant="caption" sx={{ color: 'rgba(255,255,255,0.8)' }}>
                    Lines of Code
                  </Typography>
                </Box>
              </Grid>
              <Grid item xs={6} sm={3}>
                <Box sx={{ textAlign: 'center' }}>
                  <Typography variant="h4" sx={{ color: 'white' }}>
                    {codeStats.filesGenerated}
                  </Typography>
                  <Typography variant="caption" sx={{ color: 'rgba(255,255,255,0.8)' }}>
                    Files Generated
                  </Typography>
                </Box>
              </Grid>
              <Grid item xs={6} sm={3}>
                <Box sx={{ textAlign: 'center' }}>
                  <Typography variant="h4" sx={{ color: 'white' }}>
                    30+
                  </Typography>
                  <Typography variant="caption" sx={{ color: 'rgba(255,255,255,0.8)' }}>
                    Languages
                  </Typography>
                </Box>
              </Grid>
              <Grid item xs={6} sm={3}>
                <Box sx={{ textAlign: 'center' }}>
                  <Chip
                    label={codeStats.complexity}
                    sx={{
                      backgroundColor: 'rgba(255,255,255,0.2)',
                      color: 'white',
                      mt: 1,
                    }}
                  />
                </Box>
              </Grid>
            </Grid>
          </Grid>
        </Grid>
      </Paper>

      {/* Main Content */}
      <Grid container spacing={3}>
        {/* Left Panel - Options */}
        <Grid item xs={12} md={4}>
          {/* Language Selector */}
          <Paper sx={{ p: 2, mb: 2 }}>
            <Typography variant="h6" sx={{ mb: 2, display: 'flex', alignItems: 'center', gap: 1 }}>
              <CodeIcon />
              Select Language & Library
            </Typography>
            <LanguageSelector
              selectedLanguage={selectedLanguage}
              selectedLibrary={selectedLibrary}
              onLanguageChange={setSelectedLanguage}
              onLibraryChange={setSelectedLibrary}
              favorites={favorites}
              onToggleFavorite={handleToggleFavorite}
              history={history}
            />
          </Paper>

          {/* Customization Options */}
          <Paper sx={{ p: 2, mb: 2 }}>
            <Typography variant="h6" sx={{ mb: 2, display: 'flex', alignItems: 'center', gap: 1 }}>
              <SettingsIcon />
              Customization Options
            </Typography>
            <CodeCustomizer
              options={customOptions}
              onOptionsChange={setCustomOptions}
              language={selectedLanguage}
            />
          </Paper>

          {/* Package Management */}
          <Paper sx={{ p: 2 }}>
            <Typography variant="h6" sx={{ mb: 2, display: 'flex', alignItems: 'center', gap: 1 }}>
              <FolderIcon />
              Package Management
            </Typography>
            <PackageManager
              language={selectedLanguage}
              library={selectedLibrary}
              packageFiles={packageFiles}
            />
          </Paper>
        </Grid>

        {/* Right Panel - Code Preview */}
        <Grid item xs={12} md={8}>
          <Paper sx={{ p: 2, height: '100%', minHeight: 600 }}>
            {/* Action Buttons */}
            <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
              <Tabs value={activeTab} onChange={(e, v) => setActiveTab(v)}>
                <Tab label="Code" icon={<CodeIcon />} iconPosition="start" />
                <Tab label="Documentation" icon={<DocsIcon />} iconPosition="start" />
                <Tab label="Tests" icon={<TestIcon />} iconPosition="start" />
                <Tab label="Package Files" icon={<FolderIcon />} iconPosition="start" />
              </Tabs>
              
              <Stack direction="row" spacing={1}>
                <Tooltip title="Copy Code">
                  <IconButton onClick={handleCopyCode} color="primary">
                    <CopyIcon />
                  </IconButton>
                </Tooltip>
                <Tooltip title="Download SDK">
                  <IconButton onClick={handleDownloadSDK} color="primary">
                    <CloudDownloadIcon />
                  </IconButton>
                </Tooltip>
                <Button
                  variant="contained"
                  startIcon={<DownloadIcon />}
                  onClick={handleDownloadSDK}
                  sx={{
                    background: 'linear-gradient(45deg, #2196F3 30%, #21CBF3 90%)',
                  }}
                >
                  Download Full SDK
                </Button>
              </Stack>
            </Box>

            <Divider sx={{ mb: 2 }} />

            {/* Loading State */}
            {loading && <LinearProgress sx={{ mb: 2 }} />}

            {/* Error State */}
            {error && (
              <Alert severity="warning" sx={{ mb: 2 }}>
                {error} - Using fallback generation
              </Alert>
            )}

            {/* Code Preview Tabs */}
            <Box sx={{ height: 'calc(100% - 120px)', overflow: 'auto' }}>
              {activeTab === 0 && (
                <CodePreview
                  code={generatedCode}
                  language={selectedLanguage}
                  library={selectedLibrary}
                />
              )}
              
              {activeTab === 1 && (
                <DocumentationGen
                  documentation={documentation}
                  language={selectedLanguage}
                  apiSpec={apiSpec}
                />
              )}
              
              {activeTab === 2 && (
                <Box>
                  <Typography variant="h6" sx={{ mb: 2 }}>
                    Generated Tests
                  </Typography>
                  <SyntaxHighlighter language={selectedLanguage} style={vscDarkPlus}>
                    {tests || '// Tests will be generated based on your API specification'}
                  </SyntaxHighlighter>
                </Box>
              )}
              
              {activeTab === 3 && (
                <Box>
                  <Typography variant="h6" sx={{ mb: 2 }}>
                    Package Files
                  </Typography>
                  {Object.entries(packageFiles).map(([filename, content]) => (
                    <Box key={filename} sx={{ mb: 3 }}>
                      <Typography variant="subtitle1" sx={{ mb: 1, fontFamily: 'monospace' }}>
                        {filename}
                      </Typography>
                      <SyntaxHighlighter 
                        language={filename.endsWith('.json') ? 'json' : 'yaml'} 
                        style={vscDarkPlus}
                      >
                        {content}
                      </SyntaxHighlighter>
                    </Box>
                  ))}
                </Box>
              )}
            </Box>
          </Paper>
        </Grid>
      </Grid>

      {/* Features Comparison Banner */}
      <Paper sx={{ p: 3, mt: 3, background: 'linear-gradient(135deg, #f093fb 0%, #f5576c 100%)' }}>
        <Typography variant="h5" sx={{ color: 'white', mb: 2 }}>
          Why StreamAPI Code Generation is Better Than Postman
        </Typography>
        <Grid container spacing={2}>
          {[
            { feature: '30+ Languages', ours: '✅', theirs: '❌ (20 only)' },
            { feature: 'Full SDKs', ours: '✅', theirs: '❌ (Snippets)' },
            { feature: 'AI-Powered', ours: '✅', theirs: '❌' },
            { feature: 'Package Files', ours: '✅', theirs: '❌' },
            { feature: 'Test Generation', ours: '✅', theirs: '❌' },
            { feature: 'Documentation', ours: '✅', theirs: '❌' },
            { feature: 'Enterprise Ready', ours: '✅', theirs: '❌' },
            { feature: 'Docker Support', ours: '✅', theirs: '❌' },
          ].map((item, index) => (
            <Grid item xs={6} sm={3} key={index}>
              <Box sx={{ textAlign: 'center', color: 'white' }}>
                <Typography variant="subtitle2">{item.feature}</Typography>
                <Typography variant="body2">
                  Us: {item.ours} | Them: {item.theirs}
                </Typography>
              </Box>
            </Grid>
          ))}
        </Grid>
      </Paper>

      {/* SDK Download Dialog */}
      <SDKDownloader
        open={showDownloadDialog}
        onClose={() => setShowDownloadDialog(false)}
        code={generatedCode}
        packageFiles={packageFiles}
        documentation={documentation}
        tests={tests}
        language={selectedLanguage}
        library={selectedLibrary}
        options={customOptions}
      />

      {/* Snackbar */}
      <Snackbar
        open={snackbar.open}
        autoHideDuration={6000}
        onClose={() => setSnackbar({ ...snackbar, open: false })}
      >
        <Alert severity={snackbar.severity} onClose={() => setSnackbar({ ...snackbar, open: false })}>
          {snackbar.message}
        </Alert>
      </Snackbar>
    </Box>
  );
};

export default CodeGenerator;