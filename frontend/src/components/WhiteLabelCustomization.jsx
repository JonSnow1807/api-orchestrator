import React, { useState, useEffect } from 'react';
import {
  Box,
  Grid,
  Card,
  CardBody,
  CardHeader,
  Heading,
  Text,
  VStack,
  HStack,
  Button,
  Input,
  FormControl,
  FormLabel,
  FormHelperText,
  Textarea,
  Select,
  Switch,
  Slider,
  SliderTrack,
  SliderFilledTrack,
  SliderThumb,
  ColorPicker,
  useColorModeValue,
  Tabs,
  TabList,
  TabPanels,
  Tab,
  TabPanel,
  Image,
  Badge,
  Alert,
  AlertIcon,
  AlertTitle,
  AlertDescription,
  Divider,
  Code,
  useToast,
  Modal,
  ModalOverlay,
  ModalContent,
  ModalHeader,
  ModalBody,
  ModalCloseButton,
  useDisclosure,
  Progress,
  Spinner
} from '@chakra-ui/react';
import { ChromePicker } from 'react-color';
import {
  FiPalette,
  FiImage,
  FiType,
  FiLayout,
  FiSettings,
  FiDownload,
  FiUpload,
  FiEye,
  FiSave,
  FiRefreshCw,
  FiCopy,
  FiCheck,
  FiX
} from 'react-icons/fi';

