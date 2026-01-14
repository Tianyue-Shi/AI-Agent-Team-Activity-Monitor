import { useState, useRef, useEffect } from 'react';
import { Send, Bot, User, Loader2, Zap, Shield, Sparkles, Users, ChevronDown } from 'lucide-react';
import { sendChatMessage, getChatModes, getChatProviders, getTeamMembers } from '../api/client';
import MessageBubble from './MessageBubble';

/**
 * Main Chat Interface Component
 * 
 * Features:
 * - Mode toggle (Procedural vs Agent)
 * - AI Provider toggle (OpenAI vs Claude)
 * - Message history
 * - Team member suggestions
 * - User dropdown for selecting team members (real + mock)
 */
export default function ChatInterface() {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [mode, setMode] = useState('procedural');
  const [aiProvider, setAiProvider] = useState('openai');
  const [modes, setModes] = useState([]);
  const [providers, setProviders] = useState([]);
  const [teamMembers, setTeamMembers] = useState([]);
  const [selectedUser, setSelectedUser] = useState(null); // Selected user from dropdown
  const [isUserDropdownOpen, setIsUserDropdownOpen] = useState(false);
  const messagesEndRef = useRef(null);
  const dropdownRef = useRef(null);

  // Load initial data
  useEffect(() => {
    async function loadData() {
      try {
        const [modesData, providersData, teamData] = await Promise.all([
          getChatModes(),
          getChatProviders(),
          getTeamMembers(),
        ]);
        setModes(modesData.modes);
        setProviders(providersData.providers);
        setTeamMembers(teamData.members);
      } catch (error) {
        console.error('Failed to load initial data:', error);
      }
    }
    loadData();
  }, []);

  // Scroll to bottom when messages change
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  // Close dropdown when clicking outside
  useEffect(() => {
    const handleClickOutside = (event) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target)) {
        setIsUserDropdownOpen(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!input.trim() || isLoading) return;

    const userMessage = input.trim();
    setInput('');
    
    // Add user message with selected user context
    setMessages(prev => [...prev, { 
      role: 'user', 
      content: userMessage,
      selectedUser: selectedUser ? selectedUser.display_name : null,
    }]);
    setIsLoading(true);

    try {
      // Pass selected user to API if one is selected
      const response = await sendChatMessage(userMessage, mode, aiProvider, selectedUser);
      
      // Add assistant message
      setMessages(prev => [...prev, {
        role: 'assistant',
        content: response.response,
        metadata: {
          mode: response.mode,
          aiProvider: response.ai_provider,
          sources: response.sources_consulted,
          selectedUser: selectedUser ? selectedUser.display_name : null,
        },
      }]);
    } catch (error) {
      setMessages(prev => [...prev, {
        role: 'assistant',
        content: `Error: ${error.message}`,
        isError: true,
      }]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleQuickQuery = (member) => {
    setInput(`What is ${member.display_name} working on?`);
  };

  return (
    <div className="flex flex-col h-full">
      {/* Header with controls */}
      <div className="glass rounded-xl p-4 mb-4">
        <div className="flex flex-wrap items-center justify-between gap-4">
          {/* Mode Selection */}
          <div className="flex items-center gap-3">
            <span className="text-sm text-gray-400 font-medium">Mode:</span>
            <div className="flex bg-surface-800 rounded-lg p-1">
              {modes.map((m) => (
                <button
                  key={m.id}
                  onClick={() => setMode(m.id)}
                  className={`flex items-center gap-2 px-3 py-1.5 rounded-md text-sm font-medium transition-all ${
                    mode === m.id
                      ? 'bg-primary-600 text-white'
                      : 'text-gray-400 hover:text-white'
                  }`}
                  title={m.description}
                >
                  {m.id === 'procedural' ? (
                    <Shield className="w-4 h-4" />
                  ) : (
                    <Zap className="w-4 h-4" />
                  )}
                  {m.name}
                </button>
              ))}
            </div>
          </div>

          {/* Provider Selection */}
          <div className="flex items-center gap-3">
            <span className="text-sm text-gray-400 font-medium">AI:</span>
            <div className="flex bg-surface-800 rounded-lg p-1">
              {providers.map((p) => (
                <button
                  key={p.id}
                  onClick={() => setAiProvider(p.id)}
                  className={`flex items-center gap-2 px-3 py-1.5 rounded-md text-sm font-medium transition-all ${
                    aiProvider === p.id
                      ? 'bg-primary-600 text-white'
                      : 'text-gray-400 hover:text-white'
                  } ${!p.configured ? 'opacity-50' : ''}`}
                  title={p.configured ? p.name : `${p.name} (not configured)`}
                >
                  <Sparkles className="w-4 h-4" />
                  {p.name}
                  {!p.configured && <span className="text-xs">(⚠)</span>}
                </button>
              ))}
            </div>
          </div>
        </div>

        {/* Mode explanation */}
        <div className="mt-3 text-xs text-gray-500">
          {mode === 'procedural' ? (
            <span>📊 <strong>Standard Mode:</strong> Always fetches JIRA & GitHub data. Reliable but uses more resources.</span>
          ) : (
            <span>🤖 <strong>Agent Mode:</strong> AI decides when to fetch data. Efficient but less predictable.</span>
          )}
        </div>
      </div>

      {/* Messages area */}
      <div className="flex-1 overflow-y-auto space-y-4 pr-2">
        {messages.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-full text-center">
            <Bot className="w-16 h-16 text-primary-500 mb-4" />
            <h2 className="text-xl font-semibold text-gray-200 mb-2">
              Team Activity Monitor
            </h2>
            <p className="text-gray-400 mb-6 max-w-md">
              Ask me about what your team members are working on. I'll check JIRA tickets and GitHub activity.
            </p>
            
            {/* Quick query buttons */}
            <div className="flex flex-wrap justify-center gap-2">
              {teamMembers.map((member) => (
                <button
                  key={member.username}
                  onClick={() => handleQuickQuery(member)}
                  className="btn-secondary text-sm flex items-center gap-2"
                >
                  <User className="w-4 h-4" />
                  {member.display_name}
                  <span className="text-gray-500">({member.role})</span>
                </button>
              ))}
            </div>
          </div>
        ) : (
          messages.map((message, index) => (
            <MessageBubble key={index} message={message} />
          ))
        )}
        
        {isLoading && (
          <div className="flex items-center gap-3 p-4 rounded-lg bg-surface-900">
            <Loader2 className="w-5 h-5 text-primary-500 animate-spin" />
            <span className="text-gray-400">Thinking...</span>
          </div>
        )}
        
        <div ref={messagesEndRef} />
      </div>

      {/* Input area with user dropdown */}
      <form onSubmit={handleSubmit} className="mt-4">
        <div className="flex gap-3 items-stretch">
          {/* User Selection Dropdown */}
          <div className="relative" ref={dropdownRef}>
            <button
              type="button"
              onClick={() => setIsUserDropdownOpen(!isUserDropdownOpen)}
              className={`h-full px-4 rounded-lg flex items-center gap-2 transition-all ${
                selectedUser 
                  ? 'bg-primary-600/20 border border-primary-500 text-primary-400' 
                  : 'bg-surface-800 border border-surface-700 text-gray-400 hover:border-primary-500'
              }`}
              title={selectedUser ? `Selected: ${selectedUser.display_name}` : 'Select a team member'}
            >
              <Users className="w-4 h-4" />
              <span className="max-w-24 truncate text-sm">
                {selectedUser ? selectedUser.display_name : 'All Users'}
              </span>
              <ChevronDown className={`w-4 h-4 transition-transform ${isUserDropdownOpen ? 'rotate-180' : ''}`} />
            </button>

            {/* Dropdown Menu */}
            {isUserDropdownOpen && (
              <div className="absolute bottom-full mb-2 left-0 w-64 bg-surface-800 border border-surface-700 rounded-lg shadow-xl z-50 max-h-64 overflow-y-auto">
                {/* Clear selection option */}
                <button
                  type="button"
                  onClick={() => {
                    setSelectedUser(null);
                    setIsUserDropdownOpen(false);
                  }}
                  className={`w-full px-4 py-2 text-left text-sm hover:bg-surface-700 transition-colors flex items-center gap-2 ${
                    !selectedUser ? 'text-primary-400 bg-surface-700' : 'text-gray-400'
                  }`}
                >
                  <Users className="w-4 h-4" />
                  <span>All Users (type name in query)</span>
                </button>
                
                {/* Real users section */}
                {teamMembers.filter(m => m.is_real).length > 0 && (
                  <>
                    <div className="px-4 py-1 text-xs text-gray-500 bg-surface-900 font-medium">
                      🔗 Connected Accounts
                    </div>
                    {teamMembers.filter(m => m.is_real).map((member) => (
                      <button
                        key={member.id}
                        type="button"
                        onClick={() => {
                          setSelectedUser(member);
                          setIsUserDropdownOpen(false);
                        }}
                        className={`w-full px-4 py-2 text-left text-sm hover:bg-surface-700 transition-colors flex items-center justify-between ${
                          selectedUser?.id === member.id ? 'text-primary-400 bg-surface-700' : 'text-gray-300'
                        }`}
                      >
                        <div className="flex items-center gap-2">
                          <User className="w-4 h-4" />
                          <span>{member.display_name}</span>
                        </div>
                        <span className="text-xs text-gray-500">
                          {member.source === 'jira' ? 'JIRA' : member.source === 'github' ? 'GitHub' : ''}
                        </span>
                      </button>
                    ))}
                  </>
                )}

                {/* Mock users section */}
                {teamMembers.filter(m => !m.is_real).length > 0 && (
                  <>
                    <div className="px-4 py-1 text-xs text-gray-500 bg-surface-900 font-medium">
                      🧪 Demo Users
                    </div>
                    {teamMembers.filter(m => !m.is_real).map((member) => (
                      <button
                        key={member.id}
                        type="button"
                        onClick={() => {
                          setSelectedUser(member);
                          setIsUserDropdownOpen(false);
                        }}
                        className={`w-full px-4 py-2 text-left text-sm hover:bg-surface-700 transition-colors flex items-center justify-between ${
                          selectedUser?.id === member.id ? 'text-primary-400 bg-surface-700' : 'text-gray-300'
                        }`}
                      >
                        <div className="flex items-center gap-2">
                          <User className="w-4 h-4" />
                          <span>{member.display_name}</span>
                        </div>
                        <span className="text-xs text-gray-500">{member.role}</span>
                      </button>
                    ))}
                  </>
                )}
              </div>
            )}
          </div>

          {/* Text Input */}
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder={selectedUser 
              ? `Ask about ${selectedUser.display_name}... (e.g., 'What are they working on?')`
              : "Ask about team activity... (e.g., 'What is John working on?')"
            }
            className="input-field flex-1"
            disabled={isLoading}
          />
          
          {/* Send Button */}
          <button
            type="submit"
            disabled={isLoading || !input.trim()}
            className="btn-primary flex items-center gap-2"
          >
            <Send className="w-4 h-4" />
            Send
          </button>
        </div>

        {/* Selected user indicator */}
        {selectedUser && (
          <div className="mt-2 text-xs text-gray-500 flex items-center gap-2">
            <span>Querying:</span>
            {selectedUser.jira_display_name && (
              <span className="bg-blue-500/20 text-blue-400 px-2 py-0.5 rounded">
                JIRA: {selectedUser.jira_display_name}
              </span>
            )}
            {selectedUser.github_username && (
              <span className="bg-purple-500/20 text-purple-400 px-2 py-0.5 rounded">
                GitHub: {selectedUser.github_username}
              </span>
            )}
          </div>
        )}
      </form>
    </div>
  );
}
