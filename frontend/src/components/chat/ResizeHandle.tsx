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
      title="Drag to resize panel, double-click to reset width"
      className={`hidden md:flex absolute left-0 top-0 bottom-0 w-2.5 z-20 hover:bg-transparent transition-colors cursor-col-resize items-center justify-center select-none group 
      ${
        isResizing ? 'bg-transparent' : 'bg-transparent'}
        `}
    >
      <div className={`w-0.5 h-12 rounded-full bg-slate-300 group-hover:bg-white transition-colors ${
        isResizing ? 'bg-white' : ''
      }`} />
    </div>
  );
};
