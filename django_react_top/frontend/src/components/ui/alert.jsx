import React from 'react';
import { cn } from '../../lib/utils';

const variants = {
  default: 'border-slate-200 bg-white text-slate-700',
  warning: 'border-amber-200 bg-amber-50 text-amber-800',
  danger: 'border-rose-200 bg-rose-50 text-rose-800',
  success: 'border-emerald-200 bg-emerald-50 text-emerald-800',
};

export function Alert({ className, variant = 'default', ...props }) {
  return <div className={cn('rounded-lg border p-3 text-sm', variants[variant], className)} role="status" {...props} />;
}
