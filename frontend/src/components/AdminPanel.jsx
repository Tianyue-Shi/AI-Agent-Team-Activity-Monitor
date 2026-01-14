import { useState, useEffect } from 'react';
import { Save, RotateCcw, History, Check, AlertCircle, Loader2 } from 'lucide-react';
import {
  getCurrentPrompt,
  updatePrompt,
  getPromptHistory,
  rollbackPrompt,
} from '../api/client';

/**
 * Admin Panel Component
 * 
 * Features:
 * - View and edit current system prompt
 * - Version history with timestamps
 * - Rollback to previous versions
 * - Visual indicators for active version
 */
export default function AdminPanel() {
  const [currentPrompt, setCurrentPrompt] = useState(null);
  const [editedPrompt, setEditedPrompt] = useState('');
  const [history, setHistory] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isSaving, setIsSaving] = useState(false);
  const [message, setMessage] = useState(null);

  // Load data on mount
  useEffect(() => {
    loadData();
  }, []);

  async function loadData() {
    setIsLoading(true);
    try {
      const [promptData, historyData] = await Promise.all([
        getCurrentPrompt(),
        getPromptHistory(),
      ]);
      setCurrentPrompt(promptData);
      setEditedPrompt(promptData.prompt_text);
      setHistory(historyData.prompts);
    } catch (error) {
      showMessage(`Failed to load data: ${error.message}`, 'error');
    } finally {
      setIsLoading(false);
    }
  }

  function showMessage(text, type = 'success') {
    setMessage({ text, type });
    setTimeout(() => setMessage(null), 5000);
  }

  async function handleSave() {
    if (!editedPrompt.trim() || editedPrompt === currentPrompt?.prompt_text) {
      return;
    }

    setIsSaving(true);
    try {
      const newPrompt = await updatePrompt(editedPrompt);
      setCurrentPrompt(newPrompt);
      showMessage(`Saved as version ${newPrompt.version}!`, 'success');
      await loadData(); // Refresh history
    } catch (error) {
      showMessage(`Failed to save: ${error.message}`, 'error');
    } finally {
      setIsSaving(false);
    }
  }

  async function handleRollback(version) {
    if (!confirm(`Rollback to version ${version}? This will create a new version.`)) {
      return;
    }

    setIsSaving(true);
    try {
      const newPrompt = await rollbackPrompt(version);
      setCurrentPrompt(newPrompt);
      setEditedPrompt(newPrompt.prompt_text);
      showMessage(`Rolled back to version ${version} (now version ${newPrompt.version})`, 'success');
      await loadData();
    } catch (error) {
      showMessage(`Failed to rollback: ${error.message}`, 'error');
    } finally {
      setIsSaving(false);
    }
  }

  function formatDate(dateString) {
    return new Date(dateString).toLocaleString('en-US', {
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  }

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <Loader2 className="w-8 h-8 text-primary-500 animate-spin" />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Message toast */}
      {message && (
        <div
          className={`fixed top-4 right-4 flex items-center gap-2 px-4 py-3 rounded-lg animate-fade-in ${
            message.type === 'error'
              ? 'bg-red-900/90 text-red-200 border border-red-800'
              : 'bg-green-900/90 text-green-200 border border-green-800'
          }`}
        >
          {message.type === 'error' ? (
            <AlertCircle className="w-5 h-5" />
          ) : (
            <Check className="w-5 h-5" />
          )}
          {message.text}
        </div>
      )}

      {/* Current Prompt Editor */}
      <div className="card">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-lg font-semibold text-gray-200 flex items-center gap-2">
            <span className="w-2 h-2 rounded-full bg-primary-500 animate-pulse-subtle" />
            Active System Prompt
            <span className="text-sm font-normal text-gray-500">
              (v{currentPrompt?.version})
            </span>
          </h2>
          <button
            onClick={handleSave}
            disabled={isSaving || editedPrompt === currentPrompt?.prompt_text}
            className="btn-primary flex items-center gap-2"
          >
            {isSaving ? (
              <Loader2 className="w-4 h-4 animate-spin" />
            ) : (
              <Save className="w-4 h-4" />
            )}
            Save New Version
          </button>
        </div>

        <textarea
          value={editedPrompt}
          onChange={(e) => setEditedPrompt(e.target.value)}
          className="input-field w-full h-48 font-mono text-sm resize-none"
          placeholder="Enter system prompt..."
        />

        <p className="mt-2 text-xs text-gray-500">
          💡 Tip: Changes create a new version. The old version is preserved for rollback.
        </p>
      </div>

      {/* Version History */}
      <div className="card">
        <h2 className="text-lg font-semibold text-gray-200 flex items-center gap-2 mb-4">
          <History className="w-5 h-5 text-gray-400" />
          Version History
          <span className="text-sm font-normal text-gray-500">
            ({history.length} versions)
          </span>
        </h2>

        <div className="space-y-3 max-h-96 overflow-y-auto pr-2">
          {history.map((prompt) => (
            <div
              key={prompt.id}
              className={`p-4 rounded-lg border transition-all ${
                prompt.is_active
                  ? 'bg-primary-900/20 border-primary-700'
                  : 'bg-surface-800 border-surface-700 hover:border-surface-600'
              }`}
            >
              <div className="flex items-center justify-between mb-2">
                <div className="flex items-center gap-3">
                  <span className="font-mono text-sm text-gray-300">
                    v{prompt.version}
                  </span>
                  {prompt.is_active && (
                    <span className="px-2 py-0.5 bg-primary-600 text-white text-xs rounded-full">
                      Active
                    </span>
                  )}
                  <span className="text-xs text-gray-500">
                    {formatDate(prompt.created_at)}
                  </span>
                </div>

                {!prompt.is_active && (
                  <button
                    onClick={() => handleRollback(prompt.version)}
                    disabled={isSaving}
                    className="btn-secondary text-xs flex items-center gap-1 py-1 px-2"
                  >
                    <RotateCcw className="w-3 h-3" />
                    Rollback
                  </button>
                )}
              </div>

              <p className="text-sm text-gray-400 line-clamp-2 font-mono">
                {prompt.prompt_text}
              </p>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
