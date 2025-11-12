/**
 * Message Bubble Component with Markdown Support
 */

'use client';

import { Message, Source } from '@/types';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { vscDarkPlus } from 'react-syntax-highlighter/dist/esm/styles/prism';
import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import AudioPlayer from './AudioPlayer';

interface MessageBubbleProps {
  message: Message;
  isStreaming?: boolean;
  isGeneratingAudio?: boolean;
}

export default function MessageBubble({ message, isStreaming = false, isGeneratingAudio = false }: MessageBubbleProps) {
  const [showSources, setShowSources] = useState(false);
  const isUser = message.role === 'user';

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3 }}
      className={`flex w-full ${isUser ? 'justify-end' : 'justify-start'} mb-6`}
    >
      <div className={`flex gap-3 max-w-4xl ${isUser ? 'flex-row-reverse' : 'flex-row'}`}>
        {/* Avatar - Green Theme Design */}
        <div className="flex-shrink-0">
          {isUser ? (
            <div className="w-10 h-10 rounded-full bg-user-message flex items-center justify-center border-2 border-white/20">
              <svg className="w-6 h-6 text-white" fill="currentColor" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M10 9a3 3 0 100-6 3 3 0 000 6zm-7 9a7 7 0 1114 0H3z" clipRule="evenodd" />
              </svg>
            </div>
          ) : (
            <div className="w-10 h-10 rounded-full bg-gradient-to-br from-blue-600 to-blue-800 flex items-center justify-center border-2 border-blue-500/30">
              <span className="text-white text-xl">✨</span>
            </div>
          )}
        </div>

        {/* Message Content */}
        <div className="flex flex-col gap-2 flex-1">
            <div
            className={`rounded-3xl px-4 py-3 ${
              isUser
                ? 'bg-user-message text-black rounded-tr-sm shadow-md'
                : 'bg-assistant-message backdrop-blur-sm border border-border/50 text-foreground rounded-tl-sm shadow-lg'
            }`}
          >
            {message.enhanced_query && (
              <div className="text-xs text-foreground-muted mb-2 italic opacity-80">
                🔍 Enhanced: {message.enhanced_query}
              </div>
            )}
            
            <div className={`prose max-w-none ${isUser ? 'prose-invert text-black' : ''}`}>
              {isStreaming ? (
                // Show streaming text with cursor
                <>
                  <ReactMarkdown remarkPlugins={[remarkGfm]}>
                    {message.content}
                  </ReactMarkdown>
                  <span className="animate-pulse ml-1">▌</span>
                </>
              ) : (
                // Show final text with full markdown rendering
                <ReactMarkdown
                  remarkPlugins={[remarkGfm]}
                  components={{
                    code({ node, inline, className, children, ...props }) {
                      const match = /language-(\w+)/.exec(className || '');
                      return !inline && match ? (
                        <SyntaxHighlighter
                          style={vscDarkPlus}
                          language={match[1]}
                          PreTag="div"
                          {...props}
                        >
                          {String(children).replace(/\n$/, '')}
                        </SyntaxHighlighter>
                      ) : (
                        <code className={className} {...props}>
                          {children}
                        </code>
                      );
                    },
                  }}
                >
                  {message.content}
                </ReactMarkdown>
              )}
            </div>
          </div>

          {/* Audio Player for Assistant Messages */}
          {!isUser && (
            <AudioPlayer 
              audioBase64={message.audio} 
              isGenerating={isGeneratingAudio}
            />
          )}

          {/* Sources Section */}
          {message.sources && message.sources.length > 0 && (
            <div className="mt-2">
              <motion.button
                onClick={() => setShowSources(!showSources)}
                whileHover={{ scale: 1.02 }}
                whileTap={{ scale: 0.98 }}
                className="text-xs text-foreground-muted hover:text-primary transition-colors flex items-center gap-1"
              >
                <span>📚</span>
                <span>
                  {showSources ? 'Hide' : 'View'} {message.sources.length} sources
                </span>
                <svg
                  className={`w-3 h-3 transition-transform ${
                    showSources ? 'rotate-180' : ''
                  }`}
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M19 9l-7 7-7-7"
                  />
                </svg>
              </motion.button>

              <AnimatePresence>
                {showSources && (
                  <motion.div
                    initial={{ opacity: 0, height: 0 }}
                    animate={{ opacity: 1, height: 'auto' }}
                    exit={{ opacity: 0, height: 0 }}
                    className="mt-2 space-y-2"
                  >
                    {message.sources.map((source, idx) => (
                      <SourceItem key={idx} source={source} index={idx + 1} />
                    ))}
                  </motion.div>
                )}
              </AnimatePresence>
            </div>
          )}
        </div>
      </div>
    </motion.div>
  );
}

function SourceItem({ source, index }: { source: Source; index: number }) {
  const [expanded, setExpanded] = useState(false);

  // Helper function to safely parse metadata arrays
  const parseMetadataArray = (value: any): string[] => {
    if (!value) return [];
    if (Array.isArray(value)) return value;
    if (typeof value === 'string') {
      try {
        const parsed = JSON.parse(value);
        return Array.isArray(parsed) ? parsed : [];
      } catch {
        return [];
      }
    }
    return [];
  };

  const characters = parseMetadataArray(source.metadata.characters);
  const locations = parseMetadataArray(source.metadata.locations);
  const spells = parseMetadataArray(source.metadata.spells);

  return (
    <div className="bg-secondary/50 backdrop-blur-sm border border-border rounded-lg p-3 text-sm">
      <div className="flex justify-between items-start gap-2 mb-1">
        <div className="font-semibold text-foreground">
          Source {index}: {source.metadata.source_file || 'Unknown'}, Page{' '}
          {source.metadata.page_num || '?'}
        </div>
        <motion.button
          onClick={() => setExpanded(!expanded)}
          whileHover={{ scale: 1.05 }}
          whileTap={{ scale: 0.95 }}
          className="text-foreground-muted hover:text-primary text-xs transition-colors"
        >
          {expanded ? 'Less' : 'More'}
        </motion.button>
      </div>

      <div className="text-xs text-foreground-muted space-y-1">
        {source.similarity !== undefined && (
          <div>Similarity: {source.similarity.toFixed(3)}</div>
        )}
        {source.rerank_score !== undefined && (
          <div>Rerank: {source.rerank_score.toFixed(3)}</div>
        )}
        {source.retrieval_method && (
          <div>Method: {source.retrieval_method}</div>
        )}
        {source.bm25_score !== undefined && (
          <div>BM25: {source.bm25_score.toFixed(3)}</div>
        )}
      </div>

      {expanded && (
        <motion.div 
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          className="mt-2"
        >
          <div className="text-xs bg-background rounded p-2 max-h-32 overflow-y-auto border border-border">
            {source.text}
          </div>

          {(characters.length > 0 || locations.length > 0 || spells.length > 0) && (
            <div className="mt-2 text-xs text-foreground-muted space-y-1">
              {characters.length > 0 && (
                <div>
                  <span className="font-semibold text-primary">Characters:</span>{' '}
                  {characters.slice(0, 5).join(', ')}
                </div>
              )}
              {locations.length > 0 && (
                <div>
                  <span className="font-semibold text-primary">Locations:</span>{' '}
                  {locations.slice(0, 3).join(', ')}
                </div>
              )}
              {spells.length > 0 && (
                <div>
                  <span className="font-semibold text-primary">Spells:</span>{' '}
                  {spells.slice(0, 3).join(', ')}
                </div>
              )}
            </div>
          )}
        </motion.div>
      )}
    </div>
  );
}

