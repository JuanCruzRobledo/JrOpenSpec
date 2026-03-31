/**
 * SectorForm — create/edit form for sectors.
 * Uses useActionState per React 19 pattern.
 */
import { useActionState, useCallback } from 'react';
import { Input } from '@/components/ui/Input';
import { Select } from '@/components/ui/Select';
import { Button } from '@/components/ui/Button';
import { useToast } from '@/hooks/useToast';
import { logger } from '@/lib/logger';
import type { Sector, SectorCreate, SectorUpdate } from '@/types/sector';

const SECTOR_TYPES = [
  { value: 'interior', label: 'Interior' },
  { value: 'terraza', label: 'Terraza' },
  { value: 'barra', label: 'Barra' },
  { value: 'vip', label: 'VIP' },
];

interface FormState {
  isSuccess: boolean;
  errors: Record<string, string>;
  message?: string;
}

interface Props {
  sector: Sector | null;
  onSuccess: () => void;
  onCancel: () => void;
  createFn: (data: SectorCreate) => Promise<Sector | null>;
  updateFn: (id: number, data: SectorUpdate) => Promise<Sector | null>;
}

export function SectorForm({ sector, onSuccess, onCancel, createFn, updateFn }: Props) {
  const toast = useToast();
  const isEditing = sector !== null;

  const submitAction = useCallback(
    async (_prevState: FormState, formData: FormData): Promise<FormState> => {
      const nombre = formData.get('nombre') as string;
      const tipo = formData.get('tipo') as string;
      const capacidadStr = formData.get('capacidad') as string;
      const capacidad = capacidadStr ? parseInt(capacidadStr, 10) : undefined;

      // Validation
      const errors: Record<string, string> = {};
      if (!nombre || nombre.trim().length < 2) {
        errors.nombre = 'El nombre debe tener al menos 2 caracteres';
      }
      if (!tipo) {
        errors.tipo = 'Selecciona un tipo de sector';
      }
      if (capacidadStr && (isNaN(capacidad!) || capacidad! < 1)) {
        errors.capacidad = 'La capacidad debe ser un numero positivo';
      }

      if (Object.keys(errors).length > 0) {
        return { isSuccess: false, errors };
      }

      try {
        const data = { nombre: nombre.trim(), tipo, capacidad };

        if (isEditing && sector) {
          await updateFn(sector.id, data);
        } else {
          await createFn(data as SectorCreate);
        }

        onSuccess();
        return { isSuccess: true, errors: {} };
      } catch (err) {
        const message = err instanceof Error ? err.message : 'Error al guardar';
        logger.error('Failed to save sector', err);
        toast.error(message);
        return { isSuccess: false, errors: {}, message };
      }
    },
    [sector, isEditing, createFn, updateFn, onSuccess, toast],
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
          defaultValue={sector?.nombre ?? ''}
          error={state.errors.nombre}
          placeholder="Nombre del sector"
          disabled={isPending}
        />

        <Select
          name="tipo"
          label="Tipo"
          isRequired
          options={SECTOR_TYPES}
          placeholder="Seleccionar tipo"
          defaultValue={sector?.tipo ?? ''}
          error={state.errors.tipo}
          disabled={isPending}
        />

        <Input
          name="capacidad"
          label="Capacidad maxima"
          type="number"
          defaultValue={sector?.capacidad?.toString() ?? ''}
          placeholder="Sin limite"
          error={state.errors.capacidad}
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
          {isEditing ? 'Guardar' : 'Crear sector'}
        </Button>
      </div>
    </form>
  );
}
