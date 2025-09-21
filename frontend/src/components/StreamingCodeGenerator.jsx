import React, { useState, useEffect, useRef } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { useTheme } from '../contexts/ThemeContext';
import {
  Box,
  VStack,
  HStack,
  Input,
  Button,
  Select,
  Textarea,
  Text,
  Progress,
  Badge,
  Alert,
  AlertIcon,
  Flex,
  IconButton,
  Tooltip,
  useClipboard,
  Divider,
  Card,
  CardHeader,
  CardBody,
  Heading,
  Code
} from '@chakra-ui/react';
import {
  PlayIcon,
  StopIcon,
  ClipboardDocumentIcon,
  SparklesIcon,
  CodeBracketIcon,
  DocumentTextIcon,
  BeakerIcon
} from '@heroicons/react/24/outline';

const StreamingCodeGenerator = () => {
  const { user } = useAuth();
  const { currentTheme } = useTheme();
  const wsRef = useRef(null);
  const [isConnected, setIsConnected] = useState(false);

  // Form state
  const [description, setDescription] = useState('');
  const [language, setLanguage] = useState('python');
  const [codeType, setCodeType] = useState('utility_function');

  // Generation state
  const [isGenerating, setIsGenerating] = useState(false);
  const [progress, setProgress] = useState(0);
  const [currentStep, setCurrentStep] = useState('');
  const [generatedCode, setGeneratedCode] = useState('');
  const [documentation, setDocumentation] = useState('');
  const [testCode, setTestCode] = useState('');
  const [qualityScore, setQualityScore] = useState(null);
  const [securityScore, setSecurityScore] = useState(null);
  const [dependencies, setDependencies] = useState([]);

  // Error state
  const [error, setError] = useState('');

  // Clipboard functionality
  const { onCopy: copyCode, hasCopied: codeCopied } = useClipboard(generatedCode);
  const { onCopy: copyTest, hasCopied: testCopied } = useClipboard(testCode);
  const { onCopy: copyDocs, hasCopied: docsCopied } = useClipboard(documentation);

  const languages = [
    { value: 'python', label: 'Python' },
    { value: 'javascript', label: 'JavaScript' },
    { value: 'typescript', label: 'TypeScript' },
    { value: 'java', label: 'Java' },
    { value: 'go', label: 'Go' },
    { value: 'rust', label: 'Rust' },
    { value: 'csharp', label: 'C#' },
    { value: 'php', label: 'PHP' }
  ];

  const codeTypes = [
    { value: 'utility_function', label: 'Utility Function' },
    { value: 'class_definition', label: 'Class Definition' },
    { value: 'api_endpoint', label: 'API Endpoint' },
    { value: 'data_structure', label: 'Data Structure' },
    { value: 'algorithm', label: 'Algorithm' },
    { value: 'test_suite', label: 'Test Suite' },
    { value: 'configuration', label: 'Configuration' },
    { value: 'microservice', label: 'Microservice' }
  ];

  const progressSteps = {
    'analyzing_requirements': { label: 'Analyzing Requirements', progress: 20 },
    'generating_structure': { label: 'Generating Structure', progress: 40 },
    'adding_business_logic': { label: 'Adding Business Logic', progress: 60 },
    'adding_error_handling': { label: 'Adding Error Handling', progress: 80 },
    'finalizing_code': { label: 'Finalizing Code', progress: 100 }
  };

  // WebSocket connection
  useEffect(() => {
    const connectWebSocket = () => {
      const wsUrl = `ws://localhost:8000/ws/ai?user_id=${user?.id || 'anonymous'}`;
      wsRef.current = new WebSocket(wsUrl);

      wsRef.current.onopen = () => {
        console.log('🔗 WebSocket connected for streaming code generation');
        setIsConnected(true);
        setError('');
      };

      wsRef.current.onmessage = (event) => {
        try {
          const message = JSON.parse(event.data);
          handleWebSocketMessage(message);
        } catch (err) {
          console.error('Failed to parse WebSocket message:', err);
        }
      };

      wsRef.current.onclose = () => {
        console.log('🔌 WebSocket disconnected');
        setIsConnected(false);
        setIsGenerating(false);
      };

      wsRef.current.onerror = (error) => {
        console.error('WebSocket error:', error);
        setError('Connection error. Please try again.');
        setIsGenerating(false);
      };
    };

    if (user) {
      connectWebSocket();
    }

    return () => {
      if (wsRef.current) {
        wsRef.current.close();
      }
    };
  }, [user]);

  const handleWebSocketMessage = (message) => {
    switch (message.type) {
      case 'connection_established':
        console.log('✅ Code generation WebSocket ready');
        break;

      case 'code_generation_started':
        setIsGenerating(true);
        setProgress(0);
        setCurrentStep('Starting code generation...');
        setError('');
        clearResults();
        break;

      case 'code_generation_progress':
        const step = message.data;
        const stepInfo = progressSteps[step.step];
        if (stepInfo) {
          setProgress(stepInfo.progress);
          setCurrentStep(stepInfo.label);
        }
        break;

      case 'code_generation_complete':
        const result = message.data;
        setGeneratedCode(result.code || '');
        setDocumentation(result.documentation || '');
        setTestCode(result.test_code || '');
        setQualityScore(result.quality_score);
        setSecurityScore(result.security_score);
        setDependencies(result.dependencies || []);
        setIsGenerating(false);
        setProgress(100);
        setCurrentStep('Code generation completed!');
        break;

      case 'error':
        setError(message.data.error || 'An error occurred during code generation');
        setIsGenerating(false);
        setProgress(0);
        setCurrentStep('');
        break;

      default:
        console.log('Unknown message type:', message.type);
    }
  };

  const clearResults = () => {
    setGeneratedCode('');
    setDocumentation('');
    setTestCode('');
    setQualityScore(null);
    setSecurityScore(null);
    setDependencies([]);
  };

  const handleGenerateCode = () => {
    if (!isConnected || !wsRef.current || !description.trim()) {
      setError('Please enter a description and ensure connection is active');
      return;
    }

    const message = {
      type: 'code_generation_request',
      data: {
        description: description.trim(),
        language,
        code_type: codeType
      },
      id: Date.now().toString()
    };

    wsRef.current.send(JSON.stringify(message));
  };

  const handleStopGeneration = () => {
    if (wsRef.current && isGenerating) {
      wsRef.current.close();
      setIsGenerating(false);
      setProgress(0);
      setCurrentStep('Generation stopped');
    }
  };

  const getScoreColor = (score) => {
    if (score >= 8) return 'green';
    if (score >= 6) return 'yellow';
    return 'red';
  };

  return (
    <Box
      minH="100vh"
      bg={currentTheme.colors.background}
      color={currentTheme.colors.text}
      p={6}
    >
      <VStack spacing={6} maxW="6xl" mx="auto">
        {/* Header */}
        <Flex align="center" gap={3}>
          <SparklesIcon className="w-8 h-8" />
          <Heading size="lg">Streaming Code Generator</Heading>
          <Badge colorScheme={isConnected ? 'green' : 'red'}>
            {isConnected ? 'Connected' : 'Disconnected'}
          </Badge>
        </Flex>

        {/* Error Alert */}
        {error && (
          <Alert status="error">
            <AlertIcon />
            {error}
          </Alert>
        )}

        {/* Input Form */}
        <Card w="full">
          <CardHeader>
            <Heading size="md">Code Generation Request</Heading>
          </CardHeader>
          <CardBody>
            <VStack spacing={4}>
              <Textarea
                placeholder="Describe the code you want to generate (e.g., 'Create a function that validates email addresses')"
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                size="lg"
                minH="120px"
                resize="vertical"
              />

              <HStack w="full" spacing={4}>
                <Box flex={1}>
                  <Text mb={2} fontWeight="semibold">Language</Text>
                  <Select value={language} onChange={(e) => setLanguage(e.target.value)}>
                    {languages.map(lang => (
                      <option key={lang.value} value={lang.value}>
                        {lang.label}
                      </option>
                    ))}
                  </Select>
                </Box>

                <Box flex={1}>
                  <Text mb={2} fontWeight="semibold">Code Type</Text>
                  <Select value={codeType} onChange={(e) => setCodeType(e.target.value)}>
                    {codeTypes.map(type => (
                      <option key={type.value} value={type.value}>
                        {type.label}
                      </option>
                    ))}
                  </Select>
                </Box>
              </HStack>

              <HStack>
                <Button
                  leftIcon={<PlayIcon className="w-4 h-4" />}
                  colorScheme="blue"
                  onClick={handleGenerateCode}
                  disabled={!isConnected || isGenerating || !description.trim()}
                  isLoading={isGenerating}
                  loadingText="Generating..."
                >
                  Generate Code
                </Button>

                {isGenerating && (
                  <Button
                    leftIcon={<StopIcon className="w-4 h-4" />}
                    colorScheme="red"
                    variant="outline"
                    onClick={handleStopGeneration}
                  >
                    Stop
                  </Button>
                )}
              </HStack>
            </VStack>
          </CardBody>
        </Card>

        {/* Progress */}
        {isGenerating && (
          <Card w="full">
            <CardBody>
              <VStack spacing={3}>
                <Text fontWeight="semibold">{currentStep}</Text>
                <Progress value={progress} w="full" colorScheme="blue" hasStripe isAnimated />
                <Text fontSize="sm" color={currentTheme.colors.textSecondary}>
                  {progress}% complete
                </Text>
              </VStack>
            </CardBody>
          </Card>
        )}

        {/* Results */}
        {generatedCode && (
          <VStack spacing={6} w="full">
            {/* Quality Metrics */}
            <Card w="full">
              <CardHeader>
                <Heading size="md">Quality Metrics</Heading>
              </CardHeader>
              <CardBody>
                <HStack spacing={6}>
                  {qualityScore !== null && (
                    <VStack>
                      <Text fontSize="sm" color={currentTheme.colors.textSecondary}>Quality Score</Text>
                      <Badge colorScheme={getScoreColor(qualityScore)} fontSize="lg" px={3} py={1}>
                        {qualityScore}/10
                      </Badge>
                    </VStack>
                  )}

                  {securityScore !== null && (
                    <VStack>
                      <Text fontSize="sm" color={currentTheme.colors.textSecondary}>Security Score</Text>
                      <Badge colorScheme={getScoreColor(securityScore)} fontSize="lg" px={3} py={1}>
                        {securityScore}/10
                      </Badge>
                    </VStack>
                  )}

                  {dependencies.length > 0 && (
                    <VStack align="start">
                      <Text fontSize="sm" color={currentTheme.colors.textSecondary}>Dependencies</Text>
                      <HStack wrap="wrap">
                        {dependencies.slice(0, 5).map((dep, index) => (
                          <Badge key={index} colorScheme="purple">{dep}</Badge>
                        ))}
                        {dependencies.length > 5 && (
                          <Badge colorScheme="gray">+{dependencies.length - 5} more</Badge>
                        )}
                      </HStack>
                    </VStack>
                  )}
                </HStack>
              </CardBody>
            </Card>

            {/* Generated Code */}
            <Card w="full">
              <CardHeader>
                <HStack justify="space-between">
                  <HStack>
                    <CodeBracketIcon className="w-5 h-5" />
                    <Heading size="md">Generated Code</Heading>
                  </HStack>
                  <Tooltip label={codeCopied ? "Copied!" : "Copy code"}>
                    <IconButton
                      icon={<ClipboardDocumentIcon className="w-4 h-4" />}
                      size="sm"
                      onClick={copyCode}
                      colorScheme={codeCopied ? "green" : "gray"}
                    />
                  </Tooltip>
                </HStack>
              </CardHeader>
              <CardBody>
                <Box
                  as="pre"
                  bg={currentTheme.colors.surface}
                  p={4}
                  borderRadius="md"
                  overflow="auto"
                  maxH="400px"
                  fontSize="sm"
                  fontFamily="monospace"
                >
                  <Code>{generatedCode}</Code>
                </Box>
              </CardBody>
            </Card>

            {/* Documentation */}
            {documentation && (
              <Card w="full">
                <CardHeader>
                  <HStack justify="space-between">
                    <HStack>
                      <DocumentTextIcon className="w-5 h-5" />
                      <Heading size="md">Documentation</Heading>
                    </HStack>
                    <Tooltip label={docsCopied ? "Copied!" : "Copy documentation"}>
                      <IconButton
                        icon={<ClipboardDocumentIcon className="w-4 h-4" />}
                        size="sm"
                        onClick={copyDocs}
                        colorScheme={docsCopied ? "green" : "gray"}
                      />
                    </Tooltip>
                  </HStack>
                </CardHeader>
                <CardBody>
                  <Box
                    as="pre"
                    bg={currentTheme.colors.surface}
                    p={4}
                    borderRadius="md"
                    overflow="auto"
                    maxH="300px"
                    fontSize="sm"
                    whiteSpace="pre-wrap"
                  >
                    {documentation}
                  </Box>
                </CardBody>
              </Card>
            )}

            {/* Test Code */}
            {testCode && (
              <Card w="full">
                <CardHeader>
                  <HStack justify="space-between">
                    <HStack>
                      <BeakerIcon className="w-5 h-5" />
                      <Heading size="md">Test Code</Heading>
                    </HStack>
                    <Tooltip label={testCopied ? "Copied!" : "Copy test code"}>
                      <IconButton
                        icon={<ClipboardDocumentIcon className="w-4 h-4" />}
                        size="sm"
                        onClick={copyTest}
                        colorScheme={testCopied ? "green" : "gray"}
                      />
                    </Tooltip>
                  </HStack>
                </CardHeader>
                <CardBody>
                  <Box
                    as="pre"
                    bg={currentTheme.colors.surface}
                    p={4}
                    borderRadius="md"
                    overflow="auto"
                    maxH="300px"
                    fontSize="sm"
                    fontFamily="monospace"
                  >
                    <Code>{testCode}</Code>
                  </Box>
                </CardBody>
              </Card>
            )}
          </VStack>
        )}
      </VStack>
    </Box>
  );
};

export default StreamingCodeGenerator;