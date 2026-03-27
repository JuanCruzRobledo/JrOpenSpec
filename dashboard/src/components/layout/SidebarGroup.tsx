import { useState, type ReactNode } from 'react';
import { cn } from '@/lib/cn';

interface Props {
  label: string;
  children: ReactNode;
  collapsed?: boolean;
  defaultOpen?: boolean;
}

export function SidebarGroup({ label, children, collapsed = false, defaultOpen = true }: Props) {
  const [isOpen, setIsOpen] = useState(defaultOpen);

  if (collapsed) {
    // When sidebar is collapsed, just render the items without group headers
    return <div className="flex flex-col gap-1">{children}</div>;
  }

  return (
    <div className="flex flex-col">
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="flex items-center justify-between px-3 py-2 text-xs font-semibold uppercase tracking-wider text-text-tertiary hover:text-text-secondary transition-colors"
      >
        <span>{label}</span>
        <svg
          xmlns="http://www.w3.org/2000/svg"
          width="14"
          height="14"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          strokeWidth="2"
          strokeLinecap="round"
          strokeLinejoin="round"
          className={cn(
            'transition-transform duration-200',
            isOpen ? 'rotate-0' : '-rotate-90',
          )}
        >
          <polyline points="6 9 12 15 18 9" />
        </svg>
      </button>
      {isOpen ? (
        <div className="flex flex-col gap-0.5 ml-1">{children}</div>
      ) : null}
    </div>
  );
}
