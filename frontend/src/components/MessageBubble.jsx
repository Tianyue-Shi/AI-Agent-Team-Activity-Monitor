import { Bot, User, AlertCircle, Database, GitBranch } from 'lucide-react';

/**
 * Message Bubble Component
 * 
 * Displays a single chat message with appropriate styling for:
 * - User messages (right-aligned, teal)
 * - Assistant messages (left-aligned, dark)
 * - Error messages (red accent)
 * 
 * Also shows metadata like sources consulted and mode used.
 */
export default function MessageBubble({ message }) {
  const isUser = message.role === 'user';
  const isError = message.isError;

  return (
    <div
      className={`flex gap-3 message-enter ${isUser ? 'flex-row-reverse' : ''}`}
    >
      {/* Avatar */}
      <div
        className={`flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center ${
          isUser
            ? 'bg-primary-600'
            : isError
            ? 'bg-red-600'
            : 'bg-surface-700'
        }`}
      >
        {isUser ? (
          <User className="w-4 h-4 text-white" />
        ) : isError ? (
          <AlertCircle className="w-4 h-4 text-white" />
        ) : (
          <Bot className="w-4 h-4 text-primary-400" />
        )}
      </div>

      {/* Message content */}
      <div
        className={`max-w-[80%] ${isUser ? 'text-right' : ''}`}
      >
        <div
          className={`rounded-2xl px-4 py-3 ${
            isUser
              ? 'bg-primary-600 text-white rounded-tr-sm'
              : isError
              ? 'bg-red-900/30 border border-red-800 text-red-200 rounded-tl-sm'
              : 'bg-surface-800 text-gray-200 rounded-tl-sm'
          }`}
        >
          {/* Message text with proper formatting */}
          <div className="whitespace-pre-wrap">{message.content}</div>
        </div>

        {/* Metadata for assistant messages */}
        {!isUser && message.metadata && (
          <div className="flex flex-wrap gap-2 mt-2 text-xs text-gray-500">
            {/* Mode badge */}
            <span className="inline-flex items-center gap-1 bg-surface-800 px-2 py-1 rounded-full">
              {message.metadata.mode === 'agent' ? '🤖 Agent' : '📊 Standard'}
            </span>
            
            {/* AI Provider badge */}
            <span className="inline-flex items-center gap-1 bg-surface-800 px-2 py-1 rounded-full">
              ✨ {message.metadata.aiProvider}
            </span>
            
            {/* Sources badges */}
            {message.metadata.sources?.map((source) => (
              <span
                key={source}
                className="inline-flex items-center gap-1 bg-surface-800 px-2 py-1 rounded-full"
              >
                {source === 'jira' ? (
                  <>
                    <Database className="w-3 h-3" />
                    JIRA
                  </>
                ) : (
                  <>
                    <GitBranch className="w-3 h-3" />
                    GitHub
                  </>
                )}
              </span>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
