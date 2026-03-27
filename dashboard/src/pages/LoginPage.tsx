import { useActionState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuthStore } from '@/stores/auth.store';
import { useUIStore } from '@/stores/ui.store';
import { Input } from '@/components/ui/Input';
import { Button } from '@/components/ui/Button';
import { ROUTES } from '@/router/routes';
import { logger } from '@/lib/logger';

interface LoginFormState {
  error: string | null;
  email: string;
  password: string;
}

const initialState: LoginFormState = {
  error: null,
  email: '',
  password: '',
};

/**
 * Login page — uses React 19 useActionState for form handling.
 */
export default function LoginPage() {
  const navigate = useNavigate();
  const login = useAuthStore((s) => s.login);
  const addToast = useUIStore((s) => s.addToast);

  const [state, submitAction, isPending] = useActionState(
    async (_prev: LoginFormState, formData: FormData): Promise<LoginFormState> => {
      const email = formData.get('email') as string;
      const password = formData.get('password') as string;

      if (!email || !password) {
        return { error: 'Email y contrasena son obligatorios', email, password };
      }

      try {
        await login(email, password);
        navigate(ROUTES.DASHBOARD, { replace: true });
        return { error: null, email: '', password: '' };
      } catch (err) {
        logger.warn('Login failed', err);
        const message = 'Credenciales invalidas';
        addToast({ type: 'error', message });
        return { error: message, email, password };
      }
    },
    initialState,
  );

  return (
    <div className="rounded-xl bg-bg-surface border border-border-default p-8 shadow-xl">
      {/* Logo */}
      <div className="flex flex-col items-center mb-8">
        <div className="w-14 h-14 rounded-xl bg-accent flex items-center justify-center text-white text-2xl font-bold mb-4">
          I
        </div>
        <h1 className="text-2xl font-bold text-text-primary">Integrador</h1>
        <p className="text-sm text-text-secondary mt-1">
          Panel de Administracion
        </p>
      </div>

      <form action={submitAction} className="flex flex-col gap-4">
        <Input
          name="email"
          type="email"
          label="Email"
          placeholder="admin@restaurant.com"
          defaultValue={state.email}
          isRequired
          autoComplete="email"
          autoFocus
        />
        <Input
          name="password"
          type="password"
          label="Contrasena"
          placeholder="••••••••"
          defaultValue={state.password}
          isRequired
          autoComplete="current-password"
        />

        {state.error ? (
          <p className="text-sm text-error text-center" role="alert">
            {state.error}
          </p>
        ) : null}

        <Button type="submit" isLoading={isPending} className="mt-2 w-full">
          Ingresar
        </Button>
      </form>
    </div>
  );
}
