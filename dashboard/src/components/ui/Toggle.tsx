import { cn } from '@/lib/cn';

interface Props {
  label?: string;
  checked: boolean;
  onChange: (checked: boolean) => void;
  disabled?: boolean;
  className?: string;
}

export function Toggle({ label, checked, onChange, disabled = false, className }: Props) {
  return (
    <label
      className={cn(
        'inline-flex items-center gap-3 cursor-pointer',
        disabled && 'opacity-50 cursor-not-allowed',
        className,
      )}
    >
      <button
        type="button"
        role="switch"
        aria-checked={checked}
        disabled={disabled}
        onClick={() => onChange(!checked)}
        className={cn(
          'relative inline-flex h-6 w-11 shrink-0 rounded-full border-2 border-transparent transition-colors duration-200',
          'focus:outline-none focus:ring-2 focus:ring-accent/40 focus:ring-offset-2 focus:ring-offset-bg-primary',
          checked ? 'bg-accent' : 'bg-bg-elevated',
        )}
      >
        <span
          className={cn(
            'pointer-events-none inline-block h-5 w-5 rounded-full bg-white shadow-lg transition-transform duration-200',
            checked ? 'translate-x-5' : 'translate-x-0',
          )}
        />
      </button>
      {label ? (
        <span className="text-sm text-text-secondary">{label}</span>
      ) : null}
    </label>
  );
}
