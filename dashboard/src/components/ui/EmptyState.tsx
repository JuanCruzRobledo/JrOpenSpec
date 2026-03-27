import { Button } from '@/components/ui/Button';

interface Props {
  title: string;
  description?: string;
  actionLabel?: string;
  onAction?: () => void;
  icon?: React.ReactNode;
}

export function EmptyState({ title, description, actionLabel, onAction, icon }: Props) {
  return (
    <div className="flex flex-col items-center justify-center py-16 text-center">
      {icon ? (
        <div className="mb-4 text-text-tertiary">{icon}</div>
      ) : (
        <div className="mb-4 text-4xl">📭</div>
      )}
      <h3 className="text-lg font-medium text-text-primary">{title}</h3>
      {description ? (
        <p className="mt-1 text-sm text-text-secondary max-w-md">{description}</p>
      ) : null}
      {actionLabel && onAction ? (
        <Button onClick={onAction} className="mt-4">
          {actionLabel}
        </Button>
      ) : null}
    </div>
  );
}
