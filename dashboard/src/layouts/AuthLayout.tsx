import { Outlet } from 'react-router-dom';

interface Props {}

/**
 * Layout for unauthenticated screens (login).
 * Centered card with dark background.
 */
export function AuthLayout(_props: Props) {
  return (
    <div className="min-h-screen bg-bg-primary flex items-center justify-center p-4">
      <div className="w-full max-w-md">
        <Outlet />
      </div>
    </div>
  );
}
