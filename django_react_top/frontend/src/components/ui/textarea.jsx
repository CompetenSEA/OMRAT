import React from 'react';
import { cn } from '../../lib/utils';

export function Textarea({ className, ...props }) {
  return (
    <textarea
      className={cn(
        'w-full min-h-[80px] rounded-md border border-slate-300 bg-white px-3 py-2 text-sm text-slate-900 placeholder:text-slate-400 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-slate-400',
        className,
      )}
      {...props}
    />
  );
}
