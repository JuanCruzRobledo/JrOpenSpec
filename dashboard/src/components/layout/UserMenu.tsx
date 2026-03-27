import { useState, useRef, useEffect } from 'react';
import { useAuthStore } from '@/stores/auth.store';

interface Props {}

export function UserMenu(_props: Props) {
  const user = useAuthStore((s) => s.user);
  const logout = useAuthStore((s) => s.logout);
  const [isOpen, setIsOpen] = useState(false);
  const menuRef = useRef<HTMLDivElement>(null);

  // Close on outside click
  useEffect(() => {
    if (!isOpen) return;
    const handleClick = (e: MouseEvent) => {
      if (menuRef.current && !menuRef.current.contains(e.target as Node)) {
        setIsOpen(false);
      }
    };
    document.addEventListener('mousedown', handleClick);
    return () => document.removeEventListener('mousedown', handleClick);
  }, [isOpen]);

  const displayName = user
    ? `${user.first_name} ${user.last_name}`
    : 'Usuario';

  const initials = user
    ? `${user.first_name.charAt(0)}${user.last_name.charAt(0)}`.toUpperCase()
    : 'U';

  return (
    <div ref={menuRef} className="relative">
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="flex items-center gap-2 rounded-lg px-2 py-1.5 hover:bg-bg-elevated transition-colors"
        aria-label="Menu de usuario"
      >
        <div className="w-8 h-8 rounded-full bg-accent/20 text-accent flex items-center justify-center text-sm font-semibold">
          {initials}
        </div>
        <span className="text-sm text-text-primary hidden sm:block">
          {displayName}
        </span>
      </button>

      {isOpen ? (
        <div className="absolute right-0 mt-2 w-56 rounded-lg border border-border-default bg-bg-surface shadow-xl z-50">
          <div className="px-4 py-3 border-b border-border-default">
            <p className="text-sm font-medium text-text-primary">{displayName}</p>
            <p className="text-xs text-text-tertiary">{user?.email}</p>
          </div>
          <div className="py-1">
            <button
              onClick={() => {
                setIsOpen(false);
                logout();
              }}
              className="w-full text-left px-4 py-2 text-sm text-error hover:bg-bg-elevated transition-colors"
            >
              Cerrar sesion
            </button>
          </div>
        </div>
      ) : null}
    </div>
  );
}
