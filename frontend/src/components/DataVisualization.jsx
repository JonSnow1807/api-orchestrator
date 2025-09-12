import React, { useState, useEffect, useMemo } from 'react';
import {
  LineChart, Line, BarChart, Bar, PieChart, Pie, Cell,
  XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer,
  AreaChart, Area, ScatterChart, Scatter, RadarChart, Radar,
  PolarGrid, PolarAngleAxis, PolarRadiusAxis
} from 'recharts';
import { 
  ChartBarIcon, 
  TableCellsIcon, 
  ChartPieIcon,
  ArrowTrendingUpIcon,
  SparklesIcon,
  ArrowPathIcon,
  EyeIcon,
  CodeBracketIcon
} from '@heroicons/react/24/outline';

const DataVisualization = ({ responseData, onVisualizationChange }) => {
  const [visualizationType, setVisualizationType] = useState('json');
  const [chartData, setChartData] = useState([]);
  const [selectedFields, setSelectedFields] = useState({ x: '', y: '' });
  const [autoDetectedType, setAutoDetectedType] = useState(null);
  const [customQuery, setCustomQuery] = useState('');
  const [showCustomizer, setShowCustomizer] = useState(false);

  // Colors for charts
  const COLORS = ['#3B82F6', '#10B981', '#F59E0B', '#EF4444', '#8B5CF6', '#EC4899', '#06B6D4', '#84CC16'];

  useEffect(() => {
    if (responseData) {
      analyzeDataStructure();
    }
  }, [responseData]);

  const analyzeDataStructure = () => {
    if (!responseData) return;

    try {
      // Parse response if it's a string
      const data = typeof responseData === 'string' ? JSON.parse(responseData) : responseData;
      
      // Auto-detect data structure and suggest visualization
      if (Array.isArray(data)) {
        // Array of objects - perfect for charts
        if (data.length > 0 && typeof data[0] === 'object') {
          setChartData(data);
          autoDetectVisualization(data);
        }
      } else if (typeof data === 'object') {
        // Single object - check for nested arrays
        const arrayField = Object.keys(data).find(key => Array.isArray(data[key]));
        if (arrayField && data[arrayField].length > 0) {
          setChartData(data[arrayField]);
          autoDetectVisualization(data[arrayField]);
        } else {
          // Convert object to array for visualization
          const converted = Object.entries(data).map(([key, value]) => ({
            name: key,
            value: typeof value === 'number' ? value : 1
          }));
          setChartData(converted);
          setAutoDetectedType('pie');
        }
      }
    } catch (error) {
      console.error('Error parsing response data:', error);
    }
  };

  const autoDetectVisualization = (data) => {
    if (!data || data.length === 0) return;

    const firstItem = data[0];
    const keys = Object.keys(firstItem);
    
    // Check for time series data
    const hasDate = keys.some(key => 
      key.toLowerCase().includes('date') || 
      key.toLowerCase().includes('time') ||
      key.toLowerCase().includes('timestamp')
    );
    
    // Check for numeric values
    const numericKeys = keys.filter(key => 
      typeof firstItem[key] === 'number'
    );

    // Auto-select visualization type
    if (hasDate && numericKeys.length > 0) {
      setAutoDetectedType('line');
      setSelectedFields({
        x: keys.find(k => k.toLowerCase().includes('date') || k.toLowerCase().includes('time')),
        y: numericKeys[0]
      });
    } else if (numericKeys.length >= 2) {
      setAutoDetectedType('scatter');
      setSelectedFields({
        x: numericKeys[0],
        y: numericKeys[1]
      });
    } else if (numericKeys.length === 1) {
      setAutoDetectedType('bar');
      setSelectedFields({
        x: keys.find(k => typeof firstItem[k] === 'string') || 'index',
        y: numericKeys[0]
      });
    } else {
      setAutoDetectedType('table');
    }
  };

  const renderVisualization = () => {
    switch (visualizationType) {
      case 'line':
        return renderLineChart();
      case 'bar':
        return renderBarChart();
      case 'pie':
        return renderPieChart();
      case 'area':
        return renderAreaChart();
      case 'scatter':
        return renderScatterChart();
      case 'radar':
        return renderRadarChart();
      case 'table':
        return renderTable();
      case 'json':
        return renderJSON();
      default:
        return renderJSON();
    }
  };

  const renderLineChart = () => (
    <ResponsiveContainer width="100%" height={400}>
      <LineChart data={chartData}>
        <CartesianGrid strokeDasharray="3 3" />
        <XAxis dataKey={selectedFields.x || 'name'} />
        <YAxis />
        <Tooltip />
        <Legend />
        <Line 
          type="monotone" 
          dataKey={selectedFields.y || 'value'} 
          stroke="#3B82F6" 
          activeDot={{ r: 8 }}
        />
      </LineChart>
    </ResponsiveContainer>
  );

  const renderBarChart = () => (
    <ResponsiveContainer width="100%" height={400}>
      <BarChart data={chartData}>
        <CartesianGrid strokeDasharray="3 3" />
        <XAxis dataKey={selectedFields.x || 'name'} />
        <YAxis />
        <Tooltip />
        <Legend />
        <Bar dataKey={selectedFields.y || 'value'} fill="#3B82F6" />
      </BarChart>
    </ResponsiveContainer>
  );

  const renderPieChart = () => (
    <ResponsiveContainer width="100%" height={400}>
      <PieChart>
        <Pie
          data={chartData}
          cx="50%"
          cy="50%"
          labelLine={false}
          label={({ name, percent }) => `${name}: ${(percent * 100).toFixed(0)}%`}
          outerRadius={150}
          fill="#8884d8"
          dataKey={selectedFields.y || 'value'}
        >
          {chartData.map((entry, index) => (
            <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
          ))}
        </Pie>
        <Tooltip />
      </PieChart>
    </ResponsiveContainer>
  );

  const renderAreaChart = () => (
    <ResponsiveContainer width="100%" height={400}>
      <AreaChart data={chartData}>
        <CartesianGrid strokeDasharray="3 3" />
        <XAxis dataKey={selectedFields.x || 'name'} />
        <YAxis />
        <Tooltip />
        <Legend />
        <Area 
          type="monotone" 
          dataKey={selectedFields.y || 'value'} 
          stroke="#3B82F6" 
          fill="#3B82F6" 
          fillOpacity={0.6}
        />
      </AreaChart>
    </ResponsiveContainer>
  );

  const renderScatterChart = () => (
    <ResponsiveContainer width="100%" height={400}>
      <ScatterChart>
        <CartesianGrid strokeDasharray="3 3" />
        <XAxis dataKey={selectedFields.x || 'x'} name="X" />
        <YAxis dataKey={selectedFields.y || 'y'} name="Y" />
        <Tooltip cursor={{ strokeDasharray: '3 3' }} />
        <Scatter name="Data" data={chartData} fill="#3B82F6" />
      </ScatterChart>
    </ResponsiveContainer>
  );

  const renderRadarChart = () => (
    <ResponsiveContainer width="100%" height={400}>
      <RadarChart data={chartData}>
        <PolarGrid />
        <PolarAngleAxis dataKey={selectedFields.x || 'name'} />
        <PolarRadiusAxis />
        <Radar 
          name="Value" 
          dataKey={selectedFields.y || 'value'} 
          stroke="#3B82F6" 
          fill="#3B82F6" 
          fillOpacity={0.6}
        />
      </RadarChart>
    </ResponsiveContainer>
  );

  const renderTable = () => {
    if (!chartData || chartData.length === 0) return <div>No data to display</div>;

    const columns = Object.keys(chartData[0]);

    return (
      <div className="overflow-x-auto">
        <table className="min-w-full divide-y divide-gray-200 dark:divide-gray-700">
          <thead className="bg-gray-50 dark:bg-gray-800">
            <tr>
              {columns.map((col) => (
                <th
                  key={col}
                  className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider"
                >
                  {col}
                </th>
              ))}
            </tr>
          </thead>
          <tbody className="bg-white dark:bg-gray-900 divide-y divide-gray-200 dark:divide-gray-700">
            {chartData.map((row, idx) => (
              <tr key={idx}>
                {columns.map((col) => (
                  <td
                    key={col}
                    className="px-6 py-4 whitespace-nowrap text-sm text-gray-900 dark:text-gray-300"
                  >
                    {typeof row[col] === 'object' ? JSON.stringify(row[col]) : row[col]}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    );
  };

  const renderJSON = () => {
    const data = typeof responseData === 'string' ? responseData : JSON.stringify(responseData, null, 2);
    
    return (
      <pre className="bg-gray-900 text-gray-100 p-4 rounded-lg overflow-auto max-h-96">
        <code>{data}</code>
      </pre>
    );
  };

  const handleVisualizationTypeChange = (type) => {
    setVisualizationType(type);
    if (onVisualizationChange) {
      onVisualizationChange(type);
    }
  };

  const handleCustomQuery = () => {
    try {
      // Simple query parser for natural language
      const query = customQuery.toLowerCase();
      
      if (query.includes('group by')) {
        // Group data by field
        const field = query.split('group by')[1].trim();
        const grouped = chartData.reduce((acc, item) => {
          const key = item[field];
          if (!acc[key]) acc[key] = [];
          acc[key].push(item);
          return acc;
        }, {});
        
        const groupedData = Object.entries(grouped).map(([key, items]) => ({
          name: key,
          value: items.length
        }));
        
        setChartData(groupedData);
        setVisualizationType('bar');
      } else if (query.includes('sum')) {
        // Sum numeric fields
        const field = query.split('sum')[1].trim();
        const sum = chartData.reduce((acc, item) => acc + (item[field] || 0), 0);
        
        setChartData([{ name: `Sum of ${field}`, value: sum }]);
        setVisualizationType('bar');
      } else if (query.includes('average')) {
        // Calculate average
        const field = query.split('average')[1].trim();
        const values = chartData.map(item => item[field] || 0);
        const avg = values.reduce((a, b) => a + b, 0) / values.length;
        
        setChartData([{ name: `Average ${field}`, value: avg }]);
        setVisualizationType('bar');
      }
    } catch (error) {
      console.error('Error processing custom query:', error);
    }
  };

  const getFieldOptions = () => {
    if (!chartData || chartData.length === 0) return [];
    return Object.keys(chartData[0]);
  };

  return (
    <div className="space-y-4">
      {/* Visualization Type Selector */}
      <div className="flex flex-wrap gap-2 p-4 bg-gray-50 dark:bg-gray-800 rounded-lg">
        <button
          onClick={() => handleVisualizationTypeChange('json')}
          className={`flex items-center gap-2 px-3 py-2 rounded-lg transition-colors ${
            visualizationType === 'json'
              ? 'bg-blue-500 text-white'
              : 'bg-white dark:bg-gray-700 text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-600'
          }`}
        >
          <CodeBracketIcon className="h-4 w-4" />
          JSON
        </button>
        
        <button
          onClick={() => handleVisualizationTypeChange('table')}
          className={`flex items-center gap-2 px-3 py-2 rounded-lg transition-colors ${
            visualizationType === 'table'
              ? 'bg-blue-500 text-white'
              : 'bg-white dark:bg-gray-700 text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-600'
          }`}
        >
          <TableCellsIcon className="h-4 w-4" />
          Table
        </button>
        
        <button
          onClick={() => handleVisualizationTypeChange('line')}
          className={`flex items-center gap-2 px-3 py-2 rounded-lg transition-colors ${
            visualizationType === 'line'
              ? 'bg-blue-500 text-white'
              : 'bg-white dark:bg-gray-700 text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-600'
          }`}
        >
          <ArrowTrendingUpIcon className="h-4 w-4" />
          Line Chart
        </button>
        
        <button
          onClick={() => handleVisualizationTypeChange('bar')}
          className={`flex items-center gap-2 px-3 py-2 rounded-lg transition-colors ${
            visualizationType === 'bar'
              ? 'bg-blue-500 text-white'
              : 'bg-white dark:bg-gray-700 text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-600'
          }`}
        >
          <ChartBarIcon className="h-4 w-4" />
          Bar Chart
        </button>
        
        <button
          onClick={() => handleVisualizationTypeChange('pie')}
          className={`flex items-center gap-2 px-3 py-2 rounded-lg transition-colors ${
            visualizationType === 'pie'
              ? 'bg-blue-500 text-white'
              : 'bg-white dark:bg-gray-700 text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-600'
          }`}
        >
          <ChartPieIcon className="h-4 w-4" />
          Pie Chart
        </button>
        
        <button
          onClick={() => handleVisualizationTypeChange('area')}
          className={`flex items-center gap-2 px-3 py-2 rounded-lg transition-colors ${
            visualizationType === 'area'
              ? 'bg-blue-500 text-white'
              : 'bg-white dark:bg-gray-700 text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-600'
          }`}
        >
          <ArrowTrendingUpIcon className="h-4 w-4" />
          Area Chart
        </button>
        
        <button
          onClick={() => handleVisualizationTypeChange('scatter')}
          className={`flex items-center gap-2 px-3 py-2 rounded-lg transition-colors ${
            visualizationType === 'scatter'
              ? 'bg-blue-500 text-white'
              : 'bg-white dark:bg-gray-700 text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-600'
          }`}
        >
          <SparklesIcon className="h-4 w-4" />
          Scatter Plot
        </button>
        
        <button
          onClick={() => handleVisualizationTypeChange('radar')}
          className={`flex items-center gap-2 px-3 py-2 rounded-lg transition-colors ${
            visualizationType === 'radar'
              ? 'bg-blue-500 text-white'
              : 'bg-white dark:bg-gray-700 text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-600'
          }`}
        >
          <ChartPieIcon className="h-4 w-4" />
          Radar Chart
        </button>
        
        {/* AI Auto-detect button */}
        {autoDetectedType && (
          <button
            onClick={() => handleVisualizationTypeChange(autoDetectedType)}
            className="flex items-center gap-2 px-3 py-2 rounded-lg bg-gradient-to-r from-purple-500 to-pink-500 text-white hover:from-purple-600 hover:to-pink-600 transition-all"
          >
            <SparklesIcon className="h-4 w-4" />
            AI Suggested: {autoDetectedType}
          </button>
        )}
      </div>

      {/* Customizer Panel */}
      {visualizationType !== 'json' && visualizationType !== 'table' && (
        <div className="p-4 bg-gray-50 dark:bg-gray-800 rounded-lg space-y-3">
          <button
            onClick={() => setShowCustomizer(!showCustomizer)}
            className="flex items-center gap-2 text-sm text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-gray-200"
          >
            <EyeIcon className="h-4 w-4" />
            {showCustomizer ? 'Hide' : 'Show'} Customization Options
          </button>
          
          {showCustomizer && (
            <div className="space-y-3">
              {/* Field Selectors */}
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                    X-Axis Field
                  </label>
                  <select
                    value={selectedFields.x}
                    onChange={(e) => setSelectedFields({ ...selectedFields, x: e.target.value })}
                    className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100"
                  >
                    <option value="">Select field</option>
                    {getFieldOptions().map((field) => (
                      <option key={field} value={field}>
                        {field}
                      </option>
                    ))}
                  </select>
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                    Y-Axis Field
                  </label>
                  <select
                    value={selectedFields.y}
                    onChange={(e) => setSelectedFields({ ...selectedFields, y: e.target.value })}
                    className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100"
                  >
                    <option value="">Select field</option>
                    {getFieldOptions().map((field) => (
                      <option key={field} value={field}>
                        {field}
                      </option>
                    ))}
                  </select>
                </div>
              </div>
              
              {/* Natural Language Query */}
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                  Natural Language Query
                </label>
                <div className="flex gap-2">
                  <input
                    type="text"
                    value={customQuery}
                    onChange={(e) => setCustomQuery(e.target.value)}
                    placeholder="e.g., 'group by category', 'sum amount', 'average price'"
                    className="flex-1 px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100"
                  />
                  <button
                    onClick={handleCustomQuery}
                    className="px-4 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 transition-colors"
                  >
                    Apply
                  </button>
                </div>
              </div>
            </div>
          )}
        </div>
      )}

      {/* Visualization Container */}
      <div className="bg-white dark:bg-gray-900 rounded-lg p-4 border border-gray-200 dark:border-gray-700">
        {renderVisualization()}
      </div>

      {/* Data Summary */}
      {chartData && chartData.length > 0 && (
        <div className="text-sm text-gray-600 dark:text-gray-400">
          Showing {chartData.length} data points
        </div>
      )}
    </div>
  );
};

export default DataVisualization;