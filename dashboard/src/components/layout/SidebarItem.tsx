import { NavLink } from 'react-router-dom';
import { cn } from '@/lib/cn';

interface Props {
  to: string;
  label: string;
  icon: React.ReactNode;
  collapsed?: boolean;
}

export function SidebarItem({ to, label, icon, collapsed = false }: Props) {
  return (
    <NavLink
      to={to}
      className={({ isActive }) =>
        cn(
          'flex items-center gap-3 rounded-lg px-3 py-2 text-sm transition-colors',
          isActive
            ? 'bg-accent/10 text-accent font-medium'
            : 'text-text-secondary hover:bg-bg-elevated hover:text-text-primary',
          collapsed && 'justify-center px-2',
        )
      }
      title={collapsed ? label : undefined}
    >
      <span className="shrink-0 w-5 h-5 flex items-center justify-center">
        {icon}
      </span>
      {!collapsed ? <span>{label}</span> : null}
    </NavLink>
  );
}
