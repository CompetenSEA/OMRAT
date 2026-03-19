import React from 'react';
import { cn } from '../../lib/utils';

export function Tabs({ value, onValueChange, children, className }) {
  return (
    <div className={cn(className)} data-tabs-root="true">
      {React.Children.map(children, (child) => {
        if (!React.isValidElement(child)) return child;
        return React.cloneElement(child, { value, onValueChange });
      })}
    </div>
  );
}

export function TabsList({ children, className, value, onValueChange }) {
  return (
    <div className={cn('inline-flex rounded-lg bg-slate-100 p-1', className)}>
      {React.Children.map(children, (child) => {
        if (!React.isValidElement(child)) return child;
        return React.cloneElement(child, { value, onValueChange });
      })}
    </div>
  );
}

export function TabsTrigger({ value: selectedValue, onValueChange, tabValue, children, className }) {
  const active = selectedValue === tabValue;
  return (
    <button
      type="button"
      onClick={() => onValueChange?.(tabValue)}
      className={cn(
        'rounded-md px-3 py-1.5 text-sm font-medium transition-colors',
        active ? 'bg-white text-slate-900 shadow-sm' : 'text-slate-600 hover:text-slate-900',
        className,
      )}
    >
      {children}
    </button>
  );
}

export function TabsContent({ value, tabValue, children, className }) {
  if (value !== tabValue) return null;
  return <div className={cn('mt-4', className)}>{children}</div>;
}
