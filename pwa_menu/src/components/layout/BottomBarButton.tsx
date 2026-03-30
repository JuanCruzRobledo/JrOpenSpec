import { useTranslation } from 'react-i18next';
import { cn } from '@/lib/cn';

type BottomBarLabelKey = 'bottomBar.callWaiter' | 'bottomBar.history' | 'bottomBar.myBill';

interface BottomBarButtonProps {
  /** i18n key for accessible label (also shown as tooltip) */
  labelKey: BottomBarLabelKey;
  /** SVG icon element to render inside the FAB */
  icon: React.ReactNode;
  onClick: () => void;
  className?: string;
}

/**
 * Individual FAB button for the BottomBar.
 *
 * 56×56 px, accent orange background, white icon.
 * 44 px is the WCAG minimum touch target — 56 px exceeds that.
 */
export function BottomBarButton({ labelKey, icon, onClick, className }: BottomBarButtonProps) {
  const { t } = useTranslation('menu');
  const label = t(labelKey);

  return (
    <button
      type="button"
      aria-label={label}
      title={label}
      onClick={onClick}
      className={cn(
        'flex h-14 w-14 items-center justify-center rounded-full',
        'bg-accent text-white shadow-lg',
        'transition-transform active:scale-95',
        'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent focus-visible:ring-offset-2',
        className
      )}
    >
      {icon}
    </button>
  );
}
