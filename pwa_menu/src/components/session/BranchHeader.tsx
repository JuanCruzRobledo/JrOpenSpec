import { useTranslation } from 'react-i18next';

interface BranchHeaderProps {
  branchName: string;
  tableName: string;
  logoUrl: string | null;
}

/**
 * Landing page header showing the branch name, table identifier, and optional logo.
 */
export function BranchHeader({ branchName, tableName, logoUrl }: BranchHeaderProps) {
  const { t } = useTranslation('session');

  return (
    <header className="flex flex-col items-center gap-3 text-center">
      {/* Logo placeholder */}
      <div className="flex h-16 w-16 items-center justify-center rounded-2xl bg-accent/20 overflow-hidden">
        {logoUrl ? (
          <img
            src={logoUrl}
            alt={branchName}
            className="h-full w-full object-cover"
          />
        ) : (
          <span
            className="text-2xl font-bold text-accent"
            aria-hidden="true"
          >
            {branchName.charAt(0).toUpperCase()}
          </span>
        )}
      </div>

      <div>
        <h1 className="text-xl font-bold text-surface-text">
          {t('landing.title', { branchName })}
        </h1>
        <p className="text-sm text-surface-text/60">
          {t('landing.subtitle', { tableName })}
        </p>
      </div>
    </header>
  );
}
