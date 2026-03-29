import { Outlet } from 'react-router-dom';
import { LanguageSelector } from '@/components/layout/LanguageSelector';

/**
 * Layout for unauthenticated landing/QR entry pages.
 * Dark background, centered content, no navigation.
 * Language selector floats at the top right.
 */
export function LandingLayout() {
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
