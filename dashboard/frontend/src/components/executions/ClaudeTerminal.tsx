import { useState, useEffect, useRef, useMemo } from 'react';
import { motion, AnimatePresence } from 'motion/react';
import { ChevronDown, Loader2, Check } from 'lucide-react';
import { cn } from '@/lib/utils';

// Parsed output line types matching ExecutionMonitor
export interface ParsedLine {
  type: 'text' | 'tool' | 'thinking' | 'error' | 'raw';
  content: string;
  toolName?: string;
}

interface ClaudeTerminalProps {
  lines: ParsedLine[];
  isLive?: boolean;
  title?: string;
  className?: string;
  maxHeight?: string;
}

// Collapsible thinking block component - Claude Code style
const ThinkingBlock = ({ content }: { content: string }) => {
  const [isExpanded, setIsExpanded] = useState(false);
  const previewLength = 120;
  const needsCollapse = content.length > previewLength;
  const preview = needsCollapse ? content.substring(0, previewLength) + '...' : content;

  return (
    <div className="my-2">
      <div
        className={cn(
          'flex items-start gap-2 text-zinc-500',
          needsCollapse && 'cursor-pointer hover:text-zinc-400'
        )}
        onClick={() => needsCollapse && setIsExpanded(!isExpanded)}
      >
        {needsCollapse && (
          <motion.span
            animate={{ rotate: isExpanded ? 0 : -90 }}
            transition={{ duration: 0.15 }}
            className="mt-0.5 flex-shrink-0"
          >
            <ChevronDown className="h-3.5 w-3.5" />
          </motion.span>
        )}
        {!needsCollapse && <span className="w-3.5" />}
        <div className="flex-1 min-w-0">
          <span className="text-zinc-500 italic text-xs">
            {isExpanded ? 'Thinking...' : 'Thinking... '}
          </span>
          <AnimatePresence mode="wait">
            {!isExpanded && (
              <motion.span
                key="preview"
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                exit={{ opacity: 0 }}
                className="text-zinc-600 text-xs"
              >
                {preview}
              </motion.span>
            )}
          </AnimatePresence>
        </div>
      </div>
      <AnimatePresence>
        {isExpanded && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: 'auto', opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.2 }}
            className="overflow-hidden"
          >
            <div className="ml-5.5 pl-2 border-l border-zinc-700 mt-1 text-zinc-500 text-xs whitespace-pre-wrap">
              {content}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
};

// Tool call line component - Claude Code style with completion indicator
const ToolCallLine = ({ toolName, isComplete = true }: { toolName?: string; isComplete?: boolean }) => {
  return (
    <div className="flex items-center gap-2 my-1 py-0.5">
      {isComplete ? (
        <Check className="h-3.5 w-3.5 text-green-500 flex-shrink-0" />
      ) : (
        <Loader2 className="h-3.5 w-3.5 text-blue-400 animate-spin flex-shrink-0" />
      )}
      <span className="text-zinc-400 text-sm font-medium">{toolName || 'Tool'}</span>
    </div>
  );
};

// Typing text component with cursor animation
const TypingText = ({ content, animate = true }: { content: string; animate?: boolean }) => {
  const [displayedText, setDisplayedText] = useState(animate ? '' : content);
  const [isComplete, setIsComplete] = useState(!animate);

  useEffect(() => {
    if (!animate) {
      setDisplayedText(content);
      setIsComplete(true);
      return;
    }

    // Fast typing for streaming effect
    const duration = 8; // ms per character (faster)
    let i = 0;

    const typingEffect = setInterval(() => {
      if (i < content.length) {
        setDisplayedText(content.substring(0, i + 1));
        i++;
      } else {
        clearInterval(typingEffect);
        setIsComplete(true);
      }
    }, duration);

    return () => clearInterval(typingEffect);
  }, [content, animate]);

  return (
    <span className="text-zinc-100">
      {displayedText}
      {!isComplete && (
        <motion.span
          animate={{ opacity: [1, 0] }}
          transition={{ duration: 0.53, repeat: Infinity }}
          className="text-zinc-400 inline-block w-2"
        >
          _
        </motion.span>
      )}
    </span>
  );
};

