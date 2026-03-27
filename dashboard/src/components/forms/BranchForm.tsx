import { useActionState, useCallback } from 'react';
import { Input } from '@/components/ui/Input';
import { Button } from '@/components/ui/Button';
import { useToast } from '@/hooks/useToast';
import { logger } from '@/lib/logger';
import type { Branch, BranchCreate, BranchUpdate } from '@/types/branch';

interface FormState {
  isSuccess: boolean;
  errors: Record<string, string>;
  message?: string;
}

interface Props {
  /** Branch to edit (null for create mode) */
  branch: Branch | null;
  onSuccess: () => void;
  onCancel: () => void;
  createFn: (data: BranchCreate) => Promise<Branch | null>;
  updateFn: (id: number, data: BranchUpdate) => Promise<Branch | null>;
}

/**
 * Branch create/edit form.
 * Uses useActionState per React 19 pattern.
 */
export function BranchForm({ branch, onSuccess, onCancel, createFn, updateFn }: Props) {
  const toast = useToast();
  const isEditing = branch !== null;

  const submitAction = useCallback(
    async (_prevState: FormState, formData: FormData): Promise<FormState> => {
      const nombre = formData.get('nombre') as string;
      const direccion = (formData.get('direccion') as string) || null;
      const telefono = (formData.get('telefono') as string) || null;
      const email = (formData.get('email') as string) || null;
      const imagen_url = (formData.get('imagen_url') as string) || null;
      const horario_apertura = (formData.get('horario_apertura') as string) || '09:00';
      const horario_cierre = (formData.get('horario_cierre') as string) || '23:00';
      const estado = formData.get('estado') === 'on' ? 'activo' as const : 'inactivo' as const;
      const ordenStr = formData.get('orden') as string;
      const orden = ordenStr ? parseInt(ordenStr, 10) : undefined;

      // Validation
      const errors: Record<string, string> = {};
      if (!nombre || nombre.trim().length < 2) {
        errors.nombre = 'El nombre debe tener al menos 2 caracteres';
      }
      if (nombre && nombre.trim().length > 100) {
        errors.nombre = 'El nombre no puede superar los 100 caracteres';
      }

      if (Object.keys(errors).length > 0) {
        return { isSuccess: false, errors };
      }

      try {
        const data = { nombre, direccion, telefono, email, imagen_url, horario_apertura, horario_cierre, estado, orden };

        if (isEditing && branch) {
          await updateFn(branch.id, data);
        } else {
          await createFn(data);
        }

        onSuccess();
        return { isSuccess: true, errors: {} };
      } catch (err) {
        const message = err instanceof Error ? err.message : 'Error al guardar';
        logger.error('Failed to save branch', err);
        toast.error(message);
        return { isSuccess: false, errors: {}, message };
      }
    },
    [branch, isEditing, createFn, updateFn, onSuccess, toast],
  );

  const [state, formAction, isPending] = useActionState<FormState, FormData>(
    submitAction,
    { isSuccess: false, errors: {} },
  );

  return (
    <form action={formAction}>
      <div className="space-y-4">
        <Input
          name="nombre"
          label="Nombre"
          isRequired
          defaultValue={branch?.nombre ?? ''}
          error={state.errors.nombre}
          placeholder="Nombre de la sucursal"
          disabled={isPending}
        />

        <Input
          name="direccion"
          label="Direccion"
          defaultValue={branch?.direccion ?? ''}
          placeholder="Av. Principal 123"
          disabled={isPending}
        />

        <div className="grid grid-cols-2 gap-4">
          <Input
            name="telefono"
            label="Telefono"
            defaultValue={branch?.telefono ?? ''}
            placeholder="+54 9 261 555-1234"
            disabled={isPending}
          />
          <Input
            name="email"
            label="Email"
            type="email"
            defaultValue={branch?.email ?? ''}
            placeholder="sucursal@email.com"
            disabled={isPending}
          />
        </div>

        <Input
          name="imagen_url"
          label="Imagen URL"
          defaultValue={branch?.imagen_url ?? ''}
          placeholder="https://ejemplo.com/imagen.jpg"
          disabled={isPending}
        />

        <div className="grid grid-cols-2 gap-4">
          <Input
            name="horario_apertura"
            label="Horario apertura"
            type="time"
            defaultValue={branch?.horario_apertura ?? '09:00'}
            disabled={isPending}
          />
          <Input
            name="horario_cierre"
            label="Horario cierre"
            type="time"
            defaultValue={branch?.horario_cierre ?? '23:00'}
            disabled={isPending}
          />
        </div>

        <Input
          name="orden"
          label="Orden"
          type="number"
          defaultValue={branch?.orden?.toString() ?? ''}
          placeholder="0"
          disabled={isPending}
        />

        {/* Native checkbox for formData compat — "on" when checked */}
        <div className="flex items-center gap-3">
          <input
            type="checkbox"
            id="branch-estado"
            name="estado"
            defaultChecked={branch ? branch.estado === 'activo' : true}
            className="h-4 w-4 rounded border-border-default bg-bg-surface text-accent focus:ring-accent"
            disabled={isPending}
          />
          <label htmlFor="branch-estado" className="text-sm text-text-secondary">
            Sucursal activa
          </label>
        </div>
      </div>

      {state.message && !state.isSuccess ? (
        <p className="mt-4 text-sm text-error">{state.message}</p>
      ) : null}

      <div className="mt-6 flex justify-end gap-3">
        <Button type="button" variant="secondary" onClick={onCancel} disabled={isPending}>
          Cancelar
        </Button>
        <Button type="submit" isLoading={isPending}>
          {isEditing ? 'Guardar' : 'Crear sucursal'}
        </Button>
      </div>
    </form>
  );
}
