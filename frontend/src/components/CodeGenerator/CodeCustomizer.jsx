import React from 'react';
import {
  Box,
  FormControl,
  FormControlLabel,
  FormLabel,
  RadioGroup,
  Radio,
  Checkbox,
  Switch,
  Select,
  MenuItem,
  TextField,
  Slider,
  Typography,
  Chip,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  Grid,
  Button,
  Stack,
  Tooltip,
  Paper,
  Divider,
  Alert,
} from '@mui/material';
import {
  ExpandMore as ExpandMoreIcon,
  Security as SecurityIcon,
  Speed as SpeedIcon,
  CloudUpload as CloudIcon,
  Build as BuildIcon,
  Code as CodeIcon,
  BugReport as TestIcon,
  Description as DocsIcon,
  Timer as TimerIcon,
  Sync as SyncIcon,
  Lock as LockIcon,
  Analytics as AnalyticsIcon,
  Business as EnterpriseIcon,
  AutoAwesome as AIIcon,
  CheckCircle as CheckIcon,
} from '@mui/icons-material';

const CodeCustomizer = ({ options, onOptionsChange, language }) => {
  const handleChange = (key, value) => {
    onOptionsChange({
      ...options,
      [key]: value,
    });
  };

  const handleComplianceChange = (compliance) => {
    const current = options.compliance || [];
    const updated = current.includes(compliance)
      ? current.filter(c => c !== compliance)
      : [...current, compliance];
    handleChange('compliance', updated);
  };

  const presetConfigs = {
    minimal: {
      name: 'Minimal',
      description: 'Basic request only',
      options: {
        async: false,
        errorHandling: 'basic',
        authType: 'none',
        includeTests: false,
        includeDocs: false,
        includeDocker: false,
        includeCI: false,
        logging: 'none',
        retryPolicy: 'none',
        timeout: 5000,
        responseValidation: false,
        typeDefinitions: false,
        environmentConfig: false,
        securityBestPractices: false,
        rateLimit: false,
      },
    },
    standard: {
      name: 'Standard',
      description: 'Production basics',
      options: {
        async: true,
        errorHandling: 'standard',
        authType: 'bearer',
        includeTests: true,
        includeDocs: true,
        includeDocker: false,
        includeCI: false,
        logging: 'basic',
        retryPolicy: 'linear',
        timeout: 30000,
        responseValidation: true,
        typeDefinitions: true,
        environmentConfig: true,
        securityBestPractices: true,
        rateLimit: false,
      },
    },
    enterprise: {
      name: 'Enterprise',
      description: 'Full production suite',
      options: {
        async: true,
        errorHandling: 'advanced',
        authType: 'oauth2',
        includeTests: true,
        includeDocs: true,
        includeDocker: true,
        includeCI: true,
        logging: 'production',
        retryPolicy: 'exponential',
        timeout: 60000,
        responseValidation: true,
        typeDefinitions: true,
        environmentConfig: true,
        securityBestPractices: true,
        rateLimit: true,
        streaming: true,
        monitoring: true,
        compliance: ['GDPR', 'HIPAA', 'SOC2'],
      },
    },
  };

  const applyPreset = (preset) => {
    onOptionsChange({
      ...options,
      ...presetConfigs[preset].options,
    });
  };

  return (
    <Box>
      {/* Preset Configurations */}
      <Paper sx={{ p: 2, mb: 2, bgcolor: 'background.default' }}>
        <Typography variant="subtitle2" sx={{ mb: 1, display: 'flex', alignItems: 'center', gap: 1 }}>
          <AIIcon color="primary" />
          Quick Presets
        </Typography>
        <Grid container spacing={1}>
          {Object.entries(presetConfigs).map(([key, preset]) => (
            <Grid item xs={12} sm={4} key={key}>
              <Button
                fullWidth
                variant="outlined"
                size="small"
                onClick={() => applyPreset(key)}
                sx={{ 
                  flexDirection: 'column', 
                  py: 1,
                  borderColor: key === 'enterprise' ? 'primary.main' : 'divider',
                  borderWidth: key === 'enterprise' ? 2 : 1,
                }}
              >
                <Typography variant="subtitle2">{preset.name}</Typography>
                <Typography variant="caption" color="text.secondary">
                  {preset.description}
                </Typography>
                {key === 'enterprise' && (
                  <Chip label="RECOMMENDED" size="small" color="primary" sx={{ mt: 0.5 }} />
                )}
              </Button>
            </Grid>
          ))}
        </Grid>
      </Paper>

      {/* Detailed Options */}
      <Accordion defaultExpanded>
        <AccordionSummary expandIcon={<ExpandMoreIcon />}>
          <Typography sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <CodeIcon />
            Code Generation
          </Typography>
        </AccordionSummary>
        <AccordionDetails>
          <Stack spacing={2}>
            <FormControl>
              <FormLabel>Execution Model</FormLabel>
              <RadioGroup
                value={options.async ? 'async' : 'sync'}
                onChange={(e) => handleChange('async', e.target.value === 'async')}
                row
              >
                <FormControlLabel value="sync" control={<Radio />} label="Synchronous" />
                <FormControlLabel value="async" control={<Radio />} label="Async/Await" />
              </RadioGroup>
            </FormControl>

            <FormControl>
              <FormLabel>Error Handling</FormLabel>
              <Select
                value={options.errorHandling}
                onChange={(e) => handleChange('errorHandling', e.target.value)}
                size="small"
              >
                <MenuItem value="none">None</MenuItem>
                <MenuItem value="basic">Basic Try/Catch</MenuItem>
                <MenuItem value="standard">Standard with Logging</MenuItem>
                <MenuItem value="advanced">Advanced with Retry & Recovery</MenuItem>
              </Select>
            </FormControl>

            <FormControlLabel
              control={
                <Switch
                  checked={options.typeDefinitions}
                  onChange={(e) => handleChange('typeDefinitions', e.target.checked)}
                />
              }
              label="Include Type Definitions (TypeScript/Flow)"
            />

            <FormControlLabel
              control={
                <Switch
                  checked={options.responseValidation}
                  onChange={(e) => handleChange('responseValidation', e.target.checked)}
                />
              }
              label="Response Validation & Parsing"
            />
          </Stack>
        </AccordionDetails>
      </Accordion>

      <Accordion>
        <AccordionSummary expandIcon={<ExpandMoreIcon />}>
          <Typography sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <SecurityIcon />
            Security & Authentication
          </Typography>
        </AccordionSummary>
        <AccordionDetails>
          <Stack spacing={2}>
            <FormControl>
              <FormLabel>Authentication Type</FormLabel>
              <Select
                value={options.authType}
                onChange={(e) => handleChange('authType', e.target.value)}
                size="small"
              >
                <MenuItem value="none">None</MenuItem>
                <MenuItem value="bearer">Bearer Token</MenuItem>
                <MenuItem value="basic">Basic Auth</MenuItem>
                <MenuItem value="apikey">API Key</MenuItem>
                <MenuItem value="oauth2">OAuth 2.0</MenuItem>
                <MenuItem value="jwt">JWT</MenuItem>
                <MenuItem value="aws">AWS Signature</MenuItem>
                <MenuItem value="custom">Custom Headers</MenuItem>
              </Select>
            </FormControl>

            <FormControlLabel
              control={
                <Switch
                  checked={options.securityBestPractices}
                  onChange={(e) => handleChange('securityBestPractices', e.target.checked)}
                />
              }
              label="Apply Security Best Practices"
            />

            <FormControlLabel
              control={
                <Switch
                  checked={options.environmentConfig}
                  onChange={(e) => handleChange('environmentConfig', e.target.checked)}
                />
              }
              label="Use Environment Variables for Secrets"
            />
          </Stack>
        </AccordionDetails>
      </Accordion>

      <Accordion>
        <AccordionSummary expandIcon={<ExpandMoreIcon />}>
          <Typography sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <SpeedIcon />
            Performance & Reliability
          </Typography>
        </AccordionSummary>
        <AccordionDetails>
          <Stack spacing={2}>
            <FormControl>
              <FormLabel>Retry Policy</FormLabel>
              <Select
                value={options.retryPolicy}
                onChange={(e) => handleChange('retryPolicy', e.target.value)}
                size="small"
              >
                <MenuItem value="none">No Retries</MenuItem>
                <MenuItem value="linear">Linear Backoff</MenuItem>
                <MenuItem value="exponential">Exponential Backoff</MenuItem>
                <MenuItem value="custom">Custom Strategy</MenuItem>
              </Select>
            </FormControl>

            <Box>
              <Typography gutterBottom>Timeout (ms): {options.timeout}</Typography>
              <Slider
                value={options.timeout}
                onChange={(e, v) => handleChange('timeout', v)}
                min={1000}
                max={120000}
                step={1000}
                marks={[
                  { value: 5000, label: '5s' },
                  { value: 30000, label: '30s' },
                  { value: 60000, label: '60s' },
                  { value: 120000, label: '120s' },
                ]}
              />
            </Box>

            <FormControlLabel
              control={
                <Switch
                  checked={options.rateLimit}
                  onChange={(e) => handleChange('rateLimit', e.target.checked)}
                />
              }
              label="Include Rate Limiting"
            />

            <FormControlLabel
              control={
                <Switch
                  checked={options.caching}
                  onChange={(e) => handleChange('caching', e.target.checked)}
                />
              }
              label="Response Caching"
            />

            <FormControlLabel
              control={
                <Switch
                  checked={options.compression}
                  onChange={(e) => handleChange('compression', e.target.checked)}
                />
              }
              label="Request/Response Compression"
            />
          </Stack>
        </AccordionDetails>
      </Accordion>

      <Accordion>
        <AccordionSummary expandIcon={<ExpandMoreIcon />}>
          <Typography sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <BuildIcon />
            DevOps & Deployment
          </Typography>
        </AccordionSummary>
        <AccordionDetails>
          <Stack spacing={2}>
            <FormControlLabel
              control={
                <Switch
                  checked={options.includeDocker}
                  onChange={(e) => handleChange('includeDocker', e.target.checked)}
                />
              }
              label="Generate Dockerfile"
            />

            <FormControlLabel
              control={
                <Switch
                  checked={options.includeCI}
                  onChange={(e) => handleChange('includeCI', e.target.checked)}
                />
              }
              label="CI/CD Configuration (GitHub Actions, Jenkins)"
            />

            <FormControl>
              <FormLabel>Logging Level</FormLabel>
              <Select
                value={options.logging}
                onChange={(e) => handleChange('logging', e.target.value)}
                size="small"
              >
                <MenuItem value="none">None</MenuItem>
                <MenuItem value="basic">Basic</MenuItem>
                <MenuItem value="debug">Debug</MenuItem>
                <MenuItem value="production">Production (Structured)</MenuItem>
              </Select>
            </FormControl>

            <FormControlLabel
              control={
                <Switch
                  checked={options.monitoring}
                  onChange={(e) => handleChange('monitoring', e.target.checked)}
                />
              }
              label="Include Monitoring (APM, Metrics)"
            />
          </Stack>
        </AccordionDetails>
      </Accordion>

      <Accordion>
        <AccordionSummary expandIcon={<ExpandMoreIcon />}>
          <Typography sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <TestIcon />
            Testing & Documentation
          </Typography>
        </AccordionSummary>
        <AccordionDetails>
          <Stack spacing={2}>
            <FormControlLabel
              control={
                <Switch
                  checked={options.includeTests}
                  onChange={(e) => handleChange('includeTests', e.target.checked)}
                />
              }
              label="Generate Unit Tests"
            />

            <FormControlLabel
              control={
                <Switch
                  checked={options.includeDocs}
                  onChange={(e) => handleChange('includeDocs', e.target.checked)}
                />
              }
              label="Generate Documentation"
            />

            {options.includeTests && (
              <Alert severity="info" icon={<CheckIcon />}>
                Tests will be generated using {
                  language === 'javascript' ? 'Jest' :
                  language === 'python' ? 'pytest' :
                  language === 'java' ? 'JUnit' :
                  language === 'csharp' ? 'xUnit' :
                  language === 'go' ? 'testing package' :
                  'the standard testing framework'
                }
              </Alert>
            )}
          </Stack>
        </AccordionDetails>
      </Accordion>

      <Accordion>
        <AccordionSummary expandIcon={<ExpandMoreIcon />}>
          <Typography sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <EnterpriseIcon />
            Enterprise Features
          </Typography>
        </AccordionSummary>
        <AccordionDetails>
          <Stack spacing={2}>
            <FormControlLabel
              control={
                <Switch
                  checked={options.streaming}
                  onChange={(e) => handleChange('streaming', e.target.checked)}
                />
              }
              label="Streaming Response Support"
            />

            <FormControlLabel
              control={
                <Switch
                  checked={options.websocket}
                  onChange={(e) => handleChange('websocket', e.target.checked)}
                />
              }
              label="WebSocket Support"
            />

            <FormControlLabel
              control={
                <Switch
                  checked={options.fileHandling}
                  onChange={(e) => handleChange('fileHandling', e.target.checked)}
                />
              }
              label="File Upload/Download Handling"
            />

            <Box>
              <FormLabel>Compliance Standards</FormLabel>
              <Stack direction="row" spacing={1} sx={{ mt: 1, flexWrap: 'wrap' }}>
                {['GDPR', 'HIPAA', 'SOC2', 'PCI-DSS', 'ISO27001'].map((compliance) => (
                  <Chip
                    key={compliance}
                    label={compliance}
                    onClick={() => handleComplianceChange(compliance)}
                    color={(options.compliance || []).includes(compliance) ? 'primary' : 'default'}
                    variant={(options.compliance || []).includes(compliance) ? 'filled' : 'outlined'}
                    sx={{ mb: 1 }}
                  />
                ))}
              </Stack>
            </Box>
          </Stack>
        </AccordionDetails>
      </Accordion>

      {/* Summary of Selected Options */}
      <Paper sx={{ p: 2, mt: 2, bgcolor: 'success.light', color: 'success.contrastText' }}>
        <Typography variant="subtitle2" sx={{ mb: 1 }}>
          Configuration Summary
        </Typography>
        <Grid container spacing={1}>
          {Object.entries(options).filter(([_, value]) => value === true || (Array.isArray(value) && value.length > 0)).map(([key]) => (
            <Grid item key={key}>
              <Chip 
                label={key.replace(/([A-Z])/g, ' $1').trim()} 
                size="small" 
                sx={{ bgcolor: 'success.dark', color: 'white' }}
              />
            </Grid>
          ))}
        </Grid>
      </Paper>
    </Box>
  );
};

export default CodeCustomizer;