import { useUIStore } from '@/stores/ui.store';
import { BranchSelector } from '@/components/layout/BranchSelector';
import { UserMenu } from '@/components/layout/UserMenu';
import { SIDEBAR_WIDTH, SIDEBAR_COLLAPSED_WIDTH } from '@/config/constants';

interface Props {}

export function Header(_props: Props) {
  const sidebarCollapsed = useUIStore((s) => s.sidebarCollapsed);
  const marginLeft = sidebarCollapsed ? SIDEBAR_COLLAPSED_WIDTH : SIDEBAR_WIDTH;

  return (
    <header
      className="fixed top-0 right-0 h-16 bg-bg-surface border-b border-border-default z-30 flex items-center justify-between px-6 transition-[left] duration-200"
      style={{ left: marginLeft }}
    >
      {/* Left: Restaurant name placeholder */}
      <div className="text-sm font-medium text-text-primary">
        Panel de Administracion
      </div>

      {/* Center: Branch selector */}
      <BranchSelector />

      {/* Right: User menu */}
      <UserMenu />
    </header>
  );
}
