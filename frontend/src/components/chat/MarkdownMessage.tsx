import React, { useState } from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import rehypeSanitize from 'rehype-sanitize';
import rehypeHighlight from 'rehype-highlight';
import { Check, Copy } from 'lucide-react';
import 'highlight.js/styles/github-dark.css';

interface MarkdownMessageProps {
  content: string;
}

/**
 * Reusable Code Block with Copy Button and horizontal scroll wrapper.
 */
const CodeBlock: React.FC<{ language?: string; value: string }> = ({ language, value }) => {
  const [copied, setCopied] = useState(false);

  const handleCopy = () => {
    navigator.clipboard.writeText(value);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="my-2 rounded-lg overflow-hidden bg-slate-900 border border-slate-800 text-slate-100 text-xs">
      <div className="flex items-center justify-between px-3 py-1.5 bg-slate-800/80 border-b border-slate-700/60 text-slate-400 font-mono text-[11px]">
        <span>{language || 'code'}</span>
        <button
          onClick={handleCopy}
          className="flex items-center gap-1 hover:text-white transition-colors py-0.5 px-1.5 rounded bg-slate-700/50 hover:bg-slate-700"
          title="Copy code"
        >
          {copied ? (
            <>
              <Check className="w-3 h-3 text-emerald-400" />
              <span className="text-emerald-400">Copied!</span>
            </>
          ) : (
            <>
              <Copy className="w-3 h-3" />
              <span>Copy</span>
            </>
          )}
        </button>
      </div>
      <div className="p-3 overflow-x-auto font-mono text-xs leading-relaxed">
        <pre className="m-0 p-0 bg-transparent border-0">
          <code>{value}</code>
        </pre>
      </div>
    </div>
  );
};

/**
 * Reusable MarkdownMessage component rendering rich Markdown securely for assistant replies.
 */
export const MarkdownMessage: React.FC<MarkdownMessageProps> = ({ content }) => {
  return (
    <div className="markdown-body max-w-full text-xs leading-relaxed overflow-hidden">
      <ReactMarkdown
        remarkPlugins={[remarkGfm]}
        rehypePlugins={[rehypeSanitize, rehypeHighlight]}
        components={{
          // External links open safely in a new tab
          a: ({ node, href, children, ...props }) => (
            <a
              href={href}
              target="_blank"
              rel="noopener noreferrer"
              className="text-blue-600 hover:text-blue-800 underline font-medium"
              {...props}
            >
              {children}
            </a>
          ),
          // Heading sizes
          h1: ({ children }) => <h1 className="text-sm font-bold my-1 text-slate-900">{children}</h1>,
          h2: ({ children }) => <h2 className="text-xs font-bold my-1 text-slate-900">{children}</h2>,
          h3: ({ children }) => <h3 className="text-xs font-semibold my-1 text-slate-800">{children}</h3>,
          // Tight lists
          ul: ({ children }) => <ul className="list-disc list-inside my-1 space-y-0.5">{children}</ul>,
          ol: ({ children }) => <ol className="list-decimal list-inside my-1 space-y-0.5">{children}</ol>,
          li: ({ children }) => <li className="text-xs leading-snug">{children}</li>,
          // Paragraphs
          p: ({ children }) => <p className="my-1 text-xs leading-snug">{children}</p>,
          // Tables with horizontal scrolling container
          table: ({ children }) => (
            <div className="my-2 overflow-x-auto max-w-full rounded border border-slate-200">
              <table className="w-full text-left border-collapse text-xs">
                {children}
              </table>
            </div>
          ),
          thead: ({ children }) => <thead className="bg-slate-100 border-b border-slate-200 font-semibold">{children}</thead>,
          th: ({ children }) => <th className="p-1.5 border-r border-slate-200 last:border-r-0">{children}</th>,
          td: ({ children }) => <td className="p-1.5 border-t border-r border-slate-200 last:border-r-0 text-slate-700">{children}</td>,
          // Code elements (inline vs fenced code block)
          code: ({ node, inline, className, children, ...props }: any) => {
            const match = /language-(\w+)/.exec(className || '');

            // Helper to recursively extract plain text from React nodes
            const extractText = (childrenNode: any): string => {
              if (typeof childrenNode === 'string') return childrenNode;
              if (typeof childrenNode === 'number') return String(childrenNode);
              if (Array.isArray(childrenNode)) return childrenNode.map(extractText).join('');
              if (childrenNode?.props?.children) return extractText(childrenNode.props.children);
              return '';
            };

            const rawText = extractText(children).replace(/\n$/, '');

            if (!inline && (match || rawText.includes('\n') || className)) {
              return <CodeBlock language={match ? match[1] : ''} value={rawText} />;
            }

            return (
              <code
                className="bg-slate-100 border border-slate-200 text-slate-800 px-1 py-0.5 rounded font-mono text-[11px]"
                {...props}
              >
                {children}
              </code>
            );
          }
        }}
      >
        {content}
      </ReactMarkdown>
    </div>
  );
};
