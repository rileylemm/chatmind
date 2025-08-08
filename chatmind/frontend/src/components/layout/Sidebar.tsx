import React from 'react';
import { Link, useLocation } from 'react-router-dom';
import { 
  Tag,
  Search,
  Network,
  Layers,
  Clock
} from 'lucide-react';
import { useUIStore } from '../../stores/uiStore';

const Sidebar: React.FC = () => {
  const { sidebarOpen } = useUIStore();
  const location = useLocation();

  const navigation = [
    { name: 'Semantic Search', href: '/search', icon: Search },
    { name: 'Tag Discovery', href: '/discovery', icon: Tag },
    { name: 'Connection Discovery', href: '/connections', icon: Network },
    { name: 'Cluster Discovery', href: '/clusters', icon: Layers },
    { name: 'Timeline Discovery', href: '/timeline', icon: Clock },
  ];

  if (!sidebarOpen) {
    return null;
  }

  return (
    <aside className="w-64 bg-white dark:bg-gray-800 border-r border-gray-200 dark:border-gray-700 flex flex-col">
      {/* Sidebar header */}
      <div className="p-6 border-b border-gray-200 dark:border-gray-700">
        <h2 className="text-lg font-semibold text-gray-900 dark:text-white">
          CM ChatMind
        </h2>
        <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">
          Knowledge Graph Explorer
        </p>
      </div>

      {/* Navigation menu */}
      <nav className="flex-1 p-4">
        <ul className="space-y-2">
          {navigation.map((item) => {
            const isActive = location.pathname === item.href;
            return (
              <li key={item.name}>
                <Link
                  to={item.href}
                  className={`flex items-center space-x-3 px-3 py-2 rounded-md text-sm font-medium transition-colors ${
                    isActive
                      ? 'bg-primary-100 dark:bg-primary-900 text-primary-700 dark:text-primary-300'
                      : 'text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700'
                  }`}
                >
                  <item.icon className="h-5 w-5" />
                  <span>{item.name}</span>
                </Link>
              </li>
            );
          })}
        </ul>
      </nav>

      {/* Sidebar footer */}
      <div className="p-4 border-t border-gray-200 dark:border-gray-700">
        <div className="text-xs text-gray-500 dark:text-gray-400">
          ChatMind v1.0.0
        </div>
      </div>
    </aside>
  );
};

export default Sidebar; 