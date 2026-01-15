import { Bot, User, AlertCircle, Database, GitBranch } from 'lucide-react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';

/**
 * Message Bubble Component
 * 
 * Displays a single chat message with appropriate styling for:
 * - User messages (right-aligned, teal)
 * - Assistant messages (left-aligned, dark)
 * - Error messages (red accent)
 * 
 * Supports markdown rendering for assistant messages including:
 * - Tables, lists, code blocks
 * - Links, bold, italic
 * - GitHub Flavored Markdown
 * 
 * Also shows metadata like sources consulted and mode used.
 */

// Custom components for styling markdown elements
const markdownComponents = {
  // Style tables
  table: ({ children }) => (
    <div className="overflow-x-auto my-2">
      <table className="min-w-full border-collapse text-sm">{children}</table>
    </div>
  ),
  thead: ({ children }) => (
    <thead className="bg-surface-700">{children}</thead>
  ),
  th: ({ children }) => (
    <th className="border border-surface-600 px-3 py-2 text-left font-semibold text-gray-200">{children}</th>
  ),
  td: ({ children }) => (
    <td className="border border-surface-600 px-3 py-2 text-gray-300">{children}</td>
  ),
  // Style code blocks
  code: ({ inline, className, children }) => {
    if (inline) {
      return (
        <code className="bg-surface-700 px-1.5 py-0.5 rounded text-primary-400 text-sm">
          {children}
        </code>
      );
    }
    return (
      <pre className="bg-surface-900 p-3 rounded-lg overflow-x-auto my-2">
        <code className={`text-sm text-gray-300 ${className || ''}`}>{children}</code>
      </pre>
    );
  },
  // Style links
  a: ({ href, children }) => (
    <a 
      href={href} 
      target="_blank" 
      rel="noopener noreferrer"
      className="text-primary-400 hover:text-primary-300 underline"
    >
      {children}
    </a>
  ),
  // Style lists
  ul: ({ children }) => (
    <ul className="list-disc list-inside my-2 space-y-1">{children}</ul>
  ),
  ol: ({ children }) => (
    <ol className="list-decimal list-inside my-2 space-y-1">{children}</ol>
  ),
  li: ({ children }) => (
    <li className="text-gray-300">{children}</li>
  ),
  // Style headings
  h1: ({ children }) => (
    <h1 className="text-xl font-bold text-gray-100 mt-3 mb-2">{children}</h1>
  ),
  h2: ({ children }) => (
    <h2 className="text-lg font-bold text-gray-100 mt-3 mb-2">{children}</h2>
  ),
  h3: ({ children }) => (
    <h3 className="text-base font-bold text-gray-200 mt-2 mb-1">{children}</h3>
  ),
  // Style blockquotes
  blockquote: ({ children }) => (
    <blockquote className="border-l-4 border-primary-500 pl-4 my-2 text-gray-400 italic">
      {children}
    </blockquote>
  ),
  // Style paragraphs
  p: ({ children }) => (
    <p className="my-1">{children}</p>
  ),
  // Style strong/bold
  strong: ({ children }) => (
    <strong className="font-semibold text-gray-100">{children}</strong>
  ),
  // Style emphasis/italic
  em: ({ children }) => (
    <em className="italic text-gray-300">{children}</em>
  ),
};

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
          {isUser ? (
            // User messages: plain text
            <div className="whitespace-pre-wrap">{message.content}</div>
          ) : (
            // Assistant messages: render markdown
            <div className="prose prose-invert prose-sm max-w-none">
              <ReactMarkdown 
                remarkPlugins={[remarkGfm]}
                components={markdownComponents}
              >
                {message.content}
              </ReactMarkdown>
            </div>
          )}
        </div>

        {/* Metadata for assistant messages */}
        {!isUser && message.metadata && (
          <div className="flex flex-wrap gap-2 mt-2 text-xs text-gray-500">
            {/* Intent badge */}
            {message.metadata.intent && (
              <span className="inline-flex items-center gap-1 bg-surface-800 px-2 py-1 rounded-full">
                {message.metadata.intent === 'greeting' && '👋 Greeting'}
                {message.metadata.intent === 'jira_only' && '📋 JIRA Query'}
                {message.metadata.intent === 'github_only' && '💻 GitHub Query'}
                {message.metadata.intent === 'both' && '🔄 Full Activity'}
                {message.metadata.intent === 'unknown' && '❓ Unknown'}
              </span>
            )}
            
            {/* AI Provider badge */}
            <span className="inline-flex items-center gap-1 bg-surface-800 px-2 py-1 rounded-full">
              ✨ {message.metadata.aiProvider}
            </span>
            
            {/* Sources badges */}
            {message.metadata.sources?.map((source, index) => (
              <span
                key={index}
                className="inline-flex items-center gap-1 bg-surface-800 px-2 py-1 rounded-full"
              >
                {source.includes('jira') ? (
                  <>
                    <Database className="w-3 h-3" />
                    {source.includes('mock') ? 'JIRA (demo)' : 'JIRA'}
                  </>
                ) : (
                  <>
                    <GitBranch className="w-3 h-3" />
                    {source.includes('mock') ? 'GitHub (demo)' : 'GitHub'}
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
