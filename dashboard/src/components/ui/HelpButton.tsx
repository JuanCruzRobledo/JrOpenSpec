import { useState } from 'react';
import { Modal } from '@/components/ui/Modal';
import { cn } from '@/lib/cn';

interface HelpContent {
  title: string;
  description: string;
  tips?: string[];
}

interface Props {
  content: HelpContent;
  size?: 'sm' | 'md';
  className?: string;
}

/**
 * Floating help button that opens a modal with contextual help.
 * MANDATORY on every Dashboard page.
 */
export function HelpButton({ content, size = 'md', className }: Props) {
  const [isOpen, setIsOpen] = useState(false);

  return (
    <>
      <button
        type="button"
        onClick={() => setIsOpen(true)}
        className={cn(
          'inline-flex items-center justify-center rounded-full bg-error text-white font-bold shadow-lg',
          'hover:bg-red-600 transition-colors focus:outline-none focus:ring-2 focus:ring-error/40',
          size === 'sm' ? 'h-7 w-7 text-xs' : 'h-10 w-10 text-sm',
          className,
        )}
        aria-label="Ayuda"
      >
        ?
      </button>

      <Modal isOpen={isOpen} onClose={() => setIsOpen(false)} title={content.title}>
        <p className="text-sm text-text-secondary leading-relaxed">
          {content.description}
        </p>
        {content.tips && content.tips.length > 0 ? (
          <div className="mt-4">
            <h4 className="text-sm font-medium text-text-primary mb-2">Consejos:</h4>
            <ul className="space-y-1.5">
              {content.tips.map((tip, i) => (
                <li key={i} className="text-sm text-text-secondary flex gap-2">
                  <span className="text-accent shrink-0">•</span>
                  <span>{tip}</span>
                </li>
              ))}
            </ul>
          </div>
        ) : null}
      </Modal>
    </>
  );
}
