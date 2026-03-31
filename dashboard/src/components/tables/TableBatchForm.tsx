/**
 * TableBatchForm — form for batch table creation.
 * Uses useActionState per React 19 pattern.
 */
import { useActionState, useCallback, useMemo } from 'react';
import { Input } from '@/components/ui/Input';
import { Select } from '@/components/ui/Select';
import { Button } from '@/components/ui/Button';
import { useToast } from '@/hooks/useToast';
import { logger } from '@/lib/logger';
import type { Sector } from '@/types/sector';
import type { TableBatchCreate, Table } from '@/types/table';

interface FormState {
  isSuccess: boolean;
  errors: Record<string, string>;
  message?: string;
  preview: string[];
}

interface Props {
  sectors: Sector[];
  onSuccess: () => void;
  onCancel: () => void;
  createBatchFn: (data: TableBatchCreate) => Promise<Table[]>;
}

export function TableBatchForm({ sectors, onSuccess, onCancel, createBatchFn }: Props) {
  const toast = useToast();

  const sectorOptions = useMemo(
    () => sectors.map((s) => ({ value: s.id, label: `${s.nombre} (${s.prefijo})` })),
    [sectors],
  );

  const submitAction = useCallback(
    async (_prevState: FormState, formData: FormData): Promise<FormState> => {
      const sectorIdStr = formData.get('sector_id') as string;
      const cantidadStr = formData.get('cantidad') as string;
      const capacidadStr = formData.get('capacidad_base') as string;
      const numeroInicioStr = formData.get('numero_inicio') as string;

      // Validation
      const errors: Record<string, string> = {};

      if (!sectorIdStr) {
        errors.sector_id = 'Selecciona un sector';
      }

      const cantidad = parseInt(cantidadStr, 10);
      if (isNaN(cantidad) || cantidad < 1 || cantidad > 50) {
        errors.cantidad = 'Cantidad debe ser entre 1 y 50';
      }

      const capacidad = parseInt(capacidadStr, 10);
      if (isNaN(capacidad) || capacidad < 1 || capacidad > 20) {
        errors.capacidad_base = 'Capacidad debe ser entre 1 y 20';
      }

      const numeroInicio = numeroInicioStr ? parseInt(numeroInicioStr, 10) : undefined;
      if (numeroInicioStr && (isNaN(numeroInicio!) || numeroInicio! < 1)) {
        errors.numero_inicio = 'Numero inicio debe ser mayor a 0';
      }

      if (Object.keys(errors).length > 0) {
        return { isSuccess: false, errors, preview: [] };
      }

      try {
        const data: TableBatchCreate = {
          sector_id: parseInt(sectorIdStr, 10),
          cantidad,
          capacidad_base: capacidad,
          numero_inicio: numeroInicio,
        };

        await createBatchFn(data);
        toast.success(`${cantidad} mesas creadas exitosamente`);
        onSuccess();
        return { isSuccess: true, errors: {}, preview: [] };
      } catch (err) {
        const message = err instanceof Error ? err.message : 'Error al crear mesas';
        logger.error('Failed to batch create tables', err);
        toast.error(message);
        return { isSuccess: false, errors: {}, message, preview: [] };
      }
    },
    [createBatchFn, onSuccess, toast],
  );

  const [state, formAction, isPending] = useActionState<FormState, FormData>(
    submitAction,
    { isSuccess: false, errors: {}, preview: [] },
  );

  return (
    <form action={formAction}>
      <div className="space-y-4">
        <Select
          name="sector_id"
          label="Sector"
          isRequired
          options={sectorOptions}
          placeholder="Seleccionar sector"
          error={state.errors.sector_id}
          disabled={isPending}
        />

        <Input
          name="cantidad"
          label="Cantidad de mesas"
          type="number"
          isRequired
          placeholder="Ej: 10"
          min={1}
          max={50}
          error={state.errors.cantidad}
          disabled={isPending}
        />

        <Input
          name="capacidad_base"
          label="Capacidad por mesa"
          type="number"
          isRequired
          placeholder="Ej: 4"
          min={1}
          max={20}
          error={state.errors.capacidad_base}
          disabled={isPending}
        />

        <Input
          name="numero_inicio"
          label="Numero inicio (opcional)"
          type="number"
          placeholder="Auto"
          min={1}
          error={state.errors.numero_inicio}
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
          Crear mesas
        </Button>
      </div>
    </form>
  );
}
