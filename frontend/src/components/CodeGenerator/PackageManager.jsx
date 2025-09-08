import React from 'react';
import {
  Box,
  Paper,
  Typography,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
  Chip,
  IconButton,
  Tooltip,
  Divider,
  Alert,
  Button,
  Stack,
} from '@mui/material';
import {
  Folder as FolderIcon,
  InsertDriveFile as FileIcon,
  ContentCopy as CopyIcon,
  Terminal as TerminalIcon,
  CloudDownload as DownloadIcon,
  CheckCircle as CheckIcon,
  Info as InfoIcon,
} from '@mui/icons-material';
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { vscDarkPlus } from 'react-syntax-highlighter/dist/esm/styles/prism';

const PackageManager = ({ language, library, packageFiles }) => {
  const getPackageInfo = () => {
    const packageManagers = {
      javascript: {
        file: 'package.json',
        install: 'npm install',
        run: 'npm start',
        test: 'npm test',
        build: 'npm run build',
        manager: 'npm',
        icon: '📦',
      },
      typescript: {
        file: 'package.json',
        install: 'npm install',
        run: 'npm start',
        test: 'npm test',
        build: 'npm run build',
        manager: 'npm',
        icon: '📦',
      },
      python: {
        file: 'requirements.txt',
        install: 'pip install -r requirements.txt',
        run: 'python main.py',
        test: 'pytest',
        build: 'python setup.py build',
        manager: 'pip',
        icon: '🐍',
      },
      java: {
        file: 'pom.xml',
        install: 'mvn install',
        run: 'mvn exec:java',
        test: 'mvn test',
        build: 'mvn package',
        manager: 'Maven',
        icon: '☕',
      },
      csharp: {
        file: 'project.csproj',
        install: 'dotnet restore',
        run: 'dotnet run',
        test: 'dotnet test',
        build: 'dotnet build',
        manager: 'NuGet',
        icon: '🔷',
      },
      go: {
        file: 'go.mod',
        install: 'go get',
        run: 'go run .',
        test: 'go test',
        build: 'go build',
        manager: 'Go Modules',
        icon: '🐹',
      },
      ruby: {
        file: 'Gemfile',
        install: 'bundle install',
        run: 'ruby main.rb',
        test: 'rspec',
        build: 'gem build',
        manager: 'Bundler',
        icon: '💎',
      },
      php: {
        file: 'composer.json',
        install: 'composer install',
        run: 'php index.php',
        test: 'phpunit',
        build: 'composer build',
        manager: 'Composer',
        icon: '🐘',
      },
      rust: {
        file: 'Cargo.toml',
        install: 'cargo build',
        run: 'cargo run',
        test: 'cargo test',
        build: 'cargo build --release',
        manager: 'Cargo',
        icon: '🦀',
      },
      kotlin: {
        file: 'build.gradle.kts',
        install: 'gradle build',
        run: 'gradle run',
        test: 'gradle test',
        build: 'gradle jar',
        manager: 'Gradle',
        icon: '🟣',
      },
      swift: {
        file: 'Package.swift',
        install: 'swift build',
        run: 'swift run',
        test: 'swift test',
        build: 'swift build -c release',
        manager: 'Swift Package Manager',
        icon: '🦉',
      },
    };

    return packageManagers[language] || {
      file: 'dependencies.txt',
      install: 'install dependencies',
      run: 'run application',
      test: 'run tests',
      build: 'build project',
      manager: 'Package Manager',
      icon: '📄',
    };
  };

  const getDependencies = () => {
    const deps = {
      javascript: {
        axios: ['axios@^1.6.0', 'dotenv@^16.3.1', 'winston@^3.11.0'],
        fetch: ['node-fetch@^3.3.0', 'dotenv@^16.3.1'],
        'node-fetch': ['node-fetch@^3.3.0', 'dotenv@^16.3.1'],
        got: ['got@^13.0.0', 'dotenv@^16.3.1'],
        superagent: ['superagent@^8.1.0', 'dotenv@^16.3.1'],
      },
      typescript: {
        axios: ['axios@^1.6.0', '@types/node@^20.0.0', 'typescript@^5.0.0'],
        fetch: ['node-fetch@^3.3.0', '@types/node-fetch@^3.0.0', 'typescript@^5.0.0'],
      },
      python: {
        requests: ['requests>=2.31.0', 'python-dotenv>=1.0.0', 'retry>=0.9.2'],
        aiohttp: ['aiohttp>=3.9.0', 'python-dotenv>=1.0.0', 'aiofiles>=23.0.0'],
        httpx: ['httpx>=0.25.0', 'python-dotenv>=1.0.0', 'anyio>=4.0.0'],
      },
      java: {
        okhttp: ['com.squareup.okhttp3:okhttp:4.12.0', 'com.google.code.gson:gson:2.10.1'],
        retrofit: ['com.squareup.retrofit2:retrofit:2.9.0', 'com.squareup.retrofit2:converter-gson:2.9.0'],
      },
      go: {
        'net/http': ['github.com/joho/godotenv v1.5.1'],
        resty: ['github.com/go-resty/resty/v2 v2.11.0', 'github.com/joho/godotenv v1.5.1'],
      },
    };

    return deps[language]?.[library] || ['standard-library'];
  };

  const packageInfo = getPackageInfo();
  const dependencies = getDependencies();

  const handleCopyCommand = (command) => {
    navigator.clipboard.writeText(command);
  };

  const generatedFiles = [
    { name: packageInfo.file, type: 'config', size: '2.1 KB' },
    { name: 'README.md', type: 'docs', size: '8.3 KB' },
    { name: '.env.example', type: 'config', size: '0.5 KB' },
    { name: '.gitignore', type: 'config', size: '0.3 KB' },
    { name: 'Dockerfile', type: 'docker', size: '1.2 KB' },
    { name: '.github/workflows/ci.yml', type: 'ci', size: '2.8 KB' },
    { name: `client.${language === 'javascript' ? 'js' : language === 'python' ? 'py' : language}`, type: 'code', size: '15.7 KB' },
    { name: `test.${language === 'javascript' ? 'spec.js' : language === 'python' ? 'py' : language}`, type: 'test', size: '5.4 KB' },
  ];

  return (
    <Box>
      {/* Package Manager Info */}
      <Paper sx={{ p: 2, mb: 2, bgcolor: 'background.default' }}>
        <Typography variant="subtitle2" sx={{ mb: 1, display: 'flex', alignItems: 'center', gap: 1 }}>
          <span>{packageInfo.icon}</span>
          {packageInfo.manager}
        </Typography>
        
        <Alert severity="info" icon={<InfoIcon />} sx={{ mb: 2 }}>
          Using {library} library for {language}
        </Alert>

        {/* Dependencies List */}
        <Typography variant="body2" sx={{ mb: 1, fontWeight: 500 }}>
          Dependencies:
        </Typography>
        <Box sx={{ mb: 2 }}>
          {dependencies.map((dep, index) => (
            <Chip
              key={index}
              label={dep}
              size="small"
              sx={{ mr: 0.5, mb: 0.5, fontFamily: 'monospace', fontSize: '0.75rem' }}
            />
          ))}
        </Box>

        {/* Commands */}
        <Stack spacing={1}>
          {['install', 'run', 'test', 'build'].map((cmd) => (
            <Box
              key={cmd}
              sx={{
                display: 'flex',
                alignItems: 'center',
                p: 1,
                bgcolor: 'background.paper',
                borderRadius: 1,
                border: '1px solid',
                borderColor: 'divider',
              }}
            >
              <TerminalIcon sx={{ mr: 1, color: 'text.secondary', fontSize: 20 }} />
              <Typography
                variant="body2"
                sx={{ flex: 1, fontFamily: 'monospace', fontSize: '0.85rem' }}
              >
                {packageInfo[cmd]}
              </Typography>
              <Tooltip title="Copy command">
                <IconButton size="small" onClick={() => handleCopyCommand(packageInfo[cmd])}>
                  <CopyIcon sx={{ fontSize: 16 }} />
                </IconButton>
              </Tooltip>
            </Box>
          ))}
        </Stack>
      </Paper>

      {/* Generated Files */}
      <Paper sx={{ p: 2, bgcolor: 'background.default' }}>
        <Typography variant="subtitle2" sx={{ mb: 1, display: 'flex', alignItems: 'center', gap: 1 }}>
          <FolderIcon />
          Project Structure
        </Typography>
        
        <List dense>
          {generatedFiles.map((file, index) => (
            <ListItem key={index} sx={{ py: 0.5 }}>
              <ListItemIcon sx={{ minWidth: 32 }}>
                <FileIcon sx={{ fontSize: 18, color: 
                  file.type === 'code' ? 'primary.main' :
                  file.type === 'test' ? 'success.main' :
                  file.type === 'config' ? 'warning.main' :
                  file.type === 'docker' ? 'info.main' :
                  file.type === 'ci' ? 'secondary.main' :
                  'text.secondary'
                }} />
              </ListItemIcon>
              <ListItemText
                primary={file.name}
                secondary={file.size}
                primaryTypographyProps={{ variant: 'body2', fontFamily: 'monospace' }}
                secondaryTypographyProps={{ variant: 'caption' }}
              />
              <Chip
                label={file.type}
                size="small"
                variant="outlined"
                sx={{ fontSize: '0.65rem', height: 20 }}
              />
            </ListItem>
          ))}
        </List>

        <Divider sx={{ my: 2 }} />

        {/* Quick Setup Guide */}
        <Box>
          <Typography variant="subtitle2" sx={{ mb: 1 }}>
            Quick Setup
          </Typography>
          <Paper sx={{ p: 1, bgcolor: 'background.paper' }}>
            <SyntaxHighlighter language="bash" style={vscDarkPlus} customStyle={{ fontSize: '0.8rem', margin: 0 }}>
{`# 1. Install dependencies
${packageInfo.install}

# 2. Configure environment
cp .env.example .env
# Edit .env with your API credentials

# 3. Run the application
${packageInfo.run}

# 4. Run tests
${packageInfo.test}`}
            </SyntaxHighlighter>
          </Paper>
        </Box>

        {/* Features */}
        <Box sx={{ mt: 2 }}>
          <Stack direction="row" spacing={1} flexWrap="wrap">
            {['Production Ready', 'Fully Typed', 'Error Handling', 'Retries', 'Logging'].map((feature) => (
              <Chip
                key={feature}
                label={feature}
                size="small"
                icon={<CheckIcon />}
                color="success"
                variant="outlined"
                sx={{ mb: 1 }}
              />
            ))}
          </Stack>
        </Box>
      </Paper>
    </Box>
  );
};

export default PackageManager;