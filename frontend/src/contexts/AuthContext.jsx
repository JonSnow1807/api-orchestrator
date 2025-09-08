import React, { createContext, useState, useContext, useEffect } from 'react';
import axios from 'axios';

const AuthContext = createContext({});

// Use relative URL in production (same origin), or environment variable, or fallback to localhost
const API_BASE_URL = import.meta.env.VITE_API_URL || 
  (import.meta.env.PROD ? '' : 'http://localhost:8000');

// Configure axios defaults
axios.defaults.baseURL = API_BASE_URL;

export const useAuth = () => useContext(AuthContext);

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Check if user is logged in on mount
  useEffect(() => {
    const token = localStorage.getItem('access_token');
    if (token) {
      axios.defaults.headers.common['Authorization'] = `Bearer ${token}`;
      fetchCurrentUser();
    } else {
      setLoading(false);
    }
  }, []);

  const fetchCurrentUser = async () => {
    try {
      const response = await axios.get('/auth/me');
      setUser(response.data);
    } catch (error) {
      console.error('Failed to fetch user:', error);
      localStorage.removeItem('access_token');
      localStorage.removeItem('refresh_token');
      delete axios.defaults.headers.common['Authorization'];
    } finally {
      setLoading(false);
    }
  };

  const login = async (email, password, rememberMe = false) => {
    try {
      setError(null);
      console.log('Attempting login with email:', email, 'Remember Me:', rememberMe);
      
      // OAuth2 expects form data
      const formData = new URLSearchParams();
      formData.append('username', email); // OAuth2 uses 'username' field for email
      formData.append('password', password);
      formData.append('remember_me', rememberMe.toString());

      const response = await axios.post('/auth/login', formData, {
        headers: {
          'Content-Type': 'application/x-www-form-urlencoded',
        },
      });

      const { access_token, refresh_token } = response.data;
      
      // Store tokens
      localStorage.setItem('access_token', access_token);
      if (refresh_token) {
        localStorage.setItem('refresh_token', refresh_token);
      }
      
      // Set authorization header
      axios.defaults.headers.common['Authorization'] = `Bearer ${access_token}`;
      
      // Fetch user info
      await fetchCurrentUser();
      
      return { success: true };
    } catch (error) {
      console.error('Login error:', error.response?.status, error.response?.data);
      let message = 'Login failed';
      
      if (error.response?.status === 401) {
        message = 'Incorrect email or password';
      } else if (error.response?.data?.detail) {
        message = error.response.data.detail;
      }
      
      setError(message);
      return { success: false, error: message };
    }
  };

  const register = async (email, username, password) => {
    try {
      setError(null);
      const response = await axios.post('/auth/register', {
        email,
        username,
        password,
      });

      // Auto-login after successful registration
      if (response.status === 201) {
        return await login(email, password, false);
      }
      
      return { success: true };
    } catch (error) {
      const message = error.response?.data?.detail || 'Registration failed';
      setError(message);
      return { success: false, error: message };
    }
  };

  const logout = async () => {
    // Clear auth data first to prevent infinite loops
    const token = localStorage.getItem('access_token');
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
    delete axios.defaults.headers.common['Authorization'];
    setUser(null);
    
    // Try to call logout endpoint if token existed
    if (token) {
      try {
        // Create a custom axios instance to bypass interceptors
        const axiosInstance = axios.create();
        await axiosInstance.post('/auth/logout', {}, {
          headers: { 'Authorization': `Bearer ${token}` }
        });
      } catch (error) {
        // Ignore errors - we're logging out anyway
        console.log('Logout API call failed (normal if token was invalid)');
      }
    }
  };

  const refreshToken = async () => {
    try {
      const refresh_token = localStorage.getItem('refresh_token');
      if (!refresh_token) return false;

      const response = await axios.post('/auth/refresh', { refresh_token });
      const { access_token } = response.data;
      
      localStorage.setItem('access_token', access_token);
      axios.defaults.headers.common['Authorization'] = `Bearer ${access_token}`;
      
      return true;
    } catch (error) {
      console.error('Token refresh failed:', error);
      return false;
    }
  };

  // Setup axios interceptor for token refresh
  useEffect(() => {
    const interceptor = axios.interceptors.response.use(
      (response) => response,
      async (error) => {
        const originalRequest = error.config;
        
        // Don't retry on logout endpoint to prevent infinite loop
        if (originalRequest.url?.includes('/auth/logout')) {
          return Promise.reject(error);
        }
        
        if (error.response?.status === 401 && !originalRequest._retry) {
          originalRequest._retry = true;
          
          const refreshed = await refreshToken();
          if (refreshed) {
            return axios(originalRequest);
          } else {
            // Refresh failed, redirect to login
            await logout();
          }
        }
        
        return Promise.reject(error);
      }
    );

    return () => axios.interceptors.response.eject(interceptor);
  }, []);

  const value = {
    user,
    login,
    register,
    logout,
    loading,
    error,
    isAuthenticated: !!user,
  };

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
};