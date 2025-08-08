import React from 'react';
import { Link, useLocation } from 'react-router-dom';
import { Sun, Moon, Command } from 'lucide-react';
import { useUIStore } from '../../stores/uiStore';

const Header: React.FC = () => {
  const { toggleTheme, theme, toggleCommandPalette } = useUIStore();
  const location = useLocation();

  const navigation = [
    { name: 'Cockpit', href: '/', icon: Command },
  ];

  return (
    <header className="bg-white dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700">
      {/* Top bar */}
      <div className="px-4 py-3 border-b border-gray-200 dark:border-gray-700">
        <div className="flex items-center justify-between">
          {/* Left side - Logo */}
          <div className="flex items-center space-x-3">
            <div className="w-8 h-8 bg-primary-600 rounded-lg flex items-center justify-center">
              <span className="text-white font-bold text-sm">CM</span>
            </div>
            <h1 className="text-xl font-semibold text-gray-900 dark:text-white">
              ChatMind
            </h1>
          </div>

          {/* Center - Command palette hint */}
          <div className="flex-1 max-w-lg mx-8">
            <div className="text-xs text-gray-500 dark:text-gray-400">Use ⌘K for command palette</div>
          </div>

          {/* Right side - Actions */}
          <div className="flex items-center space-x-2">
            {/* Command palette */}
            <button
              onClick={toggleCommandPalette}
              className="p-2 rounded-md hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors"
              title="Command palette (⌘K)"
            >
              <Command className="h-5 w-5" />
            </button>

            {/* Theme toggle */}
            <button
              onClick={toggleTheme}
              className="p-2 rounded-md hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors"
              title="Toggle theme"
            >
              {theme.mode === 'light' ? (
                <Moon className="h-5 w-5" />
              ) : (
                <Sun className="h-5 w-5" />
              )}
            </button>
          </div>
        </div>
      </div>

      {/* Navigation bar */}
      <nav className="px-4 py-2">
        <div className="flex items-center space-x-1">
          {navigation.map((item) => {
            const isActive = location.pathname === item.href;
            return (
              <Link
                key={item.name}
                to={item.href}
                className={`flex items-center space-x-2 px-3 py-2 rounded-md text-sm font-medium transition-colors ${
                  isActive
                    ? 'bg-primary-100 dark:bg-primary-900 text-primary-700 dark:text-primary-300'
                    : 'text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700'
                }`}
              >
                <item.icon className="h-4 w-4" />
                <span>{item.name}</span>
              </Link>
            );
          })}
        </div>
      </nav>
    </header>
  );
};

export default Header; 