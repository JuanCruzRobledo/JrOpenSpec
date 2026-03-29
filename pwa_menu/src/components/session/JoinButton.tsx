import { useTranslation } from 'react-i18next';
import { Button } from '@/components/ui/Button';

interface JoinButtonProps {
  isLoading: boolean;
}

/**
 * Submit button for the landing page join form.
 * Controlled by the form's pending state (React 19 useActionState).
 */
export function JoinButton({ isLoading }: JoinButtonProps) {
  const { t } = useTranslation('session');

  return (
    <Button
      type="submit"
      variant="primary"
      size="lg"
      isLoading={isLoading}
      className="w-full"
    >
      {isLoading ? t('landing.joining') : t('landing.joinButton')}
    </Button>
  );
}
