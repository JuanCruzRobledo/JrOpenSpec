import { Outlet } from 'react-router-dom';
import { useUIStore } from '@/stores/ui.store';
import { Sidebar } from '@/components/layout/Sidebar';
import { Header } from '@/components/layout/Header';
import { ToastContainer } from '@/components/ui/ToastContainer';
import { ConfirmDialog } from '@/components/ui/ConfirmDialog';
import { SIDEBAR_WIDTH, SIDEBAR_COLLAPSED_WIDTH } from '@/config/constants';

interface Props {}

/**
 * Main dashboard layout — sidebar + header + content area.
 * Portals: ToastContainer, ConfirmDialog.
 */
export function DashboardLayout(_props: Props) {
  const sidebarCollapsed = useUIStore((s) => s.sidebarCollapsed);
  const marginLeft = sidebarCollapsed ? SIDEBAR_COLLAPSED_WIDTH : SIDEBAR_WIDTH;

  return (
    <div className="min-h-screen bg-bg-primary">
      <Sidebar />
      <Header />

      <main
        className="pt-16 transition-[margin-left] duration-200"
        style={{ marginLeft }}
      >
        <div className="p-6 max-w-[1400px] mx-auto">
          <Outlet />
        </div>
      </main>

      <ToastContainer />
      <ConfirmDialog />
    </div>
  );
}
