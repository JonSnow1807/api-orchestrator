import React, { lazy, Suspense } from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider } from './contexts/AuthContext';
import { ToastProvider } from './contexts/ToastContext';
import ErrorBoundary from './components/ErrorBoundary';
import LoadingSkeleton from './components/LoadingSkeleton';
import PrivateRoute from './components/PrivateRoute';

// Lazy load heavy components
const LandingPage = lazy(() => import('./components/LandingPage'));
const Login = lazy(() => import('./components/Login'));
const Register = lazy(() => import('./components/Register'));
const Dashboard = lazy(() => import('./components/Dashboard'));
const ProjectCreate = lazy(() => import('./components/ProjectCreate'));
const ProjectDetails = lazy(() => import('./components/ProjectDetails'));
const UserProfile = lazy(() => import('./components/UserProfile'));
const Billing = lazy(() => import('./components/Billing'));
const PricingPage = lazy(() => import('./components/PricingPage'));

function App() {
  return (
    <ErrorBoundary>
      <Router>
        <AuthProvider>
          <ToastProvider>
            <Suspense fallback={<LoadingSkeleton />}>
              <Routes>
          {/* Public Routes */}
          <Route path="/login" element={<Login />} />
          <Route path="/register" element={<Register />} />
          
          {/* Protected Routes */}
          <Route path="/dashboard" element={
            <PrivateRoute>
              <Dashboard />
            </PrivateRoute>
          } />
          
          <Route path="/create-project" element={
            <PrivateRoute>
              <ProjectCreate />
            </PrivateRoute>
          } />
          
          <Route path="/projects/:id" element={
            <PrivateRoute>
              <ProjectDetails />
            </PrivateRoute>
          } />
          
          <Route path="/profile" element={
            <PrivateRoute>
              <UserProfile />
            </PrivateRoute>
          } />
          
          <Route path="/billing" element={
            <PrivateRoute>
              <Billing />
            </PrivateRoute>
          } />
          
          {/* Pricing route - shows public pricing page */}
          <Route path="/pricing" element={<PricingPage />} />
          
          {/* Landing Page */}
          <Route path="/" element={<LandingPage />} />
          
          {/* Catch all - redirect to landing */}
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
            </Suspense>
          </ToastProvider>
        </AuthProvider>
      </Router>
    </ErrorBoundary>
  );
}

export default App;