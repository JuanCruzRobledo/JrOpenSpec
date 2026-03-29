import { Suspense } from 'react';
import { RouterProvider } from 'react-router-dom';
import { router } from '@/router/index';
import { ToastContainer } from '@/components/ui/ToastContainer';
import { OfflineIndicator } from '@/components/ui/OfflineIndicator';
import { UpdateToast } from '@/components/pwa/UpdateToast';
import { InstallBanner } from '@/components/ui/InstallBanner';
import { MenuSkeleton } from '@/components/menu/MenuSkeleton';

/**
 * Application root.
 *
 * Structure:
 * - RouterProvider handles all navigation
 * - Overlay components mounted outside the router so they survive route changes:
 *   - ToastContainer    — ephemeral toast stack
 *   - OfflineIndicator  — top pill when offline
 *   - UpdateToast       — persistent SW update prompt (user consent required)
 *   - InstallBanner     — PWA install prompt (delayed, dismissible)
 *
 * Hard Stop Rules:
 * - UpdateToast NEVER auto-reloads — user must click the action button.
 * - OfflineIndicator ALWAYS visible when offline (Hard Stop Rule #1).
 */
export default function App() {
  return (
    <>
      <Suspense fallback={<MenuSkeleton />}>
        <RouterProvider router={router} />
      </Suspense>

      {/* Global overlay components — outside router, always mounted */}
      <ToastContainer />
      <OfflineIndicator />
      <UpdateToast />
      <InstallBanner />
    </>
  );
}
