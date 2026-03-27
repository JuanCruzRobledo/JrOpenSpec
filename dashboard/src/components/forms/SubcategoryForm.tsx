import { useActionState, useCallback } from 'react';
import { Input } from '@/components/ui/Input';
import { Select } from '@/components/ui/Select';
import { Button } from '@/components/ui/Button';
import { useToast } from '@/hooks/useToast';
import { logger } from '@/lib/logger';
import type { Category } from '@/types/category';
import type { Subcategory, SubcategoryCreate, SubcategoryUpdate } from '@/types/subcategory';

interface FormState {
  isSuccess: boolean;
  errors: Record<string, string>;
  message?: string;
}

interface Props {
  /** Subcategory to edit (null for create mode) */
  subcategory: Subcategory | null;
  /** Available categories for the dropdown */
  categories: Category[];
  onSuccess: () => void;
  onCancel: () => void;
  createFn: (data: SubcategoryCreate) => Promise<Subcategory | null>;
  updateFn: (id: number, data: SubcategoryUpdate) => Promise<Subcategory | null>;
}

/**
 * Subcategory create/edit form.
 * Uses useActionState per React 19 pattern.
 */
export function SubcategoryForm({
  subcategory,
  categories,
  onSuccess,
  onCancel,
  createFn,
  updateFn,
}: Props) {
  const toast = useToast();
  const isEditing = subcategory !== null;

  const categoryOptions = categories
    .filter((c) => !c.es_home)
    .map((c) => ({ value: c.id, label: c.nombre }));

  const submitAction = useCallback(
    async (_prevState: FormState, formData: FormData): Promise<FormState> => {
      const nombre = formData.get('nombre') as string;
      const categoria_id_str = formData.get('categoria_id') as string;
      const categoria_id = categoria_id_str ? parseInt(categoria_id_str, 10) : 0;
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
      if (!categoria_id) {
        errors.categoria_id = 'Selecciona una categoria';
      }

      if (Object.keys(errors).length > 0) {
        return { isSuccess: false, errors };
      }

      try {
        const data = { nombre, categoria_id, imagen_url, orden, estado };

        if (isEditing && subcategory) {
          await updateFn(subcategory.id, data);
        } else {
          await createFn(data);
        }

        onSuccess();
        return { isSuccess: true, errors: {} };
      } catch (err) {
        const message = err instanceof Error ? err.message : 'Error al guardar';
        logger.error('Failed to save subcategory', err);
        toast.error(message);
        return { isSuccess: false, errors: {}, message };
      }
    },
    [subcategory, isEditing, createFn, updateFn, onSuccess, toast],
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
          defaultValue={subcategory?.nombre ?? ''}
          error={state.errors.nombre}
          placeholder="Nombre de la subcategoria"
          disabled={isPending}
        />

        <Select
          name="categoria_id"
          label="Categoria"
          isRequired
          options={categoryOptions}
          placeholder="Seleccionar categoria"
          defaultValue={subcategory?.categoria_id?.toString() ?? ''}
          error={state.errors.categoria_id}
          disabled={isPending}
        />

        <Input
          name="imagen_url"
          label="Imagen URL"
          defaultValue={subcategory?.imagen_url ?? ''}
          placeholder="https://ejemplo.com/imagen.jpg"
          disabled={isPending}
        />

        <Input
          name="orden"
          label="Orden"
          type="number"
          defaultValue={subcategory?.orden?.toString() ?? ''}
          placeholder="Auto-increment"
          disabled={isPending}
        />

        <div className="flex items-center gap-3">
          <input
            type="checkbox"
            id="subcategory-estado"
            name="estado"
            defaultChecked={subcategory ? subcategory.estado === 'activo' : true}
            className="h-4 w-4 rounded border-border-default bg-bg-surface text-accent focus:ring-accent"
            disabled={isPending}
          />
          <label htmlFor="subcategory-estado" className="text-sm text-text-secondary">
            Subcategoria activa
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
          {isEditing ? 'Guardar' : 'Crear subcategoria'}
        </Button>
      </div>
    </form>
  );
}
