/**
 * StatusLegend — color legend showing all 6 table statuses.
 * Pure presentational component with no state.
 */
import { cn } from '@/lib/cn';

const LEGEND_ITEMS: Array<{ color: string; label: string }> = [
  { color: 'bg-green-500',  label: 'Libre' },
  { color: 'bg-red-500',    label: 'Ocupada' },
  { color: 'bg-yellow-500', label: 'Pedido Solicitado' },
  { color: 'bg-blue-500',   label: 'Pedido Cumplido' },
  { color: 'bg-purple-500', label: 'Cuenta' },
  { color: 'bg-gray-500',   label: 'Inactiva' },
];

interface Props {
  className?: string;
}

export function StatusLegend({ className }: Props) {
  return (
    <div className={cn('flex flex-wrap gap-4', className)}>
      {LEGEND_ITEMS.map((item) => (
        <div key={item.label} className="flex items-center gap-2">
          <span className={cn('w-3 h-3 rounded-full', item.color)} />
          <span className="text-xs text-text-secondary">{item.label}</span>
        </div>
      ))}
    </div>
  );
}