const WhiteLabelCustomization = () => {
  const [customization, setCustomization] = useState({
    branding: {
      companyName: 'Your Company',
      logo: null,
      favicon: null,
      tagline: 'Powerful API Testing Platform'
    },
    theme: {
      primaryColor: '#3182CE',
      secondaryColor: '#4A5568',
      accentColor: '#38B2AC',
      backgroundColor: '#FFFFFF',
      textColor: '#1A202C',
      borderColor: '#E2E8F0'
    },
    layout: {
      headerHeight: 64,
      sidebarWidth: 280,
      borderRadius: 8,
      spacing: 4,
      containerMaxWidth: 1200
    },
    features: {
      showBranding: true,
      customDomain: '',
      enableSSO: true,
      showPoweredBy: false,
      customFooter: '',
      enableAnalytics: true
    },
    fonts: {
      headingFont: 'Inter',
      bodyFont: 'Inter',
      codeFont: 'JetBrains Mono'
    }
  });

  const [previewMode, setPreviewMode] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [savedConfigs, setSavedConfigs] = useState([]);
  const { isOpen, onOpen, onClose } = useDisclosure();
  const toast = useToast();

  const cardBg = useColorModeValue('white', 'gray.800');
  const borderColor = useColorModeValue('gray.200', 'gray.600');
  const bgColor = useColorModeValue('gray.50', 'gray.900');

  useEffect(() => {
    loadSavedConfigurations();
  }, []);

  const loadSavedConfigurations = async () => {
    try {
      const response = await fetch('/api/v1/customization/configs');
      const configs = await response.json();
      setSavedConfigs(configs);
    } catch (error) {
      console.error('Error loading configurations:', error);
    }
  };

  const updateCustomization = (section, field, value) => {
    setCustomization(prev => ({
      ...prev,
      [section]: {
        ...prev[section],
        [field]: value
      }
    }));
  };

  const handleFileUpload = async (file, type) => {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('type', type);

    try {
      setIsLoading(true);
      const response = await fetch('/api/v1/customization/upload', {
        method: 'POST',
        body: formData
      });

      const result = await response.json();

      if (response.ok) {
        updateCustomization('branding', type, result.url);
        toast({
          title: 'Upload Successful',
          description: `${type} uploaded successfully`,
          status: 'success',
          duration: 3000,
          isClosable: true,
        });
      }
    } catch (error) {
      toast({
        title: 'Upload Failed',
        description: `Failed to upload ${type}`,
        status: 'error',
        duration: 3000,
        isClosable: true,
      });
    } finally {
      setIsLoading(false);
    }
  };

  const saveConfiguration = async () => {
    try {
      setIsLoading(true);
      const response = await fetch('/api/v1/customization/save', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(customization)
      });

      if (response.ok) {
        toast({
          title: 'Configuration Saved',
          description: 'Your customization has been saved successfully',
          status: 'success',
          duration: 3000,
          isClosable: true,
        });
        loadSavedConfigurations();
      }
    } catch (error) {
      toast({
        title: 'Save Failed',
        description: 'Failed to save configuration',
        status: 'error',
        duration: 3000,
        isClosable: true,
      });
    } finally {
      setIsLoading(false);
    }
  };

  const exportConfiguration = () => {
    const dataStr = JSON.stringify(customization, null, 2);
    const dataBlob = new Blob([dataStr], { type: 'application/json' });
    const url = URL.createObjectURL(dataBlob);
    const link = document.createElement('a');
    link.href = url;
    link.download = 'whitelabel-config.json';
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
  };

  const importConfiguration = (event) => {
    const file = event.target.files[0];
    if (file) {
      const reader = new FileReader();
      reader.onload = (e) => {
        try {
          const config = JSON.parse(e.target.result);
          setCustomization(config);
          toast({
            title: 'Configuration Imported',
            description: 'Configuration imported successfully',
            status: 'success',
            duration: 3000,
            isClosable: true,
          });
        } catch (error) {
          toast({
            title: 'Import Failed',
            description: 'Invalid configuration file',
            status: 'error',
            duration: 3000,
            isClosable: true,
          });
        }
      };
      reader.readAsText(file);
    }
  };

  const generateCSS = () => {
    return `
/* White Label Customization CSS */
:root {
  --primary-color: ${customization.theme.primaryColor};
  --secondary-color: ${customization.theme.secondaryColor};
  --accent-color: ${customization.theme.accentColor};
  --background-color: ${customization.theme.backgroundColor};
  --text-color: ${customization.theme.textColor};
  --border-color: ${customization.theme.borderColor};
  --border-radius: ${customization.layout.borderRadius}px;
  --header-height: ${customization.layout.headerHeight}px;
  --sidebar-width: ${customization.layout.sidebarWidth}px;
  --container-max-width: ${customization.layout.containerMaxWidth}px;
  --font-heading: '${customization.fonts.headingFont}', sans-serif;
  --font-body: '${customization.fonts.bodyFont}', sans-serif;
  --font-code: '${customization.fonts.codeFont}', monospace;
}

/* Apply custom branding */
.brand-logo {
  content: url('${customization.branding.logo || '/default-logo.png'}');
  max-height: 40px;
}

.brand-name::after {
  content: '${customization.branding.companyName}';
}

.brand-tagline::after {
  content: '${customization.branding.tagline}';
}

/* Theme colors */
.primary-bg { background-color: var(--primary-color); }
.secondary-bg { background-color: var(--secondary-color); }
.accent-bg { background-color: var(--accent-color); }

/* Typography */
h1, h2, h3, h4, h5, h6 { font-family: var(--font-heading); }
body, p, span { font-family: var(--font-body); }
code, pre { font-family: var(--font-code); }

/* Layout */
.container { max-width: var(--container-max-width); }
.header { height: var(--header-height); }
.sidebar { width: var(--sidebar-width); }
`;
  };

  const renderBrandingTab = () => (
    <VStack spacing={6} align="stretch">
      <Card bg={cardBg} borderColor={borderColor}>
        <CardHeader>
          <Heading size="md">Company Branding</Heading>
        </CardHeader>
        <CardBody>
          <VStack spacing={4} align="stretch">
            <FormControl>
              <FormLabel>Company Name</FormLabel>
              <Input
                value={customization.branding.companyName}
                onChange={(e) => updateCustomization('branding', 'companyName', e.target.value)}
                placeholder="Enter your company name"
              />
            </FormControl>

            <FormControl>
              <FormLabel>Tagline</FormLabel>
              <Input
                value={customization.branding.tagline}
                onChange={(e) => updateCustomization('branding', 'tagline', e.target.value)}
                placeholder="Enter your company tagline"
              />
            </FormControl>

            <Grid templateColumns="repeat(auto-fit, minmax(300px, 1fr))" gap={4}>
              <FormControl>
                <FormLabel>Logo Upload</FormLabel>
                <VStack spacing={3}>
                  {customization.branding.logo && (
                    <Image src={customization.branding.logo} maxH="100px" />
                  )}
                  <Input
                    type="file"
                    accept="image/*"
                    onChange={(e) => handleFileUpload(e.target.files[0], 'logo')}
                  />
                  <FormHelperText>Recommended size: 200x60px, PNG/SVG format</FormHelperText>
                </VStack>
              </FormControl>

              <FormControl>
                <FormLabel>Favicon Upload</FormLabel>
                <VStack spacing={3}>
                  {customization.branding.favicon && (
                    <Image src={customization.branding.favicon} maxH="32px" />
                  )}
                  <Input
                    type="file"
                    accept="image/*"
                    onChange={(e) => handleFileUpload(e.target.files[0], 'favicon')}
                  />
                  <FormHelperText>Recommended size: 32x32px, ICO/PNG format</FormHelperText>
                </VStack>
              </FormControl>
            </Grid>
          </VStack>
        </CardBody>
      </Card>
    </VStack>
  );

  const ColorPickerControl = ({ label, value, onChange, helperText }) => {
    const [showPicker, setShowPicker] = useState(false);

    return (
      <FormControl>
        <FormLabel>{label}</FormLabel>
        <HStack>
          <Box
            width="40px"
            height="40px"
            bg={value}
            border="1px solid"
            borderColor={borderColor}
            borderRadius="md"
            cursor="pointer"
            onClick={() => setShowPicker(!showPicker)}
          />
          <Input value={value} onChange={(e) => onChange(e.target.value)} />
        </HStack>
        {helperText && <FormHelperText>{helperText}</FormHelperText>}
        {showPicker && (
          <Box position="absolute" zIndex={2} mt={2}>
            <Box
              position="fixed"
              top="0"
              left="0"
              right="0"
              bottom="0"
              onClick={() => setShowPicker(false)}
            />
            <ChromePicker
              color={value}
              onChange={(color) => onChange(color.hex)}
            />
          </Box>
        )}
      </FormControl>
    );
  };

  const renderThemeTab = () => (
    <VStack spacing={6} align="stretch">
      <Card bg={cardBg} borderColor={borderColor}>
        <CardHeader>
          <Heading size="md">Color Scheme</Heading>
        </CardHeader>
        <CardBody>
          <Grid templateColumns="repeat(auto-fit, minmax(250px, 1fr))" gap={4}>
            <ColorPickerControl
              label="Primary Color"
              value={customization.theme.primaryColor}
              onChange={(value) => updateCustomization('theme', 'primaryColor', value)}
              helperText="Used for buttons, links, and accents"
            />
            <ColorPickerControl
              label="Secondary Color"
              value={customization.theme.secondaryColor}
              onChange={(value) => updateCustomization('theme', 'secondaryColor', value)}
              helperText="Used for secondary elements"
            />
            <ColorPickerControl
              label="Accent Color"
              value={customization.theme.accentColor}
              onChange={(value) => updateCustomization('theme', 'accentColor', value)}
              helperText="Used for highlights and notifications"
            />
            <ColorPickerControl
              label="Background Color"
              value={customization.theme.backgroundColor}
              onChange={(value) => updateCustomization('theme', 'backgroundColor', value)}
              helperText="Main background color"
            />
            <ColorPickerControl
              label="Text Color"
              value={customization.theme.textColor}
              onChange={(value) => updateCustomization('theme', 'textColor', value)}
              helperText="Primary text color"
            />
            <ColorPickerControl
              label="Border Color"
              value={customization.theme.borderColor}
              onChange={(value) => updateCustomization('theme', 'borderColor', value)}
              helperText="Used for borders and dividers"
            />
          </Grid>
        </CardBody>
      </Card>

      <Card bg={cardBg} borderColor={borderColor}>
        <CardHeader>
          <Heading size="md">Typography</Heading>
        </CardHeader>
        <CardBody>
          <Grid templateColumns="repeat(auto-fit, minmax(250px, 1fr))" gap={4}>
            <FormControl>
              <FormLabel>Heading Font</FormLabel>
              <Select
                value={customization.fonts.headingFont}
                onChange={(e) => updateCustomization('fonts', 'headingFont', e.target.value)}
              >
                <option value="Inter">Inter</option>
                <option value="Roboto">Roboto</option>
                <option value="Open Sans">Open Sans</option>
                <option value="Poppins">Poppins</option>
                <option value="Montserrat">Montserrat</option>
              </Select>
            </FormControl>

            <FormControl>
              <FormLabel>Body Font</FormLabel>
              <Select
                value={customization.fonts.bodyFont}
                onChange={(e) => updateCustomization('fonts', 'bodyFont', e.target.value)}
              >
                <option value="Inter">Inter</option>
                <option value="Roboto">Roboto</option>
                <option value="Open Sans">Open Sans</option>
                <option value="Source Sans Pro">Source Sans Pro</option>
                <option value="Lato">Lato</option>
              </Select>
            </FormControl>

            <FormControl>
              <FormLabel>Code Font</FormLabel>
              <Select
                value={customization.fonts.codeFont}
                onChange={(e) => updateCustomization('fonts', 'codeFont', e.target.value)}
              >
                <option value="JetBrains Mono">JetBrains Mono</option>
                <option value="Fira Code">Fira Code</option>
                <option value="Source Code Pro">Source Code Pro</option>
                <option value="Monaco">Monaco</option>
                <option value="Consolas">Consolas</option>
              </Select>
            </FormControl>
          </Grid>
        </CardBody>
      </Card>
    </VStack>
  );

  const renderLayoutTab = () => (
    <VStack spacing={6} align="stretch">
      <Card bg={cardBg} borderColor={borderColor}>
        <CardHeader>
          <Heading size="md">Layout Settings</Heading>
        </CardHeader>
        <CardBody>
          <VStack spacing={6} align="stretch">
            <FormControl>
              <FormLabel>Header Height: {customization.layout.headerHeight}px</FormLabel>
              <Slider
                value={customization.layout.headerHeight}
                onChange={(value) => updateCustomization('layout', 'headerHeight', value)}
                min={48}
                max={120}
                step={4}
              >
                <SliderTrack>
                  <SliderFilledTrack />
                </SliderTrack>
                <SliderThumb />
              </Slider>
            </FormControl>

            <FormControl>
              <FormLabel>Sidebar Width: {customization.layout.sidebarWidth}px</FormLabel>
              <Slider
                value={customization.layout.sidebarWidth}
                onChange={(value) => updateCustomization('layout', 'sidebarWidth', value)}
                min={200}
                max={400}
                step={10}
              >
                <SliderTrack>
                  <SliderFilledTrack />
                </SliderTrack>
                <SliderThumb />
              </Slider>
            </FormControl>

            <FormControl>
              <FormLabel>Border Radius: {customization.layout.borderRadius}px</FormLabel>
              <Slider
                value={customization.layout.borderRadius}
                onChange={(value) => updateCustomization('layout', 'borderRadius', value)}
                min={0}
                max={20}
                step={1}
              >
                <SliderTrack>
                  <SliderFilledTrack />
                </SliderTrack>
                <SliderThumb />
              </Slider>
            </FormControl>

            <FormControl>
              <FormLabel>Container Max Width: {customization.layout.containerMaxWidth}px</FormLabel>
              <Slider
                value={customization.layout.containerMaxWidth}
                onChange={(value) => updateCustomization('layout', 'containerMaxWidth', value)}
                min={960}
                max={1600}
                step={40}
              >
                <SliderTrack>
                  <SliderFilledTrack />
                </SliderTrack>
                <SliderThumb />
              </Slider>
            </FormControl>
          </VStack>
        </CardBody>
      </Card>
    </VStack>
  );

  const renderFeaturesTab = () => (
    <VStack spacing={6} align="stretch">
      <Card bg={cardBg} borderColor={borderColor}>
        <CardHeader>
          <Heading size="md">Feature Configuration</Heading>
        </CardHeader>
        <CardBody>
          <VStack spacing={4} align="stretch">
            <HStack justify="space-between">
              <VStack align="start" spacing={1}>
                <Text fontWeight="semibold">Show Company Branding</Text>
                <Text fontSize="sm" color="gray.500">Display your company logo and name</Text>
              </VStack>
              <Switch
                isChecked={customization.features.showBranding}
                onChange={(e) => updateCustomization('features', 'showBranding', e.target.checked)}
              />
            </HStack>

            <Divider />

            <FormControl>
              <FormLabel>Custom Domain</FormLabel>
              <Input
                value={customization.features.customDomain}
                onChange={(e) => updateCustomization('features', 'customDomain', e.target.value)}
                placeholder="api.yourcompany.com"
              />
              <FormHelperText>Configure your custom domain for the white-label instance</FormHelperText>
            </FormControl>

            <HStack justify="space-between">
              <VStack align="start" spacing={1}>
                <Text fontWeight="semibold">Enable SSO Integration</Text>
                <Text fontSize="sm" color="gray.500">Allow single sign-on authentication</Text>
              </VStack>
              <Switch
                isChecked={customization.features.enableSSO}
                onChange={(e) => updateCustomization('features', 'enableSSO', e.target.checked)}
              />
            </HStack>

            <HStack justify="space-between">
              <VStack align="start" spacing={1}>
                <Text fontWeight="semibold">Show "Powered By" Attribution</Text>
                <Text fontSize="sm" color="gray.500">Display attribution in footer</Text>
              </VStack>
              <Switch
                isChecked={customization.features.showPoweredBy}
                onChange={(e) => updateCustomization('features', 'showPoweredBy', e.target.checked)}
              />
            </HStack>

            <FormControl>
              <FormLabel>Custom Footer Text</FormLabel>
              <Textarea
                value={customization.features.customFooter}
                onChange={(e) => updateCustomization('features', 'customFooter', e.target.value)}
                placeholder="© 2025 Your Company. All rights reserved."
                rows={3}
              />
            </FormControl>

            <HStack justify="space-between">
              <VStack align="start" spacing={1}>
                <Text fontWeight="semibold">Enable Advanced Analytics</Text>
                <Text fontSize="sm" color="gray.500">Track usage and performance metrics</Text>
              </VStack>
              <Switch
                isChecked={customization.features.enableAnalytics}
                onChange={(e) => updateCustomization('features', 'enableAnalytics', e.target.checked)}
              />
            </HStack>
          </VStack>
        </CardBody>
      </Card>
    </VStack>
  );

  const renderPreviewTab = () => (
    <VStack spacing={6} align="stretch">
      <Card bg={cardBg} borderColor={borderColor}>
        <CardHeader>
          <HStack justify="space-between">
            <Heading size="md">Live Preview</Heading>
            <Badge colorScheme="blue" variant="solid">PREVIEW MODE</Badge>
          </HStack>
        </CardHeader>
        <CardBody>
          <Box
            border="2px solid"
            borderColor={borderColor}
            borderRadius="lg"
            overflow="hidden"
            bg={customization.theme.backgroundColor}
            color={customization.theme.textColor}
            minH="400px"
          >
            {/* Mock Header */}
            <Box
              bg={customization.theme.primaryColor}
              color="white"
              h={`${customization.layout.headerHeight}px`}
              display="flex"
              alignItems="center"
              px={4}
            >
              <HStack spacing={4}>
                {customization.branding.logo && (
                  <Image src={customization.branding.logo} maxH="32px" />
                )}
                <Text fontWeight="bold" fontFamily={customization.fonts.headingFont}>
                  {customization.branding.companyName}
                </Text>
              </HStack>
            </Box>

            {/* Mock Content */}
            <Box p={6}>
              <VStack align="start" spacing={4}>
                <Heading
                  size="lg"
                  fontFamily={customization.fonts.headingFont}
                  color={customization.theme.textColor}
                >
                  Welcome to {customization.branding.companyName}
                </Heading>
                <Text
                  fontSize="lg"
                  color={customization.theme.secondaryColor}
                  fontFamily={customization.fonts.bodyFont}
                >
                  {customization.branding.tagline}
                </Text>

                <HStack spacing={4} pt={4}>
                  <Button
                    bg={customization.theme.primaryColor}
                    color="white"
                    borderRadius={`${customization.layout.borderRadius}px`}
                    _hover={{ opacity: 0.9 }}
                  >
                    Primary Button
                  </Button>
                  <Button
                    variant="outline"
                    borderColor={customization.theme.primaryColor}
                    color={customization.theme.primaryColor}
                    borderRadius={`${customization.layout.borderRadius}px`}
                  >
                    Secondary Button
                  </Button>
                </HStack>

                <Box
                  bg={customization.theme.accentColor}
                  color="white"
                  p={4}
                  borderRadius={`${customization.layout.borderRadius}px`}
                  mt={6}
                >
                  <Text fontWeight="semibold">Accent Color Example</Text>
                  <Text fontSize="sm">This shows how your accent color will appear</Text>
                </Box>
              </VStack>
            </Box>

            {/* Mock Footer */}
            {customization.features.customFooter && (
              <Box
                borderTop="1px solid"
                borderColor={customization.theme.borderColor}
                p={4}
                mt={6}
              >
                <Text
                  fontSize="sm"
                  color={customization.theme.secondaryColor}
                  fontFamily={customization.fonts.bodyFont}
                >
                  {customization.features.customFooter}
                </Text>
              </Box>
            )}
          </Box>
        </CardBody>
      </Card>

      <Card bg={cardBg} borderColor={borderColor}>
        <CardHeader>
          <Heading size="md">Generated CSS</Heading>
        </CardHeader>
        <CardBody>
          <Box position="relative">
            <Code
              display="block"
              whiteSpace="pre"
              p={4}
              fontSize="sm"
              bg={bgColor}
              borderRadius="md"
              maxH="300px"
              overflow="auto"
            >
              {generateCSS()}
            </Code>
            <Button
              position="absolute"
              top={2}
              right={2}
              size="sm"
              leftIcon={<FiCopy />}
              onClick={() => {
                navigator.clipboard.writeText(generateCSS());
                toast({
                  title: 'CSS Copied',
                  description: 'CSS code copied to clipboard',
                  status: 'success',
                  duration: 2000,
                  isClosable: true,
                });
              }}
            >
              Copy CSS
            </Button>
          </Box>
        </CardBody>
      </Card>
    </VStack>
  );

  return (
    <Box p={6}>
      <VStack align="start" spacing={6}>
        {/* Header */}
        <HStack justify="space-between" width="100%">
          <VStack align="start" spacing={1}>
            <Heading size="lg">🎨 White Label Customization</Heading>
            <Text color="gray.500">
              Customize the platform with your branding and theme
            </Text>
          </VStack>

          <HStack>
            <Button
              leftIcon={<FiUpload />}
              size="sm"
              variant="outline"
              as="label"
              htmlFor="import-config"
            >
              Import Config
              <Input
                id="import-config"
                type="file"
                accept=".json"
                onChange={importConfiguration}
                style={{ display: 'none' }}
              />
            </Button>
            <Button
              leftIcon={<FiDownload />}
              size="sm"
              variant="outline"
              onClick={exportConfiguration}
            >
              Export Config
            </Button>
            <Button
              leftIcon={<FiSave />}
              size="sm"
              colorScheme="blue"
              onClick={saveConfiguration}
              isLoading={isLoading}
            >
              Save Changes
            </Button>
          </HStack>
        </HStack>

        {/* Configuration Status */}
        <Alert status="info" borderRadius="lg">
          <AlertIcon />
          <Box>
            <AlertTitle>White Label Configuration</AlertTitle>
            <AlertDescription>
              Customize your platform's appearance and branding. Changes are applied in real-time in the preview tab.
            </AlertDescription>
          </Box>
        </Alert>

        {/* Main Configuration Interface */}
        <Tabs variant="enclosed" width="100%">
          <TabList>
            <Tab><FiImage style={{ marginRight: 8 }} />Branding</Tab>
            <Tab><FiPalette style={{ marginRight: 8 }} />Theme</Tab>
            <Tab><FiLayout style={{ marginRight: 8 }} />Layout</Tab>
            <Tab><FiSettings style={{ marginRight: 8 }} />Features</Tab>
            <Tab><FiEye style={{ marginRight: 8 }} />Preview</Tab>
          </TabList>

          <TabPanels>
            <TabPanel>{renderBrandingTab()}</TabPanel>
            <TabPanel>{renderThemeTab()}</TabPanel>
            <TabPanel>{renderLayoutTab()}</TabPanel>
            <TabPanel>{renderFeaturesTab()}</TabPanel>
            <TabPanel>{renderPreviewTab()}</TabPanel>
          </TabPanels>
        </Tabs>

        {/* Saved Configurations */}
        {savedConfigs.length > 0 && (
          <Card bg={cardBg} borderColor={borderColor} width="100%">
            <CardHeader>
              <Heading size="md">Saved Configurations</Heading>
            </CardHeader>
            <CardBody>
              <Grid templateColumns="repeat(auto-fit, minmax(300px, 1fr))" gap={4}>
                {savedConfigs.map((config, index) => (
                  <Box
                    key={index}
                    p={4}
                    border="1px solid"
                    borderColor={borderColor}
                    borderRadius="md"
                    cursor="pointer"
                    _hover={{ bg: bgColor }}
                    onClick={() => setCustomization(config.data)}
                  >
                    <VStack align="start" spacing={2}>
                      <Text fontWeight="semibold">{config.name}</Text>
                      <Text fontSize="sm" color="gray.500">
                        {config.description}
                      </Text>
                      <Badge variant="outline">
                        {new Date(config.createdAt).toLocaleDateString()}
                      </Badge>
                    </VStack>
                  </Box>
                ))}
              </Grid>
            </CardBody>
          </Card>
        )}
      </VStack>
    </Box>
  );
};

export default WhiteLabelCustomization;