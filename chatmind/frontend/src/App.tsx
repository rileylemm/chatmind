import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { Layout } from './components/layout/Layout';
import Dashboard from './pages/Dashboard';

// Create a client
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 5 * 60 * 1000, // 5 minutes
      retry: 1,
    },
  },
});

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <Router>
        <Layout>
          <Routes>
            <Route path="/" element={<Dashboard />} />
            {/* Add more routes as we build them */}
            <Route path="/graph" element={<div>Graph Explorer (Coming Soon)</div>} />
            <Route path="/messages" element={<div>Messages (Coming Soon)</div>} />
            <Route path="/analytics" element={<div>Analytics (Coming Soon)</div>} />
            <Route path="/tags" element={<div>Tags (Coming Soon)</div>} />
            <Route path="/data" element={<div>Data Lake (Coming Soon)</div>} />
            <Route path="/settings" element={<div>Settings (Coming Soon)</div>} />
          </Routes>
        </Layout>
      </Router>
    </QueryClientProvider>
  );
}

export default App;
