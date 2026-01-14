/**
 * API Client for Team Activity Monitor Backend
 * 
 * Centralizes all API calls to the FastAPI backend.
 * Base URL is configured via VITE_API_URL environment variable,
 * falling back to localhost for development.
 */

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000';

/**
 * Generic fetch wrapper with error handling
 */
async function fetchAPI(endpoint, options = {}) {
  const url = `${API_BASE}${endpoint}`;
  
  const defaultOptions = {
    headers: {
      'Content-Type': 'application/json',
    },
  };
  
  const response = await fetch(url, { ...defaultOptions, ...options });
  
  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Unknown error' }));
    throw new Error(error.detail || `HTTP ${response.status}`);
  }
  
  return response.json();
}

// =============================================================================
// Chat API
// =============================================================================

/**
 * Send a chat message
 * @param {string} query - User's question
 * @param {string} mode - "procedural" or "agent"
 * @param {string} aiProvider - "openai" or "claude"
 * @param {object|null} selectedUser - User selected from dropdown (optional)
 */
export async function sendChatMessage(query, mode = 'procedural', aiProvider = 'openai', selectedUser = null) {
  const payload = { 
    query, 
    mode, 
    ai_provider: aiProvider,
  };
  
  // Add selected user if provided (with platform-specific identifiers)
  if (selectedUser) {
    payload.selected_user = {
      id: selectedUser.id,
      display_name: selectedUser.display_name,
      source: selectedUser.source,
      jira_display_name: selectedUser.jira_display_name || null,
      github_username: selectedUser.github_username || null,
    };
  }
  
  return fetchAPI('/chat', {
    method: 'POST',
    body: JSON.stringify(payload),
  });
}

/**
 * Get available chat modes
 */
export async function getChatModes() {
  return fetchAPI('/chat/modes');
}

/**
 * Get available AI providers
 */
export async function getChatProviders() {
  return fetchAPI('/chat/providers');
}

/**
 * Get team members list
 */
export async function getTeamMembers() {
  return fetchAPI('/chat/team');
}

// =============================================================================
// Prompts API
// =============================================================================

/**
 * Get the current active prompt
 */
export async function getCurrentPrompt() {
  return fetchAPI('/prompts/current');
}

/**
 * Create a new prompt version
 * @param {string} promptText - New prompt text
 */
export async function updatePrompt(promptText) {
  return fetchAPI('/prompts/update', {
    method: 'POST',
    body: JSON.stringify({ prompt_text: promptText }),
  });
}

/**
 * Get prompt version history
 */
export async function getPromptHistory() {
  return fetchAPI('/prompts/history');
}

/**
 * Rollback to a specific prompt version
 * @param {number} version - Version number to rollback to
 */
export async function rollbackPrompt(version) {
  return fetchAPI(`/prompts/rollback/${version}`, {
    method: 'POST',
  });
}

/**
 * Get a specific prompt version
 * @param {number} version - Version number
 */
export async function getPromptVersion(version) {
  return fetchAPI(`/prompts/${version}`);
}

// =============================================================================
// Health API
// =============================================================================

/**
 * Check API health
 */
export async function checkHealth() {
  return fetchAPI('/health');
}
