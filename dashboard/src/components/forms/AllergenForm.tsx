import { useActionState, useCallback } from 'react';
import { Input } from '@/components/ui/Input';
import { Textarea } from '@/components/ui/Textarea';
import { Button } from '@/components/ui/Button';
import { useToast } from '@/hooks/useToast';
import { logger } from '@/lib/logger';
import type { Allergen, AllergenCreate, AllergenUpdate } from '@/types/allergen';

interface FormState {
  isSuccess: boolean;
  errors: Record<string, string>;
  message?: string;
}

interface Props {
  allergen: Allergen | null;
  onSuccess: () => void;
  onCancel: () => void;
  createFn: (data: AllergenCreate) => Promise<Allergen | null>;
  updateFn: (id: number, data: AllergenUpdate) => Promise<Allergen | null>;
}

export function AllergenForm({ allergen, onSuccess, onCancel, createFn, updateFn }: Props) {
  const toast = useToast();
  const isEditing = allergen !== null;
  const isSystem = allergen?.es_sistema ?? false;

  const submitAction = useCallback(
    async (_prevState: FormState, formData: FormData): Promise<FormState> => {
      const nombre = formData.get('nombre') as string;
      const codigo = formData.get('codigo') as string;
      const descripcion = formData.get('descripcion') as string;
      const icono = (formData.get('icono') as string) || null;

      const errors: Record<string, string> = {};
      if (!nombre || nombre.trim().length < 2) {
        errors.nombre = 'El nombre debe tener al menos 2 caracteres';
      }
      if (!isEditing && (!codigo || codigo.trim().length < 2)) {
        errors.codigo = 'El codigo debe tener al menos 2 caracteres';
      }
      if (codigo && !/^[a-z0-9_]+$/.test(codigo)) {
        errors.codigo = 'Solo letras minusculas, numeros y guion bajo';
      }

      if (Object.keys(errors).length > 0) {
        return { isSuccess: false, errors };
      }

      try {
        if (isEditing && allergen) {
          await updateFn(allergen.id, { nombre, descripcion: descripcion || null, icono });
        } else {
          await createFn({ codigo, nombre, descripcion: descripcion || null, icono });
        }
        onSuccess();
        return { isSuccess: true, errors: {} };
      } catch (err) {
        const message = err instanceof Error ? err.message : 'Error al guardar';
        logger.error('Failed to save allergen', err);
        toast.error(message);
        return { isSuccess: false, errors: {}, message };
      }
    },
    [allergen, isEditing, createFn, updateFn, onSuccess, toast],
  );

  const [state, formAction, isPending] = useActionState<FormState, FormData>(
    submitAction,
    { isSuccess: false, errors: {} },
  );

  return (
    <form action={formAction}>
      <div className="space-y-4">
        <Input
          name="codigo"
          label="Codigo"
          isRequired={!isEditing}
          defaultValue={allergen?.codigo ?? ''}
          error={state.errors.codigo}
          placeholder="ej: lactosa, sesamo_aceite"
          disabled={isPending || isEditing}
        />

        <Input
          name="nombre"
          label="Nombre"
          isRequired
          defaultValue={allergen?.nombre ?? ''}
          error={state.errors.nombre}
          placeholder="Nombre del alergeno"
          disabled={isPending || isSystem}
        />

        <Textarea
          name="descripcion"
          label="Descripcion"
          defaultValue={allergen?.descripcion ?? ''}
          error={state.errors.descripcion}
          placeholder="Descripcion del alergeno (opcional)"
          disabled={isPending || isSystem}
        />

        <Input
          name="icono"
          label="Icono"
          defaultValue={allergen?.icono ?? ''}
          placeholder="ej: wheat, milk, egg"
          disabled={isPending || isSystem}
        />

        {isSystem ? (
          <p className="text-xs text-text-tertiary">
            Los alergenos del sistema no pueden ser editados.
          </p>
        ) : null}
      </div>

      {state.message && !state.isSuccess ? (
        <p className="mt-4 text-sm text-error">{state.message}</p>
      ) : null}

      <div className="mt-6 flex justify-end gap-3">
        <Button type="button" variant="secondary" onClick={onCancel} disabled={isPending}>
          Cancelar
        </Button>
        {!isSystem ? (
          <Button type="submit" isLoading={isPending}>
            {isEditing ? 'Guardar' : 'Crear alergeno'}
          </Button>
        ) : null}
      </div>
    </form>
  );
}
