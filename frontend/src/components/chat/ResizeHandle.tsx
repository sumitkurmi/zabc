import React from 'react';

export interface DragHandleProps {
  onMouseDown: (e: React.MouseEvent) => void;
  onDoubleClick: () => void;
  isResizing: boolean;
}

export const ResizeHandle: React.FC<DragHandleProps> = ({
  onMouseDown,
  onDoubleClick,
  isResizing,
}) => {
  return (
    <div
      onMouseDown={onMouseDown}
      onDoubleClick={onDoubleClick}
      title="Drag to resize, double-click to reset width"
      className={`hidden md:flex w-2 bg-slate-200 hover:bg-blue-600 transition-colors cursor-col-resize items-center justify-center select-none ${
        isResizing ? 'bg-blue-600' : ''
      }`}
    >
      <div className="w-1 h-8 bg-slate-400 rounded-full" />
    </div>
  );
};
