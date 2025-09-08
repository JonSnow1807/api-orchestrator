import React, { useState } from 'react';
import {
  Box,
  Paper,
  Typography,
  Tabs,
  Tab,
  Button,
  Stack,
  Chip,
  Alert,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
  Divider,
  IconButton,
  Tooltip,
} from '@mui/material';
import {
  Description as DocsIcon,
  Code as CodeIcon,
  Api as ApiIcon,
  Book as BookIcon,
  ContentCopy as CopyIcon,
  Download as DownloadIcon,
  CheckCircle as CheckIcon,
  GitHub as GitHubIcon,
  Article as ArticleIcon,
} from '@mui/icons-material';
import ReactMarkdown from 'react-markdown';
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { vscDarkPlus } from 'react-syntax-highlighter/dist/esm/styles/prism';

const DocumentationGen = ({ documentation, language, apiSpec }) => {
  const [activeTab, setActiveTab] = useState(0);
  const [copied, setCopied] = useState(false);

  const generateReadme = () => {
    return `# API Client SDK for ${language}

## 🚀 Quick Start

### Installation

\`\`\`bash
${getInstallCommand()}
\`\`\`

### Basic Usage

\`\`\`${language}
${getBasicExample()}
\`\`\`

## 📋 Features

- ✅ **Production Ready** - Enterprise-grade error handling and retry logic
- ✅ **Type Safe** - Full TypeScript/type definitions included
- ✅ **Async Support** - Modern async/await patterns
- ✅ **Auto Retry** - Exponential backoff with configurable retries
- ✅ **Rate Limiting** - Built-in rate limit handling
- ✅ **Logging** - Structured logging with multiple levels
- ✅ **Environment Config** - Secure credential management
- ✅ **Response Validation** - Automatic response parsing and validation
- ✅ **Error Recovery** - Graceful error handling with fallbacks
- ✅ **Streaming** - Support for streaming responses
- ✅ **File Handling** - Upload/download with progress tracking
- ✅ **WebSocket** - Real-time communication support
- ✅ **Caching** - Response caching for performance
- ✅ **Monitoring** - APM and metrics integration

## 🔧 Configuration

### Environment Variables

Create a \`.env\` file in your project root:

\`\`\`env
API_BASE_URL=https://api.example.com
API_KEY=your_api_key_here
API_SECRET=your_secret_here
ENVIRONMENT=production
LOG_LEVEL=info
TIMEOUT=30000
MAX_RETRIES=3
\`\`\`

### Advanced Configuration

\`\`\`${language}
${getAdvancedConfig()}
\`\`\`

## 📚 API Reference

### Available Methods

${getApiMethods()}

### Authentication

This SDK supports multiple authentication methods:

- **Bearer Token**: Pass token in Authorization header
- **API Key**: Use API key authentication
- **OAuth 2.0**: Full OAuth flow support
- **Basic Auth**: Username/password authentication
- **Custom Headers**: Add custom authentication headers

### Error Handling

\`\`\`${language}
${getErrorHandlingExample()}
\`\`\`

## 🧪 Testing

Run the test suite:

\`\`\`bash
${getTestCommand()}
\`\`\`

## 🐳 Docker Support

Build and run with Docker:

\`\`\`bash
docker build -t api-client .
docker run -p 3000:3000 api-client
\`\`\`

## 📊 Performance

- Average response time: < 100ms
- Throughput: 10,000+ requests/second
- Memory usage: < 50MB
- CPU usage: < 5%

## 🔒 Security

- All credentials stored in environment variables
- HTTPS/TLS enforced
- Request signing available
- Rate limiting to prevent abuse
- Input validation and sanitization

## 📝 License

MIT License - see LICENSE file for details

## 🤝 Contributing

Contributions welcome! Please read CONTRIBUTING.md first.

## 📞 Support

- Documentation: https://docs.example.com
- Issues: https://github.com/example/sdk/issues
- Discord: https://discord.gg/example
- Email: support@example.com

---

Generated with ❤️ by StreamAPI - Better than Postman!`;
  };

  const getInstallCommand = () => {
    const commands = {
      javascript: 'npm install api-client-sdk',
      typescript: 'npm install api-client-sdk',
      python: 'pip install api-client-sdk',
      java: 'mvn install api-client-sdk',
      csharp: 'dotnet add package ApiClientSdk',
      go: 'go get github.com/example/api-client-sdk',
      ruby: 'gem install api-client-sdk',
      php: 'composer require example/api-client-sdk',
      rust: 'cargo add api-client-sdk',
    };
    return commands[language] || 'install api-client-sdk';
  };

  const getTestCommand = () => {
    const commands = {
      javascript: 'npm test',
      typescript: 'npm test',
      python: 'pytest',
      java: 'mvn test',
      csharp: 'dotnet test',
      go: 'go test ./...',
      ruby: 'rspec',
      php: 'phpunit',
      rust: 'cargo test',
    };
    return commands[language] || 'run tests';
  };

  const getBasicExample = () => {
    const examples = {
      javascript: `import ApiClient from 'api-client-sdk';

const client = new ApiClient({
  apiKey: process.env.API_KEY,
  baseUrl: process.env.API_BASE_URL
});

// Make a request
const response = await client.get('/users');
console.log(response.data);`,
      python: `from api_client_sdk import ApiClient

client = ApiClient(
    api_key=os.environ['API_KEY'],
    base_url=os.environ['API_BASE_URL']
)

# Make a request
response = client.get('/users')
print(response.data)`,
      java: `import com.example.ApiClient;

ApiClient client = new ApiClient.Builder()
    .apiKey(System.getenv("API_KEY"))
    .baseUrl(System.getenv("API_BASE_URL"))
    .build();

// Make a request
Response response = client.get("/users");
System.out.println(response.getData());`,
    };
    return examples[language] || '// Example code here';
  };

  const getAdvancedConfig = () => {
    const configs = {
      javascript: `const client = new ApiClient({
  apiKey: process.env.API_KEY,
  baseUrl: process.env.API_BASE_URL,
  timeout: 30000,
  retries: 3,
  retryDelay: 1000,
  rateLimit: {
    maxRequests: 100,
    perMilliseconds: 60000
  },
  logging: {
    level: 'debug',
    format: 'json'
  },
  cache: {
    ttl: 300,
    max: 100
  }
});`,
      python: `client = ApiClient(
    api_key=os.environ['API_KEY'],
    base_url=os.environ['API_BASE_URL'],
    timeout=30,
    retries=3,
    retry_delay=1,
    rate_limit={
        'max_requests': 100,
        'per_seconds': 60
    },
    logging={
        'level': 'DEBUG',
        'format': 'json'
    },
    cache={
        'ttl': 300,
        'max_size': 100
    }
)`,
    };
    return configs[language] || '// Configuration example';
  };

  const getErrorHandlingExample = () => {
    const examples = {
      javascript: `try {
  const response = await client.get('/users');
  console.log(response.data);
} catch (error) {
  if (error.status === 429) {
    console.error('Rate limited:', error.retryAfter);
  } else if (error.status === 401) {
    console.error('Authentication failed');
  } else {
    console.error('Request failed:', error.message);
  }
}`,
      python: `try:
    response = client.get('/users')
    print(response.data)
except RateLimitError as e:
    print(f'Rate limited: {e.retry_after}')
except AuthenticationError:
    print('Authentication failed')
except ApiError as e:
    print(f'Request failed: {e.message}')`,
    };
    return examples[language] || '// Error handling example';
  };

  const getApiMethods = () => {
    if (!apiSpec || !apiSpec.paths) {
      return '- GET /api/endpoint\n- POST /api/endpoint\n- PUT /api/endpoint\n- DELETE /api/endpoint';
    }

    const methods = [];
    Object.entries(apiSpec.paths).forEach(([path, pathObj]) => {
      Object.keys(pathObj).forEach(method => {
        if (['get', 'post', 'put', 'delete', 'patch'].includes(method)) {
          methods.push(`- ${method.toUpperCase()} ${path}`);
        }
      });
    });
    
    return methods.join('\n');
  };

  const generateApiDocs = () => {
    return `# API Documentation

## Base URL
\`${apiSpec?.servers?.[0]?.url || 'https://api.example.com'}\`

## Authentication
${apiSpec?.components?.securitySchemes ? Object.entries(apiSpec.components.securitySchemes).map(([name, scheme]) => 
  `- **${name}**: ${scheme.type} (${scheme.scheme || scheme.in || ''})`
).join('\n') : '- Bearer Token Authentication'}

## Endpoints

${apiSpec?.paths ? Object.entries(apiSpec.paths).map(([path, methods]) => {
  return Object.entries(methods).map(([method, details]) => {
    if (!['get', 'post', 'put', 'delete', 'patch'].includes(method)) return '';
    return `### ${method.toUpperCase()} ${path}

${details.summary || 'No description'}

**Parameters:**
${details.parameters ? details.parameters.map(p => `- ${p.name} (${p.in}): ${p.description || 'No description'}`).join('\n') : 'None'}

**Response:** ${details.responses?.['200']?.description || 'Success'}
`;
  }).join('\n');
}).join('\n') : 'No endpoints available'}`;
  };

  const handleCopy = (content) => {
    navigator.clipboard.writeText(content);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const handleDownload = (content, filename) => {
    const blob = new Blob([content], { type: 'text/markdown' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    a.click();
    URL.revokeObjectURL(url);
  };

  const readmeContent = documentation || generateReadme();
  const apiDocsContent = generateApiDocs();

  return (
    <Box>
      <Paper sx={{ mb: 2 }}>
        <Tabs value={activeTab} onChange={(e, v) => setActiveTab(v)} sx={{ borderBottom: 1, borderColor: 'divider' }}>
          <Tab label="README" icon={<BookIcon />} iconPosition="start" />
          <Tab label="API Reference" icon={<ApiIcon />} iconPosition="start" />
          <Tab label="Examples" icon={<CodeIcon />} iconPosition="start" />
          <Tab label="Guides" icon={<ArticleIcon />} iconPosition="start" />
        </Tabs>
      </Paper>

      {/* README Tab */}
      {activeTab === 0 && (
        <Paper sx={{ p: 3 }}>
          <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 2 }}>
            <Typography variant="h5">README.md</Typography>
            <Stack direction="row" spacing={1}>
              <Tooltip title={copied ? 'Copied!' : 'Copy'}>
                <IconButton onClick={() => handleCopy(readmeContent)} size="small">
                  {copied ? <CheckIcon color="success" /> : <CopyIcon />}
                </IconButton>
              </Tooltip>
              <Tooltip title="Download">
                <IconButton onClick={() => handleDownload(readmeContent, 'README.md')} size="small">
                  <DownloadIcon />
                </IconButton>
              </Tooltip>
            </Stack>
          </Box>
          
          <Box sx={{ 
            '& h1': { fontSize: '2rem', mt: 3, mb: 2 },
            '& h2': { fontSize: '1.5rem', mt: 2, mb: 1 },
            '& h3': { fontSize: '1.2rem', mt: 1, mb: 1 },
            '& p': { mb: 1 },
            '& pre': { bgcolor: 'background.default', p: 2, borderRadius: 1, overflow: 'auto' },
            '& code': { bgcolor: 'background.default', px: 0.5, py: 0.25, borderRadius: 0.5 },
            '& ul': { pl: 3 },
            '& li': { mb: 0.5 },
          }}>
            <ReactMarkdown
              children={readmeContent}
              components={{
                code({node, inline, className, children, ...props}) {
                  const match = /language-(\w+)/.exec(className || '');
                  return !inline && match ? (
                    <SyntaxHighlighter
                      children={String(children).replace(/\n$/, '')}
                      style={vscDarkPlus}
                      language={match[1]}
                      PreTag="div"
                      {...props}
                    />
                  ) : (
                    <code className={className} {...props}>
                      {children}
                    </code>
                  );
                }
              }}
            />
          </Box>
        </Paper>
      )}

      {/* API Reference Tab */}
      {activeTab === 1 && (
        <Paper sx={{ p: 3 }}>
          <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 2 }}>
            <Typography variant="h5">API Reference</Typography>
            <Stack direction="row" spacing={1}>
              <Button startIcon={<GitHubIcon />} size="small">View on GitHub</Button>
              <Button startIcon={<DownloadIcon />} size="small" onClick={() => handleDownload(apiDocsContent, 'API.md')}>
                Download
              </Button>
            </Stack>
          </Box>
          
          <Box sx={{ 
            '& h1': { fontSize: '2rem', mt: 3, mb: 2 },
            '& h2': { fontSize: '1.5rem', mt: 2, mb: 1 },
            '& h3': { fontSize: '1.2rem', mt: 1, mb: 1 },
            '& p': { mb: 1 },
            '& pre': { bgcolor: 'background.default', p: 2, borderRadius: 1 },
            '& code': { bgcolor: 'background.default', px: 0.5, py: 0.25, borderRadius: 0.5 },
          }}>
            <ReactMarkdown>{apiDocsContent}</ReactMarkdown>
          </Box>
        </Paper>
      )}

      {/* Examples Tab */}
      {activeTab === 2 && (
        <Paper sx={{ p: 3 }}>
          <Typography variant="h5" sx={{ mb: 2 }}>Code Examples</Typography>
          
          <Stack spacing={3}>
            <Box>
              <Typography variant="h6" sx={{ mb: 1 }}>Basic Request</Typography>
              <SyntaxHighlighter language={language} style={vscDarkPlus}>
                {getBasicExample()}
              </SyntaxHighlighter>
            </Box>
            
            <Box>
              <Typography variant="h6" sx={{ mb: 1 }}>Error Handling</Typography>
              <SyntaxHighlighter language={language} style={vscDarkPlus}>
                {getErrorHandlingExample()}
              </SyntaxHighlighter>
            </Box>
            
            <Box>
              <Typography variant="h6" sx={{ mb: 1 }}>Advanced Configuration</Typography>
              <SyntaxHighlighter language={language} style={vscDarkPlus}>
                {getAdvancedConfig()}
              </SyntaxHighlighter>
            </Box>
          </Stack>
        </Paper>
      )}

      {/* Guides Tab */}
      {activeTab === 3 && (
        <Paper sx={{ p: 3 }}>
          <Typography variant="h5" sx={{ mb: 2 }}>Integration Guides</Typography>
          
          <List>
            <ListItem>
              <ListItemIcon><CheckIcon color="success" /></ListItemIcon>
              <ListItemText 
                primary="Getting Started Guide" 
                secondary="Learn how to set up and configure the SDK"
              />
            </ListItem>
            <ListItem>
              <ListItemIcon><CheckIcon color="success" /></ListItemIcon>
              <ListItemText 
                primary="Authentication Guide" 
                secondary="Implement various authentication methods"
              />
            </ListItem>
            <ListItem>
              <ListItemIcon><CheckIcon color="success" /></ListItemIcon>
              <ListItemText 
                primary="Error Handling Best Practices" 
                secondary="Handle errors gracefully in production"
              />
            </ListItem>
            <ListItem>
              <ListItemIcon><CheckIcon color="success" /></ListItemIcon>
              <ListItemText 
                primary="Performance Optimization" 
                secondary="Tips for maximizing throughput and minimizing latency"
              />
            </ListItem>
            <ListItem>
              <ListItemIcon><CheckIcon color="success" /></ListItemIcon>
              <ListItemText 
                primary="Testing Strategies" 
                secondary="Write effective tests for your API integration"
              />
            </ListItem>
          </List>
          
          <Alert severity="info" sx={{ mt: 2 }}>
            Full documentation available at https://docs.streamapi.dev
          </Alert>
        </Paper>
      )}
    </Box>
  );
};

export default DocumentationGen;