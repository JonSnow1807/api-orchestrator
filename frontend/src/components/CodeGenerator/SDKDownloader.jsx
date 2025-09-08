import React, { useState } from 'react';
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  Box,
  Typography,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
  Checkbox,
  Chip,
  Alert,
  LinearProgress,
  Stack,
  Paper,
  IconButton,
  Tooltip,
  Divider,
} from '@mui/material';
import {
  Download as DownloadIcon,
  Folder as FolderIcon,
  InsertDriveFile as FileIcon,
  Code as CodeIcon,
  Description as DocsIcon,
  BugReport as TestIcon,
  CloudDownload as CloudIcon,
  GitHub as GitHubIcon,
  Check as CheckIcon,
  Close as CloseIcon,
  Archive as ZipIcon,
} from '@mui/icons-material';
import JSZip from 'jszip';
import { saveAs } from 'file-saver';

const SDKDownloader = ({
  open,
  onClose,
  code,
  packageFiles,
  documentation,
  tests,
  language,
  library,
  options,
}) => {
  const [selectedFiles, setSelectedFiles] = useState({
    mainCode: true,
    packageFile: true,
    readme: true,
    tests: true,
    dockerfile: true,
    ciConfig: true,
    envExample: true,
    gitignore: true,
    license: true,
    contributing: true,
  });
  const [downloading, setDownloading] = useState(false);
  const [downloadProgress, setDownloadProgress] = useState(0);

  const getFileExtension = () => {
    const extensions = {
      javascript: 'js',
      typescript: 'ts',
      python: 'py',
      java: 'java',
      csharp: 'cs',
      go: 'go',
      ruby: 'rb',
      php: 'php',
      rust: 'rs',
      kotlin: 'kt',
      swift: 'swift',
    };
    return extensions[language] || 'txt';
  };

  const generateEnvExample = () => {
    return `# API Configuration
API_BASE_URL=https://api.example.com
API_KEY=your_api_key_here
API_SECRET=your_secret_here

# Environment
ENVIRONMENT=development
DEBUG=false

# Timeouts and Retries
TIMEOUT=30000
MAX_RETRIES=3
RETRY_DELAY=1000

# Logging
LOG_LEVEL=info
LOG_FORMAT=json

# Rate Limiting
RATE_LIMIT_MAX_REQUESTS=100
RATE_LIMIT_WINDOW_MS=60000

# Cache
CACHE_TTL=300
CACHE_MAX_SIZE=100

# Monitoring
ENABLE_MONITORING=true
METRICS_PORT=9090`;
  };

  const generateGitignore = () => {
    const common = `# Environment variables
.env
.env.local
.env.*.local

# IDE
.vscode/
.idea/
*.iml

# OS
.DS_Store
Thumbs.db

# Logs
logs/
*.log

# Testing
coverage/
.nyc_output/

# Build outputs
dist/
build/
out/
`;

    const languageSpecific = {
      javascript: `node_modules/
package-lock.json
yarn.lock`,
      python: `__pycache__/
*.py[cod]
*$py.class
.Python
venv/
env/
.pytest_cache/`,
      java: `target/
*.class
*.jar
.gradle/`,
      go: `vendor/
go.sum`,
    };

    return common + '\n' + (languageSpecific[language] || '');
  };

  const generateDockerfile = () => {
    const dockerfiles = {
      javascript: `FROM node:18-alpine

WORKDIR /app

COPY package*.json ./
RUN npm ci --only=production

COPY . .

EXPOSE 3000

CMD ["node", "index.js"]`,
      python: `FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["python", "main.py"]`,
      java: `FROM openjdk:17-alpine

WORKDIR /app

COPY pom.xml .
COPY src ./src

RUN mvn clean package

EXPOSE 8080

CMD ["java", "-jar", "target/app.jar"]`,
      go: `FROM golang:1.21-alpine AS builder

WORKDIR /app

COPY go.mod go.sum ./
RUN go mod download

COPY . .
RUN go build -o main .

FROM alpine:latest
RUN apk --no-cache add ca-certificates
WORKDIR /root/

COPY --from=builder /app/main .

EXPOSE 8080

CMD ["./main"]`,
    };

    return dockerfiles[language] || `FROM alpine:latest\n\nWORKDIR /app\n\nCOPY . .\n\nCMD ["./app"]`;
  };

  const generateCIConfig = () => {
    return `name: CI/CD Pipeline

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main ]

jobs:
  test:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Setup ${language}
      uses: actions/setup-${language === 'javascript' ? 'node' : language}@v3
      with:
        ${language === 'javascript' ? 'node-version' : language + '-version'}: 'latest'
    
    - name: Install dependencies
      run: |
        ${language === 'javascript' ? 'npm ci' : 
          language === 'python' ? 'pip install -r requirements.txt' :
          language === 'java' ? 'mvn install' :
          language === 'go' ? 'go mod download' :
          'echo "Install dependencies"'}
    
    - name: Run tests
      run: |
        ${language === 'javascript' ? 'npm test' :
          language === 'python' ? 'pytest' :
          language === 'java' ? 'mvn test' :
          language === 'go' ? 'go test ./...' :
          'echo "Run tests"'}
    
    - name: Build
      run: |
        ${language === 'javascript' ? 'npm run build' :
          language === 'python' ? 'python setup.py build' :
          language === 'java' ? 'mvn package' :
          language === 'go' ? 'go build' :
          'echo "Build"'}
    
    - name: Upload artifacts
      uses: actions/upload-artifact@v3
      with:
        name: build-artifacts
        path: |
          dist/
          build/
          target/

  deploy:
    needs: test
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main'
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Deploy to production
      run: echo "Deploy to production environment"`;
  };

  const generateLicense = () => {
    return `MIT License

Copyright (c) ${new Date().getFullYear()} Your Company

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.`;
  };

  const generateContributing = () => {
    return `# Contributing to API Client SDK

We love your input! We want to make contributing to this project as easy and transparent as possible.

## Development Process

1. Fork the repo and create your branch from \`main\`.
2. If you've added code that should be tested, add tests.
3. If you've changed APIs, update the documentation.
4. Ensure the test suite passes.
5. Make sure your code lints.
6. Issue that pull request!

## Code Style

- Use consistent indentation (2 spaces for JS/TS, 4 spaces for Python)
- Follow language-specific conventions
- Write clear, self-documenting code
- Add comments for complex logic

## Testing

- Write unit tests for new functionality
- Ensure all tests pass before submitting PR
- Aim for >80% code coverage

## License

By contributing, you agree that your contributions will be licensed under the MIT License.`;
  };

  const handleToggleFile = (file) => {
    setSelectedFiles(prev => ({
      ...prev,
      [file]: !prev[file]
    }));
  };

  const handleSelectAll = () => {
    const allSelected = Object.values(selectedFiles).every(v => v);
    const newSelection = {};
    Object.keys(selectedFiles).forEach(key => {
      newSelection[key] = !allSelected;
    });
    setSelectedFiles(newSelection);
  };

  const handleDownload = async () => {
    setDownloading(true);
    setDownloadProgress(0);

    const zip = new JSZip();
    const projectName = `api-client-${language}-${library}`;
    const folder = zip.folder(projectName);

    let filesAdded = 0;
    const totalFiles = Object.values(selectedFiles).filter(v => v).length;

    // Add selected files
    if (selectedFiles.mainCode && code) {
      folder.file(`client.${getFileExtension()}`, code);
      filesAdded++;
      setDownloadProgress((filesAdded / totalFiles) * 100);
    }

    if (selectedFiles.packageFile && packageFiles) {
      Object.entries(packageFiles).forEach(([filename, content]) => {
        folder.file(filename, content);
      });
      filesAdded++;
      setDownloadProgress((filesAdded / totalFiles) * 100);
    }

    if (selectedFiles.readme) {
      folder.file('README.md', documentation || generateReadme());
      filesAdded++;
      setDownloadProgress((filesAdded / totalFiles) * 100);
    }

    if (selectedFiles.tests && tests) {
      folder.file(`test.${getFileExtension()}`, tests);
      filesAdded++;
      setDownloadProgress((filesAdded / totalFiles) * 100);
    }

    if (selectedFiles.dockerfile && options.includeDocker) {
      folder.file('Dockerfile', generateDockerfile());
      folder.file('.dockerignore', 'node_modules\n.env\n.git');
      filesAdded++;
      setDownloadProgress((filesAdded / totalFiles) * 100);
    }

    if (selectedFiles.ciConfig && options.includeCI) {
      const githubFolder = folder.folder('.github').folder('workflows');
      githubFolder.file('ci.yml', generateCIConfig());
      filesAdded++;
      setDownloadProgress((filesAdded / totalFiles) * 100);
    }

    if (selectedFiles.envExample) {
      folder.file('.env.example', generateEnvExample());
      filesAdded++;
      setDownloadProgress((filesAdded / totalFiles) * 100);
    }

    if (selectedFiles.gitignore) {
      folder.file('.gitignore', generateGitignore());
      filesAdded++;
      setDownloadProgress((filesAdded / totalFiles) * 100);
    }

    if (selectedFiles.license) {
      folder.file('LICENSE', generateLicense());
      filesAdded++;
      setDownloadProgress((filesAdded / totalFiles) * 100);
    }

    if (selectedFiles.contributing) {
      folder.file('CONTRIBUTING.md', generateContributing());
      filesAdded++;
      setDownloadProgress((filesAdded / totalFiles) * 100);
    }

    // Generate zip file
    const content = await zip.generateAsync({ type: 'blob' });
    saveAs(content, `${projectName}.zip`);

    setDownloading(false);
    setDownloadProgress(100);
    
    // Close dialog after short delay
    setTimeout(() => {
      onClose();
      setDownloadProgress(0);
    }, 1000);
  };

  const generateReadme = () => {
    return `# API Client SDK for ${language}

Generated with StreamAPI - The Enterprise API Platform

## Installation

\`\`\`bash
# Install dependencies
${language === 'javascript' ? 'npm install' :
  language === 'python' ? 'pip install -r requirements.txt' :
  language === 'java' ? 'mvn install' :
  language === 'go' ? 'go mod download' :
  'install dependencies'}
\`\`\`

## Usage

See the generated client code for usage examples.

## Configuration

Copy \`.env.example\` to \`.env\` and update with your API credentials.

## Testing

Run tests with appropriate command for your language.

## License

MIT`;
  };

  const fileList = [
    { key: 'mainCode', name: `client.${getFileExtension()}`, icon: <CodeIcon />, size: '15.7 KB' },
    { key: 'packageFile', name: Object.keys(packageFiles || {})[0] || 'package.json', icon: <FileIcon />, size: '2.1 KB' },
    { key: 'readme', name: 'README.md', icon: <DocsIcon />, size: '8.3 KB' },
    { key: 'tests', name: `test.${getFileExtension()}`, icon: <TestIcon />, size: '5.4 KB' },
    { key: 'dockerfile', name: 'Dockerfile', icon: <CloudIcon />, size: '1.2 KB', optional: !options.includeDocker },
    { key: 'ciConfig', name: '.github/workflows/ci.yml', icon: <GitHubIcon />, size: '2.8 KB', optional: !options.includeCI },
    { key: 'envExample', name: '.env.example', icon: <FileIcon />, size: '0.5 KB' },
    { key: 'gitignore', name: '.gitignore', icon: <FileIcon />, size: '0.3 KB' },
    { key: 'license', name: 'LICENSE', icon: <FileIcon />, size: '1.1 KB' },
    { key: 'contributing', name: 'CONTRIBUTING.md', icon: <DocsIcon />, size: '0.9 KB' },
  ];

  const selectedCount = Object.values(selectedFiles).filter(v => v).length;
  const totalSize = fileList
    .filter(f => selectedFiles[f.key] && !f.optional)
    .reduce((acc, f) => acc + parseFloat(f.size), 0)
    .toFixed(1);

  return (
    <Dialog open={open} onClose={onClose} maxWidth="md" fullWidth>
      <DialogTitle>
        <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
          <Typography variant="h6" sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <ZipIcon />
            Download SDK Package
          </Typography>
          <IconButton onClick={onClose} size="small">
            <CloseIcon />
          </IconButton>
        </Box>
      </DialogTitle>
      
      <DialogContent>
        <Alert severity="success" sx={{ mb: 2 }}>
          Your production-ready SDK for {language} using {library} is ready to download!
        </Alert>

        <Paper sx={{ p: 2, mb: 2, bgcolor: 'background.default' }}>
          <Typography variant="subtitle2" sx={{ mb: 1 }}>
            Package Contents ({selectedCount} files, ~{totalSize} KB)
          </Typography>
          
          <Button
            size="small"
            onClick={handleSelectAll}
            sx={{ mb: 1 }}
          >
            {Object.values(selectedFiles).every(v => v) ? 'Deselect All' : 'Select All'}
          </Button>

          <List dense>
            {fileList.filter(f => !f.optional).map((file) => (
              <ListItem key={file.key}>
                <ListItemIcon>
                  <Checkbox
                    checked={selectedFiles[file.key]}
                    onChange={() => handleToggleFile(file.key)}
                  />
                </ListItemIcon>
                <ListItemIcon sx={{ minWidth: 32 }}>
                  {file.icon}
                </ListItemIcon>
                <ListItemText
                  primary={file.name}
                  secondary={file.size}
                  primaryTypographyProps={{ fontFamily: 'monospace' }}
                />
              </ListItem>
            ))}
          </List>
        </Paper>

        <Stack direction="row" spacing={1} sx={{ mb: 2 }}>
          <Chip label={`${language} SDK`} color="primary" />
          <Chip label={library} variant="outlined" />
          <Chip label="Production Ready" color="success" variant="outlined" />
          <Chip label="Fully Documented" color="info" variant="outlined" />
        </Stack>

        {downloading && (
          <Box sx={{ mb: 2 }}>
            <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
              Preparing download... {Math.round(downloadProgress)}%
            </Typography>
            <LinearProgress variant="determinate" value={downloadProgress} />
          </Box>
        )}
      </DialogContent>

      <DialogActions>
        <Button onClick={onClose}>Cancel</Button>
        <Button
          variant="contained"
          startIcon={downloading ? null : <DownloadIcon />}
          onClick={handleDownload}
          disabled={downloading || selectedCount === 0}
          sx={{
            background: downloading ? undefined : 'linear-gradient(45deg, #2196F3 30%, #21CBF3 90%)',
          }}
        >
          {downloading ? 'Downloading...' : `Download SDK (${totalSize} KB)`}
        </Button>
      </DialogActions>
    </Dialog>
  );
};

export default SDKDownloader;