// Error line component
const ErrorLine = ({ content }: { content: string }) => {
  return (
    <div className="flex items-start gap-2 my-1 py-0.5 text-red-400">
      <span className="font-bold flex-shrink-0">✗</span>
      <span className="text-sm">{content}</span>
    </div>
  );
};

export function ClaudeTerminal({
  lines,
  isLive = false,
  title = 'Claude Code',
  className,
  maxHeight = 'h-96',
}: ClaudeTerminalProps) {
  const outputRef = useRef<HTMLDivElement>(null);
  const [lastLineCount, setLastLineCount] = useState(0);

  // Track which lines should animate (only new ones)
  const animatingLines = useMemo(() => {
    const result = new Set<number>();
    if (isLive && lines.length > lastLineCount) {
      // Only animate the last new line
      result.add(lines.length - 1);
    }
    return result;
  }, [lines.length, lastLineCount, isLive]);

  // Update last line count
  useEffect(() => {
    setLastLineCount(lines.length);
  }, [lines.length]);

  // Auto-scroll to bottom when new output arrives
  useEffect(() => {
    if (outputRef.current) {
      outputRef.current.scrollTop = outputRef.current.scrollHeight;
    }
  }, [lines]);

  return (
    <div
      className={cn(
        'rounded-lg border border-zinc-800 bg-zinc-950 overflow-hidden',
        className
      )}
    >
      {/* Header bar - minimal Claude Code style */}
      <div className="flex items-center justify-between border-b border-zinc-800 bg-zinc-900/50 px-4 py-2">
        <div className="flex items-center gap-2">
          {isLive ? (
            <motion.div
              animate={{ opacity: [1, 0.4] }}
              transition={{ duration: 0.8, repeat: Infinity }}
              className="h-2 w-2 rounded-full bg-green-500"
            />
          ) : (
            <div className="h-2 w-2 rounded-full bg-zinc-600" />
          )}
          <span className="text-xs text-zinc-400 font-medium">{title}</span>
        </div>
        <div className="text-xs text-zinc-600">
          {isLive ? 'streaming...' : 'completed'}
        </div>
      </div>

      {/* Terminal content */}
      <div
        ref={outputRef}
        className={cn(
          'p-4 font-mono text-sm overflow-y-auto overflow-x-auto',
          maxHeight
        )}
      >
        {lines.length === 0 ? (
          <div className="text-zinc-600 flex items-center gap-2">
            {isLive ? (
              <>
                <Loader2 className="h-4 w-4 animate-spin" />
                <span>Waiting for output...</span>
              </>
            ) : (
              <span className="italic">No output captured</span>
            )}
          </div>
        ) : (
          <div className="space-y-1">
            {lines.map((line, index) => {
              const shouldAnimate = animatingLines.has(index) && line.type === 'text';

              switch (line.type) {
                case 'tool':
                  return (
                    <motion.div
                      key={index}
                      initial={{ opacity: 0 }}
                      animate={{ opacity: 1 }}
                      transition={{ duration: 0.15 }}
                    >
                      <ToolCallLine
                        toolName={line.toolName}
                        isComplete={!isLive || index < lines.length - 1}
                      />
                    </motion.div>
                  );
                case 'thinking':
                  return (
                    <motion.div
                      key={index}
                      initial={{ opacity: 0 }}
                      animate={{ opacity: 1 }}
                      transition={{ duration: 0.15 }}
                    >
                      <ThinkingBlock content={line.content} />
                    </motion.div>
                  );
                case 'error':
                  return (
                    <motion.div
                      key={index}
                      initial={{ opacity: 0 }}
                      animate={{ opacity: 1 }}
                      transition={{ duration: 0.15 }}
                    >
                      <ErrorLine content={line.content} />
                    </motion.div>
                  );
                case 'text':
                default:
                  return (
                    <div key={index} className="whitespace-pre-wrap break-words leading-relaxed py-0.5">
                      <TypingText content={line.content} animate={shouldAnimate} />
                    </div>
                  );
              }
            })}
          </div>
        )}

        {/* Blinking cursor at end when live */}
        {isLive && lines.length > 0 && (
          <motion.span
            animate={{ opacity: [1, 0] }}
            transition={{ duration: 0.53, repeat: Infinity }}
            className="text-zinc-500 inline-block"
          >
            _
          </motion.span>
        )}
      </div>
    </div>
  );
}
