// MODULE: Complaint Management (Part 2) - this file belongs to the code for this module.
// StarRating component providing 1-5 star selection or read-only display.

import React from 'react';
import { Star } from 'lucide-react';

interface StarRatingProps {
  value: number;
  onChange?: (val: number) => void;
  readOnly?: boolean;
  size?: number;
}

export const StarRating: React.FC<StarRatingProps> = ({
  value,
  onChange,
  readOnly = false,
  size = 20
}) => {
  return (
    <div className="flex items-center gap-1">
      {[1, 2, 3, 4, 5].map((star) => (
        <button
          key={star}
          type="button"
          disabled={readOnly}
          onClick={() => onChange && onChange(star)}
          className={`${readOnly ? 'cursor-default' : 'cursor-pointer hover:scale-110 transition-transform'}`}
        >
          <Star
            style={{ width: size, height: size }}
            className={star <= value ? 'text-amber-400 fill-amber-400' : 'text-slate-300'}
          />
        </button>
      ))}
    </div>
  );
};
