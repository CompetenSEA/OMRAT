import React from 'react';
import { cn } from '../../lib/utils';

export function Card({ className, ...props }) {
  return <div className={cn('rounded-lg border border-slate-200 bg-white shadow-sm', className)} {...props} />;
}

export function CardHeader({ className, ...props }) {
  return <div className={cn('border-b border-slate-100 p-4', className)} {...props} />;
}

export function CardTitle({ className, ...props }) {
  return <h3 className={cn('text-base font-semibold text-slate-900', className)} {...props} />;
}

export function CardDescription({ className, ...props }) {
  return <p className={cn('mt-1 text-sm text-slate-500', className)} {...props} />;
}

export function CardContent({ className, ...props }) {
  return <div className={cn('p-4', className)} {...props} />;
}
