import { BrowserRouter, Routes, Route, NavLink } from 'react-router-dom';
import { MessageSquare, Settings, Activity } from 'lucide-react';
import ChatInterface from './components/ChatInterface';
import AdminPanel from './components/AdminPanel';

/**
 * Main Application Component
 * 
 * Features:
 * - Two main routes: Chat and Admin
 * - Responsive sidebar navigation
 * - Clean dark theme
 */
function App() {
  return (
    <BrowserRouter>
      <div className="flex h-screen bg-surface-950">
        {/* Sidebar Navigation */}
        <nav className="w-64 bg-surface-900 border-r border-surface-800 flex flex-col">
          {/* Logo */}
          <div className="p-6 border-b border-surface-800">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-primary-500 to-primary-700 flex items-center justify-center">
                <Activity className="w-6 h-6 text-white" />
              </div>
              <div>
                <h1 className="font-semibold text-gray-100">Team Monitor</h1>
                <p className="text-xs text-gray-500">Activity Tracker</p>
              </div>
            </div>
          </div>

          {/* Navigation Links */}
          <div className="flex-1 p-4 space-y-2">
            <NavLink
              to="/"
              className={({ isActive }) =>
                `flex items-center gap-3 px-4 py-3 rounded-lg transition-all ${
                  isActive
                    ? 'bg-primary-600 text-white'
                    : 'text-gray-400 hover:bg-surface-800 hover:text-gray-200'
                }`
              }
            >
              <MessageSquare className="w-5 h-5" />
              Chat
            </NavLink>

            <NavLink
              to="/admin"
              className={({ isActive }) =>
                `flex items-center gap-3 px-4 py-3 rounded-lg transition-all ${
                  isActive
                    ? 'bg-primary-600 text-white'
                    : 'text-gray-400 hover:bg-surface-800 hover:text-gray-200'
                }`
              }
            >
              <Settings className="w-5 h-5" />
              Admin Panel
            </NavLink>
          </div>

          {/* Footer */}
          <div className="p-4 border-t border-surface-800">
            <div className="text-xs text-gray-500 space-y-1">
              <p>Dual-Mode AI Engine</p>
              <div className="flex gap-2">
                <span className="px-2 py-0.5 bg-surface-800 rounded text-gray-400">
                  📊 Standard
                </span>
                <span className="px-2 py-0.5 bg-surface-800 rounded text-gray-400">
                  🤖 Agent
                </span>
              </div>
            </div>
          </div>
        </nav>

        {/* Main Content */}
        <main className="flex-1 overflow-hidden">
          <div className="h-full p-6">
            <Routes>
              <Route path="/" element={<ChatInterface />} />
              <Route path="/admin" element={<AdminPanel />} />
            </Routes>
          </div>
        </main>
      </div>
    </BrowserRouter>
  );
}

export default App;
