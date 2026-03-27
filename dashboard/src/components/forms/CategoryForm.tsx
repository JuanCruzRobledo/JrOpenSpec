import { useActionState, useCallback } from 'react';
import { Input } from '@/components/ui/Input';
import { Button } from '@/components/ui/Button';
import { useToast } from '@/hooks/useToast';
import { logger } from '@/lib/logger';
import type { Category, CategoryCreate, CategoryUpdate } from '@/types/category';

interface FormState {
  isSuccess: boolean;
  errors: Record<string, string>;
  message?: string;
}

interface Props {
  /** Category to edit (null for create mode) */
  category: Category | null;
  onSuccess: () => void;
  onCancel: () => void;
  createFn: (data: CategoryCreate) => Promise<Category | null>;
  updateFn: (id: number, data: CategoryUpdate) => Promise<Category | null>;
}

/**
 * Category create/edit form.
 * Uses useActionState per React 19 pattern.
 */
export function CategoryForm({ category, onSuccess, onCancel, createFn, updateFn }: Props) {
  const toast = useToast();
  const isEditing = category !== null;

  const submitAction = useCallback(
    async (_prevState: FormState, formData: FormData): Promise<FormState> => {
      const nombre = formData.get('nombre') as string;
      const icono = (formData.get('icono') as string) || null;
      const imagen_url = (formData.get('imagen_url') as string) || null;
      const ordenStr = formData.get('orden') as string;
      const orden = ordenStr ? parseInt(ordenStr, 10) : undefined;
      const estado = formData.get('estado') === 'on' ? 'activo' as const : 'inactivo' as const;

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
        const data = { nombre, icono, imagen_url, orden, estado };

        if (isEditing && category) {
          await updateFn(category.id, data);
        } else {
          await createFn(data);
        }

        onSuccess();
        return { isSuccess: true, errors: {} };
      } catch (err) {
        const message = err instanceof Error ? err.message : 'Error al guardar';
        logger.error('Failed to save category', err);
        toast.error(message);
        return { isSuccess: false, errors: {}, message };
      }
    },
    [category, isEditing, createFn, updateFn, onSuccess, toast],
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
          defaultValue={category?.nombre ?? ''}
          error={state.errors.nombre}
          placeholder="Nombre de la categoria"
          disabled={isPending}
        />

        <Input
          name="icono"
          label="Icono (emoji)"
          defaultValue={category?.icono ?? ''}
          placeholder="🍕"
          disabled={isPending}
        />

        <Input
          name="imagen_url"
          label="Imagen URL"
          defaultValue={category?.imagen_url ?? ''}
          placeholder="https://ejemplo.com/imagen.jpg"
          disabled={isPending}
        />

        <Input
          name="orden"
          label="Orden"
          type="number"
          defaultValue={category?.orden?.toString() ?? ''}
          placeholder="Auto-increment"
          disabled={isPending}
        />

        <div className="flex items-center gap-3">
          <input
            type="checkbox"
            id="category-estado"
            name="estado"
            defaultChecked={category ? category.estado === 'activo' : true}
            className="h-4 w-4 rounded border-border-default bg-bg-surface text-accent focus:ring-accent"
            disabled={isPending}
          />
          <label htmlFor="category-estado" className="text-sm text-text-secondary">
            Categoria activa
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
          {isEditing ? 'Guardar' : 'Crear categoria'}
        </Button>
      </div>
    </form>
  );
}
