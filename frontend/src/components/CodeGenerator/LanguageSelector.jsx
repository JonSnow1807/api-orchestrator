import React, { useState, useMemo } from 'react';
import {
  Box,
  TextField,
  Autocomplete,
  Chip,
  Grid,
  Typography,
  ToggleButton,
  ToggleButtonGroup,
  Paper,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
  ListItemSecondaryAction,
  IconButton,
  InputAdornment,
  Tooltip,
  Badge,
  Avatar,
  Tabs,
  Tab,
} from '@mui/material';
import {
  Search as SearchIcon,
  Star as StarIcon,
  StarBorder as StarBorderIcon,
  History as HistoryIcon,
  TrendingUp as TrendingIcon,
  Code as CodeIcon,
  Speed as SpeedIcon,
  Security as SecurityIcon,
} from '@mui/icons-material';

const LANGUAGES = {
  javascript: {
    name: 'JavaScript',
    icon: '🟨',
    libraries: ['axios', 'fetch', 'node-fetch', 'got', 'superagent', 'request', 'needle'],
    popular: true,
    category: 'web',
  },
  typescript: {
    name: 'TypeScript',
    icon: '🔷',
    libraries: ['axios', 'fetch', 'node-fetch', 'got', 'typed-rest-client'],
    popular: true,
    category: 'web',
  },
  python: {
    name: 'Python',
    icon: '🐍',
    libraries: ['requests', 'aiohttp', 'httpx', 'urllib3', 'pycurl', 'treq'],
    popular: true,
    category: 'scripting',
  },
  java: {
    name: 'Java',
    icon: '☕',
    libraries: ['okhttp', 'retrofit', 'apache-httpclient', 'spring-resttemplate', 'jersey', 'unirest'],
    popular: true,
    category: 'enterprise',
  },
  csharp: {
    name: 'C#',
    icon: '🔵',
    libraries: ['httpclient', 'restsharp', 'flurl', 'refit', 'servicestack'],
    popular: true,
    category: 'enterprise',
  },
  go: {
    name: 'Go',
    icon: '🐹',
    libraries: ['net/http', 'resty', 'gentleman', 'grequests', 'heimdall'],
    popular: true,
    category: 'systems',
  },
  ruby: {
    name: 'Ruby',
    icon: '💎',
    libraries: ['net/http', 'restclient', 'faraday', 'httparty', 'typhoeus'],
    popular: false,
    category: 'scripting',
  },
  php: {
    name: 'PHP',
    icon: '🐘',
    libraries: ['curl', 'guzzle', 'symfony-httpclient', 'buzz', 'httpful'],
    popular: true,
    category: 'web',
  },
  swift: {
    name: 'Swift',
    icon: '🦉',
    libraries: ['urlsession', 'alamofire', 'moya', 'networking', 'siesta'],
    popular: false,
    category: 'mobile',
  },
  kotlin: {
    name: 'Kotlin',
    icon: '🟣',
    libraries: ['okhttp', 'retrofit', 'ktor', 'fuel', 'volley'],
    popular: true,
    category: 'mobile',
  },
  rust: {
    name: 'Rust',
    icon: '🦀',
    libraries: ['reqwest', 'hyper', 'surf', 'ureq', 'attohttpc'],
    popular: false,
    category: 'systems',
  },
  cpp: {
    name: 'C++',
    icon: '⚙️',
    libraries: ['curl', 'cpprestsdk', 'poco', 'beast', 'cpp-httplib'],
    popular: false,
    category: 'systems',
  },
  dart: {
    name: 'Dart/Flutter',
    icon: '🎯',
    libraries: ['http', 'dio', 'chopper', 'retrofit', 'http_interceptor'],
    popular: false,
    category: 'mobile',
  },
  scala: {
    name: 'Scala',
    icon: '🔴',
    libraries: ['akka-http', 'sttp', 'scalaj-http', 'dispatch', 'newman'],
    popular: false,
    category: 'enterprise',
  },
  elixir: {
    name: 'Elixir',
    icon: '💧',
    libraries: ['httpoison', 'tesla', 'finch', 'mint', 'gun'],
    popular: false,
    category: 'functional',
  },
  perl: {
    name: 'Perl',
    icon: '🐪',
    libraries: ['lwp', 'http-tiny', 'mojo-useragent', 'furl', 'anyevent-http'],
    popular: false,
    category: 'scripting',
  },
  r: {
    name: 'R',
    icon: '📊',
    libraries: ['httr', 'rcurl', 'httr2', 'curl', 'crul'],
    popular: false,
    category: 'data',
  },
  matlab: {
    name: 'MATLAB',
    icon: '📈',
    libraries: ['webread', 'webwrite', 'urlread', 'webservices'],
    popular: false,
    category: 'data',
  },
  shell: {
    name: 'Shell/Bash',
    icon: '🖥️',
    libraries: ['curl', 'wget', 'httpie', 'aria2', 'lynx'],
    popular: true,
    category: 'scripting',
  },
  powershell: {
    name: 'PowerShell',
    icon: '🔷',
    libraries: ['invoke-restmethod', 'invoke-webrequest', 'system.net.webclient', 'restmethod'],
    popular: false,
    category: 'scripting',
  },
  objectivec: {
    name: 'Objective-C',
    icon: '🍎',
    libraries: ['nsurlsession', 'afnetworking', 'restkit', 'mknetworkkit'],
    popular: false,
    category: 'mobile',
  },
  lua: {
    name: 'Lua',
    icon: '🌙',
    libraries: ['socket.http', 'luasocket', 'lua-requests', 'lua-curl'],
    popular: false,
    category: 'scripting',
  },
  haskell: {
    name: 'Haskell',
    icon: '🎓',
    libraries: ['http-client', 'wreq', 'req', 'http-conduit'],
    popular: false,
    category: 'functional',
  },
  clojure: {
    name: 'Clojure',
    icon: '🔮',
    libraries: ['clj-http', 'http-kit', 'aleph', 'clj-ajax'],
    popular: false,
    category: 'functional',
  },
  fsharp: {
    name: 'F#',
    icon: '🔷',
    libraries: ['fsharp.data', 'httpclient', 'fshttp', 'http.fs'],
    popular: false,
    category: 'functional',
  },
  julia: {
    name: 'Julia',
    icon: '🔬',
    libraries: ['http.jl', 'requests.jl', 'httpclient.jl', 'curl.jl'],
    popular: false,
    category: 'data',
  },
  groovy: {
    name: 'Groovy',
    icon: '🎸',
    libraries: ['httpbuilder', 'rest-client', 'http-builder-ng', 'groovy-wslite'],
    popular: false,
    category: 'enterprise',
  },
  crystal: {
    name: 'Crystal',
    icon: '💎',
    libraries: ['http-client', 'crest', 'halite', 'http'],
    popular: false,
    category: 'systems',
  },
  nim: {
    name: 'Nim',
    icon: '👑',
    libraries: ['httpclient', 'asynchttpclient', 'puppy', 'fetch'],
    popular: false,
    category: 'systems',
  },
  ocaml: {
    name: 'OCaml',
    icon: '🐫',
    libraries: ['cohttp', 'ocurl', 'httpaf', 'piaf'],
    popular: false,
    category: 'functional',
  },
};

