import React from 'react';
import Navbar from './Navbar';

const Layout = ({ children, showNavbar = true }) => {
  return (
    <div className="min-h-screen bg-gray-900">
      {showNavbar && <Navbar />}
      <div className={showNavbar ? "pt-16" : ""}>
        {children}
      </div>
    </div>
  );
};

export default Layout;