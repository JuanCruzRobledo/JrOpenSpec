import { useTranslation } from 'react-i18next';
import type { CrossReactionHiddenSummary } from '@/lib/filter-engine';

interface CrossReactionFilterFeedbackProps {
  summary: CrossReactionHiddenSummary;
}

export function CrossReactionFilterFeedback({
  summary,
}: CrossReactionFilterFeedbackProps) {
  const { t } = useTranslation('menu');

  return (
    <div
      role="status"
      aria-live="polite"
      className="rounded-2xl border border-warning/30 bg-warning/10 px-4 py-3 text-left"
    >
      <p className="text-sm font-semibold text-warning">
        {t('crossReactionFeedback.title', { count: summary.hiddenProductCount })}
      </p>
      <p className="mt-1 text-sm text-text-secondary">
        {t('crossReactionFeedback.description', {
          selectedAllergens: summary.selectedAllergenNames.join(', '),
          crossReactions: summary.crossReactionAllergenNames.join(', '),
        })}
      </p>
    </div>
  );
}
