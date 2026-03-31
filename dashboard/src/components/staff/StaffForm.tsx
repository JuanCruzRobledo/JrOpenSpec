/**
 * StaffForm — create/edit form for staff members.
 * Uses useActionState per React 19 pattern.
 * Password field only shown on create mode.
 */
import { useActionState, useCallback } from 'react';
import { Input } from '@/components/ui/Input';
import { Select } from '@/components/ui/Select';
import { Button } from '@/components/ui/Button';
import { useToast } from '@/hooks/useToast';
import { logger } from '@/lib/logger';
import type { Staff, StaffCreate, StaffUpdate } from '@/types/staff';

const ROLE_OPTIONS = [
  { value: 'OWNER', label: 'Propietario' },
  { value: 'ADMIN', label: 'Administrador' },
  { value: 'MANAGER', label: 'Gerente' },
  { value: 'WAITER', label: 'Mozo' },
  { value: 'CHEF', label: 'Chef' },
  { value: 'CASHIER', label: 'Cajero' },
];

interface FormState {
  isSuccess: boolean;
  errors: Record<string, string>;
  message?: string;
}

interface Props {
  staff: Staff | null;
  onSuccess: () => void;
  onCancel: () => void;
  createFn: (data: StaffCreate) => Promise<Staff | null>;
  updateFn: (id: number, data: StaffUpdate) => Promise<Staff | null>;
}

export function StaffForm({ staff, onSuccess, onCancel, createFn, updateFn }: Props) {
  const toast = useToast();
  const isEditing = staff !== null;

  const submitAction = useCallback(
    async (_prevState: FormState, formData: FormData): Promise<FormState> => {
      const nombre_completo = formData.get('nombre_completo') as string;
      const email = formData.get('email') as string;
      const password = formData.get('password') as string;
      const rol = formData.get('rol') as string;
      const dni = (formData.get('dni') as string) || undefined;
      const fecha_contratacion = (formData.get('fecha_contratacion') as string) || undefined;

      // Validation
      const errors: Record<string, string> = {};
      if (!nombre_completo || nombre_completo.trim().length < 2) {
        errors.nombre_completo = 'El nombre debe tener al menos 2 caracteres';
      }
      if (!isEditing) {
        if (!email || !email.includes('@')) {
          errors.email = 'Ingresa un email valido';
        }
        if (!password || password.length < 8) {
          errors.password = 'La contraseña debe tener al menos 8 caracteres';
        }
      }
      if (!rol) {
        errors.rol = 'Selecciona un rol';
      }

      if (Object.keys(errors).length > 0) {
        return { isSuccess: false, errors };
      }

      try {
        if (isEditing && staff) {
          const updateData: StaffUpdate = {
            nombre_completo: nombre_completo.trim(),
            rol,
            dni,
            fecha_contratacion,
          };
          await updateFn(staff.id, updateData);
        } else {
          const createData: StaffCreate = {
            nombre_completo: nombre_completo.trim(),
            email,
            password,
            rol,
            dni,
            fecha_contratacion,
          };
          await createFn(createData);
        }

        onSuccess();
        return { isSuccess: true, errors: {} };
      } catch (err) {
        const message = err instanceof Error ? err.message : 'Error al guardar';
        logger.error('Failed to save staff member', err);
        toast.error(message);
        return { isSuccess: false, errors: {}, message };
      }
    },
    [staff, isEditing, createFn, updateFn, onSuccess, toast],
  );

  const [state, formAction, isPending] = useActionState<FormState, FormData>(
    submitAction,
    { isSuccess: false, errors: {} },
  );

  return (
    <form action={formAction}>
      <div className="space-y-4">
        <Input
          name="nombre_completo"
          label="Nombre completo"
          isRequired
          defaultValue={staff?.nombre_completo ?? ''}
          error={state.errors.nombre_completo}
          placeholder="Nombre y apellido"
          disabled={isPending}
        />

        {!isEditing ? (
          <>
            <Input
              name="email"
              label="Email"
              type="email"
              isRequired
              defaultValue=""
              error={state.errors.email}
              placeholder="email@ejemplo.com"
              disabled={isPending}
            />

            <Input
              name="password"
              label="Contraseña"
              type="password"
              isRequired
              defaultValue=""
              error={state.errors.password}
              placeholder="Minimo 8 caracteres"
              disabled={isPending}
            />
          </>
        ) : null}

        <Select
          name="rol"
          label="Rol"
          isRequired
          options={ROLE_OPTIONS}
          placeholder="Seleccionar rol"
          defaultValue={staff?.rol ?? ''}
          error={state.errors.rol}
          disabled={isPending}
        />

        <Input
          name="dni"
          label="DNI"
          defaultValue={staff?.dni ?? ''}
          placeholder="Documento de identidad"
          disabled={isPending}
        />

        <Input
          name="fecha_contratacion"
          label="Fecha de contratacion"
          type="date"
          defaultValue={staff?.fecha_contratacion ?? ''}
          disabled={isPending}
        />
      </div>

      {state.message && !state.isSuccess ? (
        <p className="mt-4 text-sm text-error">{state.message}</p>
      ) : null}

      <div className="mt-6 flex justify-end gap-3">
        <Button type="button" variant="secondary" onClick={onCancel} disabled={isPending}>
          Cancelar
        </Button>
        <Button type="submit" isLoading={isPending}>
          {isEditing ? 'Guardar' : 'Crear miembro'}
        </Button>
      </div>
    </form>
  );
}
