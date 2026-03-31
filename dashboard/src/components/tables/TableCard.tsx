/**
 * TableCard — displays a single table with status color, capacity, and elapsed time.
 * Presentational component: receives all data as props.
 */
import { useMemo } from 'react';
import { cn } from '@/lib/cn';
import type { TableStatus } from '@/types/table';

const STATUS_STYLES: Record<TableStatus, { bg: string; border: string; text: string; label: string }> = {
  libre:             { bg: 'bg-green-500/10',  border: 'border-l-green-500',  text: 'text-green-500',  label: 'Libre' },
  ocupada:           { bg: 'bg-red-500/10',    border: 'border-l-red-500',    text: 'text-red-500',    label: 'Ocupada' },
  pedido_solicitado: { bg: 'bg-yellow-500/10', border: 'border-l-yellow-500', text: 'text-yellow-600', label: 'Pedido Solicitado' },
  pedido_cumplido:   { bg: 'bg-blue-500/10',   border: 'border-l-blue-500',   text: 'text-blue-500',   label: 'Pedido Cumplido' },
  cuenta:            { bg: 'bg-purple-500/10', border: 'border-l-purple-500', text: 'text-purple-500', label: 'Cuenta' },
  inactiva:          { bg: 'bg-gray-500/10',   border: 'border-l-gray-500',   text: 'text-gray-500',   label: 'Inactiva' },
};

/** Format elapsed time from a date string to a human-readable string. */
function formatElapsed(dateStr: string | null): string {
  if (!dateStr) return '';
  const diff = Date.now() - new Date(dateStr).getTime();
  if (diff < 0) return '';
  const minutes = Math.floor(diff / 60_000);
  if (minutes < 1) return 'ahora';
  if (minutes < 60) return `${minutes}m`;
  const hours = Math.floor(minutes / 60);
  if (hours < 24) return `${hours}h ${minutes % 60}m`;
  return `${Math.floor(hours / 24)}d`;
}

interface Props {
  codigo: string | null;
  numero: number;
  capacidad: number;
  estado: TableStatus;
  statusChangedAt: string | null;
  onClick: () => void;
}

export function TableCard({ codigo, numero, capacidad, estado, statusChangedAt, onClick }: Props) {
  const style = STATUS_STYLES[estado];
  const elapsed = useMemo(() => formatElapsed(statusChangedAt), [statusChangedAt]);

  return (
    <button
      type="button"
      onClick={onClick}
      className={cn(
        'relative flex flex-col gap-2 p-4 rounded-xl border-l-[3px] cursor-pointer',
        'transition-all duration-150 hover:scale-[1.02] hover:shadow-lg',
        'bg-bg-surface border border-border-default',
        style.border,
        style.bg,
      )}
    >
      {/* Table code / number */}
      <span className="text-lg font-bold text-text-primary">
        {codigo ?? `Mesa ${numero}`}
      </span>

      {/* Capacity */}
      <div className="flex items-center gap-1.5 text-sm text-text-secondary">
        <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
          <path d="M17 21v-2a4 4 0 00-4-4H5a4 4 0 00-4 4v2" />
          <circle cx="9" cy="7" r="4" />
          <path d="M23 21v-2a4 4 0 00-3-3.87" />
          <path d="M16 3.13a4 4 0 010 7.75" />
        </svg>
        <span>{capacidad}</span>
      </div>

      {/* Status badge */}
      <div className="flex items-center justify-between">
        <span className={cn('text-xs font-medium', style.text)}>
          {style.label}
        </span>
        {elapsed ? (
          <span className="text-xs text-text-tertiary">{elapsed}</span>
        ) : null}
      </div>
    </button>
  );
}
