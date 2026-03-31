/**
 * ShiftSelector — 3-button toggle for morning/afternoon/night shift selection.
 * Presentational component.
 */
import { cn } from '@/lib/cn';

const SHIFTS = [
  { value: 'morning', label: 'Mañana', icon: '☀️' },
  { value: 'afternoon', label: 'Tarde', icon: '🌤️' },
  { value: 'night', label: 'Noche', icon: '🌙' },
] as const;

type ShiftValue = typeof SHIFTS[number]['value'];

interface Props {
  selected: string | null;
  onChange: (shift: ShiftValue) => void;
}

export function ShiftSelector({ selected, onChange }: Props) {
  return (
    <div className="inline-flex rounded-lg border border-border-default overflow-hidden">
      {SHIFTS.map((shift) => (
        <button
          key={shift.value}
          type="button"
          onClick={() => onChange(shift.value)}
          className={cn(
            'px-4 py-2 text-sm font-medium transition-colors',
            'border-r border-border-default last:border-r-0',
            selected === shift.value
              ? 'bg-accent text-white'
              : 'bg-bg-surface text-text-secondary hover:bg-bg-elevated',
          )}
        >
          <span className="mr-1.5">{shift.icon}</span>
          {shift.label}
        </button>
      ))}
    </div>
  );
}
