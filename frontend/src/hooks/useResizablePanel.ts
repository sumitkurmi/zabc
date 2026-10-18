import { useState, useEffect, useCallback } from 'react';

/**
 * Custom hook for managing resizable side-panel width logic.
 * Specification Section 5.4:
 * Min width 320px, max 80% of viewport, default 50%.
 * Chosen width stored in localStorage.
 * Double-click handle resets to 50%.
 */
export function useResizablePanel() {
  const [width, setWidth] = useState<number>(() => {
    const saved = localStorage.getItem('chat_panel_width');
    if (saved) {
      const parsed = parseInt(saved, 10);
      if (!isNaN(parsed) && parsed >= 320) return parsed;
    }
    return Math.floor(window.innerWidth * 0.5);
  });

  const [isResizing, setIsResizing] = useState(false);

  const startResizing = useCallback((e: React.MouseEvent) => {
    e.preventDefault();
    setIsResizing(true);
  }, []);

  const resetWidth = useCallback(() => {
    const defaultWidth = Math.floor(window.innerWidth * 0.5);
    setWidth(defaultWidth);
    localStorage.setItem('chat_panel_width', String(defaultWidth));
  }, []);

  useEffect(() => {
    const handleMouseMove = (e: MouseEvent) => {
      if (!isResizing) return;
      const newWidth = window.innerWidth - e.clientX;
      const minWidth = 320;
      const maxWidth = window.innerWidth * 0.8;

      if (newWidth >= minWidth && newWidth <= maxWidth) {
        setWidth(newWidth);
        localStorage.setItem('chat_panel_width', String(Math.floor(newWidth)));
      }
    };

    const handleMouseUp = () => {
      if (isResizing) {
        setIsResizing(false);
      }
    };

    if (isResizing) {
      window.addEventListener('mousemove', handleMouseMove);
      window.addEventListener('mouseup', handleMouseUp);
    }

    return () => {
      window.removeEventListener('mousemove', handleMouseMove);
      window.removeEventListener('mouseup', handleMouseUp);
    };
  }, [isResizing]);

  return { width, isResizing, startResizing, resetWidth };
}
