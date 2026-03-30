import { Outlet, useParams } from 'react-router-dom';
import { useActivityTracker } from '@/hooks/useActivityTracker';
import { BottomBar } from '@/components/layout/BottomBar';
import { useDynamicManifest } from '@/hooks/useDynamicManifest';
import { useSessionStore, selectBranchName } from '@/stores/session.store';
import { humanizeSlug } from '@/lib/text';

/**
 * Layout for authenticated menu pages.
 *
 * Structure:
 * - Fixed header (rendered by MenuHeader inside child page)
 * - Scrollable main content area (rendered by child page)
 * - Fixed BottomBar at the bottom (always visible on menu pages)
 *
 * useActivityTracker is active here to maintain the 8-hour sliding window.
 * The header is mounted by the child page so it can carry page-specific state
 * (e.g. category tabs, filter count badge).
 */
export function MenuLayout() {
  const params = useParams<{ tenant: string; branch: string }>();
  const branchName = useSessionStore(selectBranchName);

  // Tracks user activity for session sliding-window expiry
  useActivityTracker();

  useDynamicManifest({
    tenant: params.tenant,
    branch: params.branch,
    branchName: branchName ?? (params.branch ? humanizeSlug(params.branch) : undefined),
  });

  return (
    <div className="flex min-h-dvh flex-col bg-surface-bg">
      <Outlet />
      <BottomBar />
    </div>
  );
}
