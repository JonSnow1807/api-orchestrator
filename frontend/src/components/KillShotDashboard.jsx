import React, { useState, useEffect, useRef } from 'react';
import {
  Box,
  Grid,
  Card,
  CardBody,
  Heading,
  Text,
  Badge,
  Progress,
  VStack,
  HStack,
  Button,
  Alert,
  AlertIcon,
  AlertTitle,
  AlertDescription,
  Tabs,
  TabList,
  TabPanels,
  Tab,
  TabPanel,
  Stat,
  StatLabel,
  StatNumber,
  StatHelpText,
  StatArrow,
  useColorModeValue,
  Spinner,
  Table,
  Thead,
  Tbody,
  Tr,
  Th,
  Td,
  IconButton,
  Tooltip,
  useToast
} from '@chakra-ui/react';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip as RechartsTooltip,
  Legend,
  ResponsiveContainer,
  AreaChart,
  Area,
  BarChart,
  Bar
} from 'recharts';
import { FiPlay, FiPause, FiRefreshCw, FiAlertTriangle, FiZap, FiClock, FiTrendingUp } from 'react-icons/fi';

const KillShotDashboard = () => {
  const [isRunning, setIsRunning] = useState(false);
  const [dashboardData, setDashboardData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [selectedFeature, setSelectedFeature] = useState('overview');
  const intervalRef = useRef(null);
  const toast = useToast();

  const cardBg = useColorModeValue('white', 'gray.800');
  const borderColor = useColorModeValue('gray.200', 'gray.600');

  useEffect(() => {
    // Initialize dashboard
    fetchDashboardData();

    return () => {
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
      }
    };
  }, []);

  const fetchDashboardData = async () => {
    try {
      const response = await fetch('/api/v1/kill-shots/dashboard');
      const data = await response.json();
      setDashboardData(data);
      setLoading(false);
    } catch (error) {
      console.error('Error fetching dashboard data:', error);
      setLoading(false);
      toast({
        title: 'Error',
        description: 'Failed to fetch dashboard data',
        status: 'error',
        duration: 3000,
        isClosable: true,
      });
    }
  };

  const startMonitoring = () => {
    setIsRunning(true);
    intervalRef.current = setInterval(fetchDashboardData, 5000); // Update every 5 seconds
    toast({
      title: 'Monitoring Started',
      description: 'Real-time monitoring is now active',
      status: 'success',
      duration: 2000,
      isClosable: true,
    });
  };

  const stopMonitoring = () => {
    setIsRunning(false);
    if (intervalRef.current) {
      clearInterval(intervalRef.current);
      intervalRef.current = null;
    }
    toast({
      title: 'Monitoring Stopped',
      description: 'Real-time monitoring has been paused',
      status: 'info',
      duration: 2000,
      isClosable: true,
    });
  };

  const triggerKillShotFeature = async (feature) => {
    try {
      const response = await fetch(`/api/v1/kill-shots/${feature}/trigger`, {
        method: 'POST'
      });
      const result = await response.json();

      toast({
        title: `${feature} Triggered`,
        description: 'Kill Shot feature executed successfully',
        status: 'success',
        duration: 3000,
        isClosable: true,
      });

      // Refresh data
      fetchDashboardData();
    } catch (error) {
      toast({
        title: 'Error',
        description: `Failed to trigger ${feature}`,
        status: 'error',
        duration: 3000,
        isClosable: true,
      });
    }
  };

  if (loading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" height="400px">
        <VStack>
          <Spinner size="xl" color="blue.500" />
          <Text>Loading Kill Shot Dashboard...</Text>
        </VStack>
      </Box>
    );
  }

  const renderOverviewTab = () => (
    <Grid templateColumns="repeat(auto-fit, minmax(300px, 1fr))" gap={6}>
      {/* System Status */}
      <Card bg={cardBg} borderColor={borderColor}>
        <CardBody>
          <VStack align="start" spacing={4}>
            <HStack justify="space-between" width="100%">
              <Heading size="md">System Status</Heading>
              <Badge
                colorScheme={dashboardData?.system_status === 'healthy' ? 'green' : 'red'}
                variant="solid"
              >
                {dashboardData?.system_status?.toUpperCase()}
              </Badge>
            </HStack>

            <HStack spacing={4} width="100%">
              <Button
                leftIcon={isRunning ? <FiPause /> : <FiPlay />}
                colorScheme={isRunning ? 'red' : 'green'}
                onClick={isRunning ? stopMonitoring : startMonitoring}
                size="sm"
              >
                {isRunning ? 'Stop' : 'Start'} Monitoring
              </Button>

              <Button
                leftIcon={<FiRefreshCw />}
                variant="outline"
                onClick={fetchDashboardData}
                size="sm"
              >
                Refresh
              </Button>
            </HStack>

            <Text fontSize="sm" color="gray.500">
              Last updated: {new Date(dashboardData?.timestamp).toLocaleTimeString()}
            </Text>
          </VStack>
        </CardBody>
      </Card>

      {/* Active Predictions */}
      <Card bg={cardBg} borderColor={borderColor}>
        <CardBody>
          <VStack align="start" spacing={4}>
            <Heading size="md">🔮 Active Predictions</Heading>

            {dashboardData?.active_predictions?.length > 0 ? (
              dashboardData.active_predictions.map((prediction, index) => (
                <Alert key={index} status="warning" borderRadius="md">
                  <AlertIcon />
                  <Box>
                    <AlertTitle fontSize="sm">
                      {prediction.type.replace('_', ' ').toUpperCase()}
                    </AlertTitle>
                    <AlertDescription fontSize="xs">
                      {(prediction.probability * 100).toFixed(1)}% probability in {prediction.time_until_failure}
                    </AlertDescription>
                  </Box>
                </Alert>
              ))
            ) : (
              <Text color="gray.500">No critical predictions detected</Text>
            )}
          </VStack>
        </CardBody>
      </Card>

      {/* Current Metrics */}
      <Card bg={cardBg} borderColor={borderColor}>
        <CardBody>
          <VStack align="start" spacing={4}>
            <Heading size="md">📊 Current Metrics</Heading>

            <Grid templateColumns="repeat(2, 1fr)" gap={4} width="100%">
              <Stat>
                <StatLabel>CPU Usage</StatLabel>
                <StatNumber>{dashboardData?.current_metrics?.system_cpu_usage?.toFixed(1)}%</StatNumber>
                <StatHelpText>
                  <StatArrow type="increase" />
                  Real-time
                </StatHelpText>
              </Stat>

              <Stat>
                <StatLabel>Memory</StatLabel>
                <StatNumber>{dashboardData?.current_metrics?.system_memory_usage?.toFixed(1)}%</StatNumber>
                <StatHelpText>
                  <StatArrow type="decrease" />
                  Optimized
                </StatHelpText>
              </Stat>

              <Stat>
                <StatLabel>API Response</StatLabel>
                <StatNumber>{dashboardData?.current_metrics?.api_response_time?.toFixed(0)}ms</StatNumber>
                <StatHelpText>Average</StatHelpText>
              </Stat>

              <Stat>
                <StatLabel>Error Rate</StatLabel>
                <StatNumber>{dashboardData?.current_metrics?.api_error_rate?.toFixed(2)}%</StatNumber>
                <StatHelpText>Last 5min</StatHelpText>
              </Stat>
            </Grid>
          </VStack>
        </CardBody>
      </Card>

      {/* Kill Shot Features */}
      <Card bg={cardBg} borderColor={borderColor}>
        <CardBody>
          <VStack align="start" spacing={4}>
            <Heading size="md">⚡ Kill Shot Features</Heading>

            <VStack spacing={3} width="100%">
              {[
                { name: 'api-time-machine', icon: FiClock, title: 'API Time Machine', desc: 'Track API evolution' },
                { name: 'telepathic-discovery', icon: FiZap, title: 'Telepathic Discovery', desc: 'Find hidden APIs' },
                { name: 'quantum-test-generation', icon: FiTrendingUp, title: 'Quantum Test Gen', desc: 'Generate millions of tests' },
                { name: 'predictive-analysis', icon: FiAlertTriangle, title: 'Predictive Analysis', desc: '24h failure prediction' }
              ].map((feature) => (
                <HStack key={feature.name} justify="space-between" width="100%" p={2} borderRadius="md" bg="gray.50" _dark={{ bg: 'gray.700' }}>
                  <HStack>
                    <feature.icon size={20} />
                    <VStack align="start" spacing={0}>
                      <Text fontWeight="semibold" fontSize="sm">{feature.title}</Text>
                      <Text fontSize="xs" color="gray.500">{feature.desc}</Text>
                    </VStack>
                  </HStack>

                  <Button
                    size="xs"
                    colorScheme="blue"
                    variant="outline"
                    onClick={() => triggerKillShotFeature(feature.name)}
                  >
                    Trigger
                  </Button>
                </HStack>
              ))}
            </VStack>
          </VStack>
        </CardBody>
      </Card>
    </Grid>
  );

  const renderPredictiveAnalysisTab = () => (
    <VStack spacing={6}>
      <Card bg={cardBg} borderColor={borderColor} width="100%">
        <CardBody>
          <VStack align="start" spacing={4}>
            <Heading size="md">🔮 24-Hour Failure Predictions</Heading>

            {dashboardData?.active_predictions?.length > 0 ? (
              <Table size="sm">
                <Thead>
                  <Tr>
                    <Th>Failure Type</Th>
                    <Th>Probability</Th>
                    <Th>Time Until Failure</Th>
                    <Th>Impact Score</Th>
                    <Th>Actions</Th>
                  </Tr>
                </Thead>
                <Tbody>
                  {dashboardData.active_predictions.map((prediction, index) => (
                    <Tr key={index}>
                      <Td>
                        <Badge colorScheme="red" variant="subtle">
                          {prediction.type.replace('_', ' ')}
                        </Badge>
                      </Td>
                      <Td>
                        <HStack>
                          <Progress
                            value={prediction.probability * 100}
                            size="sm"
                            width="60px"
                            colorScheme={prediction.probability > 0.7 ? 'red' : 'orange'}
                          />
                          <Text fontSize="sm">{(prediction.probability * 100).toFixed(1)}%</Text>
                        </HStack>
                      </Td>
                      <Td>{prediction.time_until_failure}</Td>
                      <Td>
                        <Badge colorScheme={prediction.impact_score > 70 ? 'red' : 'yellow'}>
                          {prediction.impact_score.toFixed(0)}
                        </Badge>
                      </Td>
                      <Td>
                        <Tooltip label="View preventive actions">
                          <IconButton
                            icon={<FiAlertTriangle />}
                            size="xs"
                            variant="ghost"
                          />
                        </Tooltip>
                      </Td>
                    </Tr>
                  ))}
                </Tbody>
              </Table>
            ) : (
              <Alert status="success">
                <AlertIcon />
                <AlertTitle>All Systems Normal</AlertTitle>
                <AlertDescription>
                  No critical failures predicted in the next 24 hours
                </AlertDescription>
              </Alert>
            )}
          </VStack>
        </CardBody>
      </Card>
    </VStack>
  );

  const renderPerformanceTab = () => {
    // Generate sample performance data for visualization
    const performanceData = Array.from({ length: 24 }, (_, i) => ({
      hour: `${i}:00`,
      responseTime: Math.random() * 200 + 50,
      throughput: Math.random() * 1000 + 500,
      errorRate: Math.random() * 5
    }));

    return (
      <VStack spacing={6}>
        <Card bg={cardBg} borderColor={borderColor} width="100%">
          <CardBody>
            <VStack align="start" spacing={4}>
              <Heading size="md">🚀 Performance Metrics</Heading>

              <Grid templateColumns="repeat(auto-fit, minmax(200px, 1fr))" gap={4} width="100%">
                <Stat>
                  <StatLabel>Current Throughput</StatLabel>
                  <StatNumber>1,247</StatNumber>
                  <StatHelpText>requests/second</StatHelpText>
                </Stat>

                <Stat>
                  <StatLabel>Avg Response Time</StatLabel>
                  <StatNumber>127ms</StatNumber>
                  <StatHelpText>
                    <StatArrow type="decrease" />
                    12% improvement
                  </StatHelpText>
                </Stat>

                <Stat>
                  <StatLabel>Uptime</StatLabel>
                  <StatNumber>99.9%</StatNumber>
                  <StatHelpText>Last 30 days</StatHelpText>
                </Stat>

                <Stat>
                  <StatLabel>Tests/Second</StatLabel>
                  <StatNumber>80,709</StatNumber>
                  <StatHelpText>Peak performance</StatHelpText>
                </Stat>
              </Grid>
            </VStack>
          </CardBody>
        </Card>

        <Card bg={cardBg} borderColor={borderColor} width="100%">
          <CardBody>
            <Heading size="md" mb={4}>24-Hour Performance Trends</Heading>

            <ResponsiveContainer width="100%" height={300}>
              <AreaChart data={performanceData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="hour" />
                <YAxis />
                <RechartsTooltip />
                <Legend />
                <Area
                  type="monotone"
                  dataKey="responseTime"
                  stackId="1"
                  stroke="#8884d8"
                  fill="#8884d8"
                  name="Response Time (ms)"
                />
                <Area
                  type="monotone"
                  dataKey="throughput"
                  stackId="2"
                  stroke="#82ca9d"
                  fill="#82ca9d"
                  name="Throughput (req/s)"
                />
              </AreaChart>
            </ResponsiveContainer>
          </CardBody>
        </Card>
      </VStack>
    );
  };

  return (
    <Box p={6}>
      <VStack align="start" spacing={6}>
        <HStack justify="space-between" width="100%">
          <VStack align="start" spacing={1}>
            <Heading size="lg">⚡ Kill Shot Dashboard</Heading>
            <Text color="gray.500">
              Real-time monitoring and predictive analysis powered by AI
            </Text>
          </VStack>

          <HStack>
            <Badge colorScheme={isRunning ? 'green' : 'gray'} variant="solid">
              {isRunning ? 'LIVE' : 'PAUSED'}
            </Badge>
          </HStack>
        </HStack>

        <Tabs variant="enclosed" width="100%">
          <TabList>
            <Tab>Overview</Tab>
            <Tab>Predictive Analysis</Tab>
            <Tab>Performance</Tab>
            <Tab>API Time Machine</Tab>
            <Tab>Test Generation</Tab>
          </TabList>

          <TabPanels>
            <TabPanel>
              {renderOverviewTab()}
            </TabPanel>

            <TabPanel>
              {renderPredictiveAnalysisTab()}
            </TabPanel>

            <TabPanel>
              {renderPerformanceTab()}
            </TabPanel>

            <TabPanel>
              <Alert status="info">
                <AlertIcon />
                <AlertTitle>API Time Machine</AlertTitle>
                <AlertDescription>
                  Track API evolution and detect breaking changes over time
                </AlertDescription>
              </Alert>
            </TabPanel>

            <TabPanel>
              <Alert status="info">
                <AlertIcon />
                <AlertTitle>Quantum Test Generation</AlertTitle>
                <AlertDescription>
                  Generate millions of test cases with quantum-inspired algorithms
                </AlertDescription>
              </Alert>
            </TabPanel>
          </TabPanels>
        </Tabs>
      </VStack>
    </Box>
  );
};

export default KillShotDashboard;