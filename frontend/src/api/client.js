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
 * @param {string} aiProvider - "openai" or "claude"
 * @param {object|null} selectedUser - User selected from dropdown (optional)
 * @param {string|null} conversationId - Conversation ID for follow-ups (optional)
 */
export async function sendChatMessage(query, aiProvider = 'openai', selectedUser = null, conversationId = null) {
  const payload = { 
    query, 
    ai_provider: aiProvider,
  };
  
  // Add conversation ID if provided
  if (conversationId) {
    payload.conversation_id = conversationId;
  }
  
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
// Conversation API
// =============================================================================

/**
 * List all conversations
 * @param {number} limit - Maximum number of conversations to return
 */
export async function listConversations(limit = 20) {
  return fetchAPI(`/chat/conversations?limit=${limit}`);
}

/**
 * Get a specific conversation with messages
 * @param {string} conversationId - Conversation ID
 */
export async function getConversation(conversationId) {
  return fetchAPI(`/chat/conversations/${conversationId}`);
}

/**
 * Delete a conversation
 * @param {string} conversationId - Conversation ID
 */
export async function deleteConversation(conversationId) {
  return fetchAPI(`/chat/conversations/${conversationId}`, {
    method: 'DELETE',
  });
}

/**
 * Create a new conversation
 */
export async function createNewConversation() {
  return fetchAPI('/chat/conversations/new', {
    method: 'POST',
  });
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
