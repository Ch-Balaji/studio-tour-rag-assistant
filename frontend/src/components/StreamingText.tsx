/**
 * Streaming Text Component with Typing Animation
 */

'use client';

import { useEffect, useState } from 'react';

interface StreamingTextProps {
  text: string;
  isComplete?: boolean;
}

export default function StreamingText({ text, isComplete = false }: StreamingTextProps) {
  const [displayedText, setDisplayedText] = useState('');
  const [currentIndex, setCurrentIndex] = useState(0);

  useEffect(() => {
    if (isComplete) {
      setDisplayedText(text);
      return;
    }

    if (currentIndex < text.length) {
      const timer = setTimeout(() => {
        setDisplayedText(text.slice(0, currentIndex + 1));
        setCurrentIndex(currentIndex + 1);
      }, 10);

      return () => clearTimeout(timer);
    }
  }, [text, currentIndex, isComplete]);

  useEffect(() => {
    setCurrentIndex(0);
    setDisplayedText('');
  }, [text]);

  return (
    <span>
      {displayedText}
      {!isComplete && <span className="animate-pulse">▌</span>}
    </span>
  );
}

