import React, { useState, useEffect, useRef } from 'react';
import {
  Box,
  Grid,
  Card,
  CardBody,
  CardHeader,
  Heading,
  Text,
  Badge,
  Progress,
  VStack,
  HStack,
  Button,
  Select,
  Input,
  InputGroup,
  InputLeftElement,
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
  Tag,
  TagLabel,
  Divider,
  useToast,
  Modal,
  ModalOverlay,
  ModalContent,
  ModalHeader,
  ModalBody,
  ModalCloseButton,
  useDisclosure,
  Flex
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
  Bar,
  PieChart,
  Pie,
  Cell,
  ScatterChart,
  Scatter,
  Radar,
  RadarChart,
  PolarGrid,
  PolarAngleAxis,
  PolarRadiusAxis
} from 'recharts';
import {
  FiSearch,
  FiDownload,
  FiRefreshCw,
  FiTrendingUp,
  FiTrendingDown,
  FiActivity,
  FiUsers,
  FiServer,
  FiDatabase,
  FiGlobe,
  FiClock,
  FiAlertTriangle,
  FiCheckCircle,
  FiFilter,
  FiCalendar
} from 'react-icons/fi';

const AdvancedAnalyticsDashboard = () => {
  const [analyticsData, setAnalyticsData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [selectedTimeRange, setSelectedTimeRange] = useState('24h');
  const [selectedMetric, setSelectedMetric] = useState('all');
  const [searchQuery, setSearchQuery] = useState('');
  const [isRealTime, setIsRealTime] = useState(false);
  const intervalRef = useRef(null);
  const toast = useToast();
  const { isOpen, onOpen, onClose } = useDisclosure();

  const cardBg = useColorModeValue('white', 'gray.800');
  const borderColor = useColorModeValue('gray.200', 'gray.600');
  const textColor = useColorModeValue('gray.600', 'gray.300');

  useEffect(() => {
    fetchAnalyticsData();

    return () => {
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
      }
    };
  }, [selectedTimeRange, selectedMetric]);

  const fetchAnalyticsData = async () => {
    try {
      setLoading(true);
      const response = await fetch(`/api/v1/analytics/advanced?timeRange=${selectedTimeRange}&metric=${selectedMetric}`);
      const data = await response.json();
      setAnalyticsData(data);
    } catch (error) {
      console.error('Error fetching analytics:', error);
      toast({
        title: 'Error',
        description: 'Failed to fetch analytics data',
        status: 'error',
        duration: 3000,
        isClosable: true,
      });
    } finally {
      setLoading(false);
    }
  };

  const toggleRealTime = () => {
    if (isRealTime) {
      setIsRealTime(false);
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
        intervalRef.current = null;
      }
    } else {
      setIsRealTime(true);
      intervalRef.current = setInterval(fetchAnalyticsData, 10000); // Update every 10 seconds
    }
  };

  const exportData = async (format) => {
    try {
      const response = await fetch(`/api/v1/analytics/export?format=${format}&timeRange=${selectedTimeRange}`);
      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `analytics_${selectedTimeRange}.${format}`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);

      toast({
        title: 'Export Successful',
        description: `Analytics data exported as ${format.toUpperCase()}`,
        status: 'success',
        duration: 3000,
        isClosable: true,
      });
    } catch (error) {
      toast({
        title: 'Export Failed',
        description: 'Failed to export analytics data',
        status: 'error',
        duration: 3000,
        isClosable: true,
      });
    }
  };

  if (loading && !analyticsData) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" height="400px">
        <VStack>
          <Spinner size="xl" color="blue.500" />
          <Text>Loading Advanced Analytics...</Text>
        </VStack>
      </Box>
    );
  }

  // Sample data generation for demo purposes
  const mockAnalyticsData = analyticsData || {
    overview: {
      totalRequests: 1234567,
      avgResponseTime: 127,
      errorRate: 0.23,
      activeUsers: 8945,
      totalEndpoints: 359,
      testsExecuted: 203242,
      systemHealth: 98.7
    },
    trends: Array.from({ length: 24 }, (_, i) => ({
      time: `${i}:00`,
      requests: Math.floor(Math.random() * 1000) + 500,
      responseTime: Math.floor(Math.random() * 100) + 50,
      errors: Math.floor(Math.random() * 20),
      activeUsers: Math.floor(Math.random() * 200) + 100
    })),
    endpoints: [
      { path: '/api/v1/projects', requests: 45230, avgTime: 123, errors: 12, status: 'healthy' },
      { path: '/api/v1/tests', requests: 38940, avgTime: 89, errors: 5, status: 'healthy' },
      { path: '/api/v1/auth/login', requests: 29384, avgTime: 234, errors: 45, status: 'warning' },
      { path: '/api/v1/workspaces', requests: 23847, avgTime: 156, errors: 8, status: 'healthy' },
      { path: '/api/v1/orchestrate', requests: 19283, avgTime: 456, errors: 23, status: 'critical' }
    ],
    geographicData: [
      { country: 'United States', requests: 456789, users: 3456 },
      { country: 'United Kingdom', requests: 234567, users: 1890 },
      { country: 'Germany', requests: 189234, users: 1567 },
      { country: 'France', requests: 145678, users: 1234 },
      { country: 'Canada', requests: 123456, users: 987 }
    ],
    performanceMetrics: [
      { name: 'CPU Usage', value: 65, trend: 'up', change: 5.2 },
      { name: 'Memory Usage', value: 78, trend: 'down', change: -2.1 },
      { name: 'Disk I/O', value: 45, trend: 'stable', change: 0.5 },
      { name: 'Network I/O', value: 67, trend: 'up', change: 8.3 }
    ]
  };

  const renderOverviewCards = () => (
    <Grid templateColumns="repeat(auto-fit, minmax(250px, 1fr))" gap={6} mb={8}>
      <Card bg={cardBg} borderColor={borderColor}>
        <CardBody>
          <Stat>
            <StatLabel>Total Requests</StatLabel>
            <StatNumber>{mockAnalyticsData.overview.totalRequests.toLocaleString()}</StatNumber>
            <StatHelpText>
              <StatArrow type="increase" />
              23.5% from last period
            </StatHelpText>
          </Stat>
        </CardBody>
      </Card>

      <Card bg={cardBg} borderColor={borderColor}>
        <CardBody>
          <Stat>
            <StatLabel>Avg Response Time</StatLabel>
            <StatNumber>{mockAnalyticsData.overview.avgResponseTime}ms</StatNumber>
            <StatHelpText>
              <StatArrow type="decrease" />
              8.2% improvement
            </StatHelpText>
          </Stat>
        </CardBody>
      </Card>

      <Card bg={cardBg} borderColor={borderColor}>
        <CardBody>
          <Stat>
            <StatLabel>Error Rate</StatLabel>
            <StatNumber>{mockAnalyticsData.overview.errorRate}%</StatNumber>
            <StatHelpText>
              <StatArrow type="decrease" />
              0.1% improvement
            </StatHelpText>
          </Stat>
        </CardBody>
      </Card>

      <Card bg={cardBg} borderColor={borderColor}>
        <CardBody>
          <Stat>
            <StatLabel>Active Users</StatLabel>
            <StatNumber>{mockAnalyticsData.overview.activeUsers.toLocaleString()}</StatNumber>
            <StatHelpText>
              <StatArrow type="increase" />
              12.3% growth
            </StatHelpText>
          </Stat>
        </CardBody>
      </Card>

      <Card bg={cardBg} borderColor={borderColor}>
        <CardBody>
          <Stat>
            <StatLabel>API Endpoints</StatLabel>
            <StatNumber>{mockAnalyticsData.overview.totalEndpoints}</StatNumber>
            <StatHelpText>All monitored</StatHelpText>
          </Stat>
        </CardBody>
      </Card>

      <Card bg={cardBg} borderColor={borderColor}>
        <CardBody>
          <Stat>
            <StatLabel>Tests/Second</StatLabel>
            <StatNumber>{mockAnalyticsData.overview.testsExecuted.toLocaleString()}</StatNumber>
            <StatHelpText>
              <FiTrendingUp color="green" />
              Peak performance
            </StatHelpText>
          </Stat>
        </CardBody>
      </Card>
    </Grid>
  );

  const renderPerformanceTrends = () => (
    <Card bg={cardBg} borderColor={borderColor} mb={8}>
      <CardHeader>
        <HStack justify="space-between">
          <Heading size="md">Performance Trends</Heading>
          <HStack>
            <Select size="sm" value={selectedTimeRange} onChange={(e) => setSelectedTimeRange(e.target.value)}>
              <option value="1h">Last Hour</option>
              <option value="24h">Last 24 Hours</option>
              <option value="7d">Last 7 Days</option>
              <option value="30d">Last 30 Days</option>
            </Select>
            <Button
              size="sm"
              leftIcon={isRealTime ? <FiActivity /> : <FiRefreshCw />}
              colorScheme={isRealTime ? "green" : "blue"}
              onClick={toggleRealTime}
            >
              {isRealTime ? 'Live' : 'Refresh'}
            </Button>
          </HStack>
        </HStack>
      </CardHeader>
      <CardBody>
        <ResponsiveContainer width="100%" height={400}>
          <AreaChart data={mockAnalyticsData.trends}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="time" />
            <YAxis yAxisId="left" orientation="left" />
            <YAxis yAxisId="right" orientation="right" />
            <RechartsTooltip />
            <Legend />
            <Area
              yAxisId="left"
              type="monotone"
              dataKey="requests"
              stackId="1"
              stroke="#8884d8"
              fill="#8884d8"
              name="Requests"
              fillOpacity={0.6}
            />
            <Area
              yAxisId="right"
              type="monotone"
              dataKey="responseTime"
              stackId="2"
              stroke="#82ca9d"
              fill="#82ca9d"
              name="Response Time (ms)"
              fillOpacity={0.6}
            />
            <Area
              yAxisId="left"
              type="monotone"
              dataKey="errors"
              stackId="3"
              stroke="#ffc658"
              fill="#ffc658"
              name="Errors"
              fillOpacity={0.6}
            />
          </AreaChart>
        </ResponsiveContainer>
      </CardBody>
    </Card>
  );

  const renderTopEndpoints = () => (
    <Card bg={cardBg} borderColor={borderColor} mb={8}>
      <CardHeader>
        <HStack justify="space-between">
          <Heading size="md">Top API Endpoints</Heading>
          <InputGroup size="sm" width="300px">
            <InputLeftElement pointerEvents="none">
              <FiSearch color="gray.300" />
            </InputLeftElement>
            <Input
              placeholder="Search endpoints..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
            />
          </InputGroup>
        </HStack>
      </CardHeader>
      <CardBody>
        <Table size="sm">
          <Thead>
            <Tr>
              <Th>Endpoint</Th>
              <Th isNumeric>Requests</Th>
              <Th isNumeric>Avg Time</Th>
              <Th isNumeric>Errors</Th>
              <Th>Status</Th>
            </Tr>
          </Thead>
          <Tbody>
            {mockAnalyticsData.endpoints
              .filter(endpoint =>
                searchQuery === '' ||
                endpoint.path.toLowerCase().includes(searchQuery.toLowerCase())
              )
              .map((endpoint, index) => (
                <Tr key={index}>
                  <Td>
                    <Text fontFamily="mono" fontSize="sm">
                      {endpoint.path}
                    </Text>
                  </Td>
                  <Td isNumeric>{endpoint.requests.toLocaleString()}</Td>
                  <Td isNumeric>{endpoint.avgTime}ms</Td>
                  <Td isNumeric>{endpoint.errors}</Td>
                  <Td>
                    <Badge
                      colorScheme={
                        endpoint.status === 'healthy' ? 'green' :
                        endpoint.status === 'warning' ? 'yellow' : 'red'
                      }
                      variant="subtle"
                    >
                      {endpoint.status}
                    </Badge>
                  </Td>
                </Tr>
              ))}
          </Tbody>
        </Table>
      </CardBody>
    </Card>
  );

  const renderGeographicAnalytics = () => (
    <Grid templateColumns="repeat(auto-fit, minmax(400px, 1fr))" gap={6} mb={8}>
      <Card bg={cardBg} borderColor={borderColor}>
        <CardHeader>
          <Heading size="md">Geographic Distribution</Heading>
        </CardHeader>
        <CardBody>
          <VStack align="stretch" spacing={4}>
            {mockAnalyticsData.geographicData.map((country, index) => (
              <Box key={index}>
                <HStack justify="space-between" mb={2}>
                  <Text fontWeight="semibold">{country.country}</Text>
                  <Text fontSize="sm" color={textColor}>
                    {country.requests.toLocaleString()} requests
                  </Text>
                </HStack>
                <Progress
                  value={(country.requests / mockAnalyticsData.geographicData[0].requests) * 100}
                  colorScheme="blue"
                  size="sm"
                />
                <Text fontSize="xs" color={textColor} mt={1}>
                  {country.users.toLocaleString()} active users
                </Text>
              </Box>
            ))}
          </VStack>
        </CardBody>
      </Card>

      <Card bg={cardBg} borderColor={borderColor}>
        <CardHeader>
          <Heading size="md">System Performance</Heading>
        </CardHeader>
        <CardBody>
          <VStack align="stretch" spacing={4}>
            {mockAnalyticsData.performanceMetrics.map((metric, index) => (
              <Box key={index}>
                <HStack justify="space-between" mb={2}>
                  <Text fontWeight="semibold">{metric.name}</Text>
                  <HStack>
                    <Text fontSize="sm" color={textColor}>
                      {metric.value}%
                    </Text>
                    {metric.trend === 'up' && <FiTrendingUp color="red" />}
                    {metric.trend === 'down' && <FiTrendingDown color="green" />}
                    {metric.trend === 'stable' && <FiActivity color="gray" />}
                  </HStack>
                </HStack>
                <Progress
                  value={metric.value}
                  colorScheme={metric.value > 80 ? 'red' : metric.value > 60 ? 'yellow' : 'green'}
                  size="sm"
                />
                <Text fontSize="xs" color={textColor} mt={1}>
                  {metric.change > 0 ? '+' : ''}{metric.change}% from last period
                </Text>
              </Box>
            ))}
          </VStack>
        </CardBody>
      </Card>
    </Grid>
  );

  const renderAdvancedCharts = () => (
    <Grid templateColumns="repeat(auto-fit, minmax(500px, 1fr))" gap={6} mb={8}>
      <Card bg={cardBg} borderColor={borderColor}>
        <CardHeader>
          <Heading size="md">Response Time Distribution</Heading>
        </CardHeader>
        <CardBody>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={mockAnalyticsData.trends}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="time" />
              <YAxis />
              <RechartsTooltip />
              <Bar dataKey="responseTime" fill="#8884d8" />
            </BarChart>
          </ResponsiveContainer>
        </CardBody>
      </Card>

      <Card bg={cardBg} borderColor={borderColor}>
        <CardHeader>
          <Heading size="md">Error Rate Analysis</Heading>
        </CardHeader>
        <CardBody>
          <ResponsiveContainer width="100%" height={300}>
            <LineChart data={mockAnalyticsData.trends}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="time" />
              <YAxis />
              <RechartsTooltip />
              <Legend />
              <Line type="monotone" dataKey="errors" stroke="#ff6b6b" strokeWidth={2} />
            </LineChart>
          </ResponsiveContainer>
        </CardBody>
      </Card>
    </Grid>
  );

  const renderRealTimeMetrics = () => (
    <Card bg={cardBg} borderColor={borderColor} mb={8}>
      <CardHeader>
        <HStack justify="space-between">
          <Heading size="md">Real-Time Metrics</Heading>
          <Badge colorScheme={isRealTime ? 'green' : 'gray'} variant="solid">
            {isRealTime ? 'LIVE' : 'PAUSED'}
          </Badge>
        </HStack>
      </CardHeader>
      <CardBody>
        <Grid templateColumns="repeat(auto-fit, minmax(200px, 1fr))" gap={4}>
          <VStack>
            <Text fontSize="2xl" fontWeight="bold" color="blue.500">
              {Math.floor(Math.random() * 1000) + 500}
            </Text>
            <Text fontSize="sm" color={textColor}>Requests/min</Text>
          </VStack>
          <VStack>
            <Text fontSize="2xl" fontWeight="bold" color="green.500">
              {Math.floor(Math.random() * 50) + 100}ms
            </Text>
            <Text fontSize="sm" color={textColor}>Avg Response</Text>
          </VStack>
          <VStack>
            <Text fontSize="2xl" fontWeight="bold" color="purple.500">
              {Math.floor(Math.random() * 100) + 200}
            </Text>
            <Text fontSize="sm" color={textColor}>Active Users</Text>
          </VStack>
          <VStack>
            <Text fontSize="2xl" fontWeight="bold" color="orange.500">
              {(Math.random() * 2).toFixed(2)}%
            </Text>
            <Text fontSize="sm" color={textColor}>Error Rate</Text>
          </VStack>
        </Grid>
      </CardBody>
    </Card>
  );

  return (
    <Box p={6}>
      <VStack align="start" spacing={6}>
        {/* Header */}
        <HStack justify="space-between" width="100%">
          <VStack align="start" spacing={1}>
            <Heading size="lg">📊 Advanced Analytics Dashboard</Heading>
            <Text color={textColor}>
              Comprehensive insights and performance analytics
            </Text>
          </VStack>

          <HStack>
            <Button
              leftIcon={<FiDownload />}
              size="sm"
              variant="outline"
              onClick={onOpen}
            >
              Export
            </Button>
            <Button
              leftIcon={<FiRefreshCw />}
              size="sm"
              colorScheme="blue"
              onClick={fetchAnalyticsData}
              isLoading={loading}
            >
              Refresh
            </Button>
          </HStack>
        </HStack>

        {/* Filters */}
        <Card bg={cardBg} borderColor={borderColor} width="100%">
          <CardBody>
            <HStack spacing={4} wrap="wrap">
              <HStack>
                <FiCalendar />
                <Text fontSize="sm" fontWeight="semibold">Time Range:</Text>
                <Select size="sm" value={selectedTimeRange} onChange={(e) => setSelectedTimeRange(e.target.value)}>
                  <option value="1h">Last Hour</option>
                  <option value="24h">Last 24 Hours</option>
                  <option value="7d">Last 7 Days</option>
                  <option value="30d">Last 30 Days</option>
                </Select>
              </HStack>

              <HStack>
                <FiFilter />
                <Text fontSize="sm" fontWeight="semibold">Metric:</Text>
                <Select size="sm" value={selectedMetric} onChange={(e) => setSelectedMetric(e.target.value)}>
                  <option value="all">All Metrics</option>
                  <option value="performance">Performance</option>
                  <option value="usage">Usage</option>
                  <option value="errors">Errors</option>
                </Select>
              </HStack>
            </HStack>
          </CardBody>
        </Card>

        {/* Main Analytics Content */}
        <Tabs variant="enclosed" width="100%">
          <TabList>
            <Tab>Overview</Tab>
            <Tab>Performance</Tab>
            <Tab>Endpoints</Tab>
            <Tab>Geographic</Tab>
            <Tab>Real-Time</Tab>
            <Tab>Custom Reports</Tab>
          </TabList>

          <TabPanels>
            <TabPanel>
              <VStack align="stretch" spacing={6}>
                {renderOverviewCards()}
                {renderPerformanceTrends()}
                {renderTopEndpoints()}
              </VStack>
            </TabPanel>

            <TabPanel>
              <VStack align="stretch" spacing={6}>
                {renderAdvancedCharts()}
                {renderGeographicAnalytics()}
              </VStack>
            </TabPanel>

            <TabPanel>
              <VStack align="stretch" spacing={6}>
                {renderTopEndpoints()}
              </VStack>
            </TabPanel>

            <TabPanel>
              <VStack align="stretch" spacing={6}>
                {renderGeographicAnalytics()}
              </VStack>
            </TabPanel>

            <TabPanel>
              <VStack align="stretch" spacing={6}>
                {renderRealTimeMetrics()}
                {renderPerformanceTrends()}
              </VStack>
            </TabPanel>

            <TabPanel>
              <Card bg={cardBg} borderColor={borderColor}>
                <CardBody>
                  <VStack align="center" spacing={4} py={12}>
                    <FiDatabase size={48} color="gray" />
                    <Heading size="md" color={textColor}>Custom Reports</Heading>
                    <Text color={textColor} textAlign="center">
                      Build custom analytics reports with drag-and-drop widgets,
                      custom date ranges, and advanced filtering options.
                    </Text>
                    <Button colorScheme="blue">
                      Create Custom Report
                    </Button>
                  </VStack>
                </CardBody>
              </Card>
            </TabPanel>
          </TabPanels>
        </Tabs>

        {/* Export Modal */}
        <Modal isOpen={isOpen} onClose={onClose}>
          <ModalOverlay />
          <ModalContent>
            <ModalHeader>Export Analytics Data</ModalHeader>
            <ModalCloseButton />
            <ModalBody pb={6}>
              <VStack spacing={4} align="stretch">
                <Text fontSize="sm" color={textColor}>
                  Choose the format for exporting your analytics data:
                </Text>

                <HStack spacing={3}>
                  <Button
                    flex={1}
                    onClick={() => {
                      exportData('csv');
                      onClose();
                    }}
                  >
                    CSV
                  </Button>
                  <Button
                    flex={1}
                    onClick={() => {
                      exportData('json');
                      onClose();
                    }}
                  >
                    JSON
                  </Button>
                  <Button
                    flex={1}
                    onClick={() => {
                      exportData('xlsx');
                      onClose();
                    }}
                  >
                    Excel
                  </Button>
                </HStack>

                <Divider />

                <VStack spacing={2} align="start">
                  <Text fontSize="sm" fontWeight="semibold">Export includes:</Text>
                  <Text fontSize="xs" color={textColor}>• Performance metrics and trends</Text>
                  <Text fontSize="xs" color={textColor}>• Endpoint usage statistics</Text>
                  <Text fontSize="xs" color={textColor}>• Geographic distribution data</Text>
                  <Text fontSize="xs" color={textColor}>• Error rates and response times</Text>
                </VStack>
              </VStack>
            </ModalBody>
          </ModalContent>
        </Modal>
      </VStack>
    </Box>
  );
};

export default AdvancedAnalyticsDashboard;