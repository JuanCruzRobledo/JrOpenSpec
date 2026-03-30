import { Outlet, useParams } from 'react-router-dom';
import { LanguageSelector } from '@/components/layout/LanguageSelector';
import { useDynamicManifest } from '@/hooks/useDynamicManifest';
import { humanizeSlug } from '@/lib/text';

/**
 * Layout for unauthenticated landing/QR entry pages.
 * Dark background, centered content, no navigation.
 * Language selector floats at the top right.
 */
export function LandingLayout() {
  const params = useParams<{ tenant: string; branch: string }>();

  useDynamicManifest({
    tenant: params.tenant,
    branch: params.branch,
    branchName: params.branch ? humanizeSlug(params.branch) : undefined,
  });

  return (
    <div className="relative min-h-dvh bg-surface-bg flex flex-col">
      {/* Language selector — top right */}
      <div className="absolute top-4 right-4 z-10">
        <LanguageSelector />
      </div>

      {/* Centered content */}
      <main className="flex flex-1 items-center justify-center">
        <Outlet />
      </main>
    </div>
  );
}
