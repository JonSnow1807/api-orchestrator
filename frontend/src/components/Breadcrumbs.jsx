import React from 'react';
import { Link, useLocation } from 'react-router-dom';
import { ChevronRight, Home } from 'lucide-react';

const Breadcrumbs = () => {
  const location = useLocation();
  const pathnames = location.pathname.split('/').filter((x) => x);

  // Map paths to user-friendly names
  const pathNameMap = {
    'dashboard': 'Dashboard',
    'projects': 'Projects',
    'create-project': 'Create Project',
    'profile': 'Profile',
    'billing': 'Billing',
    'pricing': 'Pricing',
    'settings': 'Settings',
    'team': 'Team Management',
    'analytics': 'Analytics',
    'documentation': 'Documentation',
    'api': 'API Testing',
    'monitoring': 'Monitoring'
  };

  // Don't show breadcrumbs on landing, login, or register pages
  if (location.pathname === '/' || location.pathname === '/login' || location.pathname === '/register') {
    return null;
  }

  return (
    <nav aria-label="Breadcrumb" className="flex items-center space-x-2 px-4 py-2 bg-gray-800/30 border-b border-gray-700">
      {/* Home link */}
      <Link
        to="/"
        className="flex items-center text-gray-400 hover:text-white transition-colors"
        aria-label="Home"
      >
        <Home className="w-4 h-4" />
      </Link>

      {pathnames.length > 0 && (
        <ChevronRight className="w-4 h-4 text-gray-500" aria-hidden="true" />
      )}

      {/* Path segments */}
      {pathnames.map((pathname, index) => {
        const routeTo = `/${pathnames.slice(0, index + 1).join('/')}`;
        const isLast = index === pathnames.length - 1;
        const displayName = pathNameMap[pathname] || pathname.charAt(0).toUpperCase() + pathname.slice(1);

        return (
          <React.Fragment key={pathname}>
            {isLast ? (
              <span className="text-purple-400 font-medium" aria-current="page">
                {displayName}
              </span>
            ) : (
              <>
                <Link
                  to={routeTo}
                  className="text-gray-400 hover:text-white transition-colors"
                >
                  {displayName}
                </Link>
                <ChevronRight className="w-4 h-4 text-gray-500" aria-hidden="true" />
              </>
            )}
          </React.Fragment>
        );
      })}
    </nav>
  );
};

export default Breadcrumbs;