const CATEGORIES = {
  all: { label: 'All Languages', icon: <CodeIcon /> },
  web: { label: 'Web', icon: '🌐' },
  mobile: { label: 'Mobile', icon: '📱' },
  enterprise: { label: 'Enterprise', icon: '🏢' },
  systems: { label: 'Systems', icon: '⚙️' },
  scripting: { label: 'Scripting', icon: '📜' },
  functional: { label: 'Functional', icon: '🔮' },
  data: { label: 'Data Science', icon: '📊' },
};

const LanguageSelector = ({
  selectedLanguage,
  selectedLibrary,
  onLanguageChange,
  onLibraryChange,
  favorites,
  onToggleFavorite,
  history,
}) => {
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedCategory, setSelectedCategory] = useState('all');
  const [viewMode, setViewMode] = useState('grid'); // grid or list

  const filteredLanguages = useMemo(() => {
    return Object.entries(LANGUAGES).filter(([key, lang]) => {
      const matchesSearch = searchQuery === '' ||
        lang.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
        key.toLowerCase().includes(searchQuery.toLowerCase());
      
      const matchesCategory = selectedCategory === 'all' || lang.category === selectedCategory;
      
      return matchesSearch && matchesCategory;
    });
  }, [searchQuery, selectedCategory]);

  const popularLanguages = useMemo(() => {
    return Object.entries(LANGUAGES)
      .filter(([_, lang]) => lang.popular)
      .map(([key, _]) => key);
  }, []);

  const handleLanguageClick = (langKey) => {
    onLanguageChange(langKey);
    // Auto-select the first library for the language
    if (LANGUAGES[langKey].libraries.length > 0) {
      onLibraryChange(LANGUAGES[langKey].libraries[0]);
    }
  };

  const getLanguageStats = (langKey) => {
    const isFavorite = favorites.includes(langKey);
    const isRecent = history.slice(0, 5).includes(langKey);
    const isPopular = LANGUAGES[langKey].popular;
    
    return { isFavorite, isRecent, isPopular };
  };

  return (
    <Box>
      {/* Search Bar */}
      <TextField
        fullWidth
        variant="outlined"
        placeholder="Search 30+ languages..."
        value={searchQuery}
        onChange={(e) => setSearchQuery(e.target.value)}
        sx={{ mb: 2 }}
        InputProps={{
          startAdornment: (
            <InputAdornment position="start">
              <SearchIcon />
            </InputAdornment>
          ),
          endAdornment: searchQuery && (
            <InputAdornment position="end">
              <Typography variant="caption" color="text.secondary">
                {filteredLanguages.length} results
              </Typography>
            </InputAdornment>
          ),
        }}
      />

      {/* Category Tabs */}
      <Tabs
        value={selectedCategory}
        onChange={(e, v) => setSelectedCategory(v)}
        variant="scrollable"
        scrollButtons="auto"
        sx={{ mb: 2 }}
      >
        {Object.entries(CATEGORIES).map(([key, cat]) => (
          <Tab
            key={key}
            value={key}
            label={cat.label}
            icon={typeof cat.icon === 'string' ? <span>{cat.icon}</span> : cat.icon}
            iconPosition="start"
          />
        ))}
      </Tabs>

      {/* Quick Access - Favorites & Recent */}
      {!searchQuery && selectedCategory === 'all' && (
        <Box sx={{ mb: 2 }}>
          {/* Favorites */}
          {favorites.length > 0 && (
            <Box sx={{ mb: 1 }}>
              <Typography variant="caption" color="text.secondary" sx={{ mb: 0.5, display: 'block' }}>
                ⭐ Favorites
              </Typography>
              <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap' }}>
                {favorites.map((langKey) => (
                  <Chip
                    key={langKey}
                    label={`${LANGUAGES[langKey]?.icon} ${LANGUAGES[langKey]?.name}`}
                    onClick={() => handleLanguageClick(langKey)}
                    onDelete={() => onToggleFavorite(langKey)}
                    deleteIcon={<StarIcon />}
                    color={selectedLanguage === langKey ? 'primary' : 'default'}
                    variant={selectedLanguage === langKey ? 'filled' : 'outlined'}
                  />
                ))}
              </Box>
            </Box>
          )}

          {/* Recent */}
          {history.length > 0 && (
            <Box>
              <Typography variant="caption" color="text.secondary" sx={{ mb: 0.5, display: 'block' }}>
                🕐 Recent
              </Typography>
              <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap' }}>
                {history.slice(0, 5).map((langKey) => (
                  <Chip
                    key={langKey}
                    label={`${LANGUAGES[langKey]?.icon} ${LANGUAGES[langKey]?.name}`}
                    onClick={() => handleLanguageClick(langKey)}
                    color={selectedLanguage === langKey ? 'primary' : 'default'}
                    variant={selectedLanguage === langKey ? 'filled' : 'outlined'}
                    size="small"
                  />
                ))}
              </Box>
            </Box>
          )}
        </Box>
      )}

      {/* Language Grid */}
      <Grid container spacing={1} sx={{ mb: 2 }}>
        {filteredLanguages.map(([langKey, lang]) => {
          const stats = getLanguageStats(langKey);
          return (
            <Grid item xs={6} sm={4} md={3} key={langKey}>
              <Paper
                sx={{
                  p: 1,
                  cursor: 'pointer',
                  border: selectedLanguage === langKey ? '2px solid' : '1px solid',
                  borderColor: selectedLanguage === langKey ? 'primary.main' : 'divider',
                  backgroundColor: selectedLanguage === langKey ? 'action.selected' : 'background.paper',
                  transition: 'all 0.2s',
                  '&:hover': {
                    borderColor: 'primary.main',
                    transform: 'translateY(-2px)',
                    boxShadow: 2,
                  },
                  position: 'relative',
                }}
                onClick={() => handleLanguageClick(langKey)}
              >
                {/* Badges */}
                <Box sx={{ position: 'absolute', top: 4, right: 4, display: 'flex', gap: 0.5 }}>
                  {stats.isPopular && (
                    <Tooltip title="Popular">
                      <TrendingIcon sx={{ fontSize: 16, color: 'error.main' }} />
                    </Tooltip>
                  )}
                  <Tooltip title={stats.isFavorite ? 'Remove from favorites' : 'Add to favorites'}>
                    <IconButton
                      size="small"
                      onClick={(e) => {
                        e.stopPropagation();
                        onToggleFavorite(langKey);
                      }}
                      sx={{ p: 0 }}
                    >
                      {stats.isFavorite ? (
                        <StarIcon sx={{ fontSize: 16, color: 'warning.main' }} />
                      ) : (
                        <StarBorderIcon sx={{ fontSize: 16 }} />
                      )}
                    </IconButton>
                  </Tooltip>
                </Box>

                {/* Language Info */}
                <Box sx={{ display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
                  <Typography variant="h4" sx={{ mb: 0.5 }}>
                    {lang.icon}
                  </Typography>
                  <Typography variant="caption" noWrap>
                    {lang.name}
                  </Typography>
                  <Typography variant="caption" color="text.secondary">
                    {lang.libraries.length} libraries
                  </Typography>
                </Box>
              </Paper>
            </Grid>
          );
        })}
      </Grid>

      {/* Library Selector for Selected Language */}
      {selectedLanguage && LANGUAGES[selectedLanguage] && (
        <Box>
          <Typography variant="subtitle2" sx={{ mb: 1 }}>
            Select Library for {LANGUAGES[selectedLanguage].name}
          </Typography>
          <ToggleButtonGroup
            value={selectedLibrary}
            exclusive
            onChange={(e, v) => v && onLibraryChange(v)}
            sx={{ flexWrap: 'wrap' }}
          >
            {LANGUAGES[selectedLanguage].libraries.map((lib) => (
              <ToggleButton key={lib} value={lib} size="small">
                {lib}
              </ToggleButton>
            ))}
          </ToggleButtonGroup>
        </Box>
      )}

      {/* Stats */}
      <Box sx={{ mt: 2, p: 1, bgcolor: 'background.default', borderRadius: 1 }}>
        <Grid container spacing={1}>
          <Grid item xs={4}>
            <Box sx={{ textAlign: 'center' }}>
              <Typography variant="h6" color="primary">
                {Object.keys(LANGUAGES).length}
              </Typography>
              <Typography variant="caption" color="text.secondary">
                Languages
              </Typography>
            </Box>
          </Grid>
          <Grid item xs={4}>
            <Box sx={{ textAlign: 'center' }}>
              <Typography variant="h6" color="primary">
                {Object.values(LANGUAGES).reduce((acc, lang) => acc + lang.libraries.length, 0)}
              </Typography>
              <Typography variant="caption" color="text.secondary">
                Libraries
              </Typography>
            </Box>
          </Grid>
          <Grid item xs={4}>
            <Box sx={{ textAlign: 'center' }}>
              <Typography variant="h6" color="primary">
                100%
              </Typography>
              <Typography variant="caption" color="text.secondary">
                Coverage
              </Typography>
            </Box>
          </Grid>
        </Grid>
      </Box>
    </Box>
  );
};

export default LanguageSelector;