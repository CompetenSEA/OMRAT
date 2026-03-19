import React from 'react';
import { cn } from '../../lib/utils';

export function Progress({ value = 0, className }) {
  const safe = Math.max(0, Math.min(100, value));
  return (
    <div className={cn('h-2 w-full overflow-hidden rounded-full bg-slate-100', className)}>
      <div className="h-full rounded-full bg-slate-900 transition-all" style={{ width: `${safe}%` }} />
    </div>
  );
}
