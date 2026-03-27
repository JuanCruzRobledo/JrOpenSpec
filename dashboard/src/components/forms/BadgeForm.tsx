import { useActionState, useCallback, useState } from 'react';
import { Input } from '@/components/ui/Input';
import { Button } from '@/components/ui/Button';
import { useToast } from '@/hooks/useToast';
import { logger } from '@/lib/logger';
import type { Badge, BadgeCreate, BadgeUpdate } from '@/types/badge';

interface FormState {
  isSuccess: boolean;
  errors: Record<string, string>;
  message?: string;
}

interface Props {
  badge: Badge | null;
  onSuccess: () => void;
  onCancel: () => void;
  createFn: (data: BadgeCreate) => Promise<Badge | null>;
  updateFn: (id: number, data: BadgeUpdate) => Promise<Badge | null>;
}

const HEX_COLOR_REGEX = /^#[0-9A-Fa-f]{6}$/;

export function BadgeForm({ badge, onSuccess, onCancel, createFn, updateFn }: Props) {
  const toast = useToast();
  const isEditing = badge !== null;
  const isSystem = badge?.es_sistema ?? false;
  const [colorPreview, setColorPreview] = useState(badge?.color ?? '#f97316');

  const submitAction = useCallback(
    async (_prevState: FormState, formData: FormData): Promise<FormState> => {
      const nombre = formData.get('nombre') as string;
      const codigo = formData.get('codigo') as string;
      const color = formData.get('color') as string;
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
      if (!color || !HEX_COLOR_REGEX.test(color)) {
        errors.color = 'Ingresa un color hex valido (ej: #FF5500)';
      }

      if (Object.keys(errors).length > 0) {
        return { isSuccess: false, errors };
      }

      try {
        if (isEditing && badge) {
          await updateFn(badge.id, { nombre, color, icono });
        } else {
          await createFn({ codigo, nombre, color, icono });
        }
        onSuccess();
        return { isSuccess: true, errors: {} };
      } catch (err) {
        const message = err instanceof Error ? err.message : 'Error al guardar';
        logger.error('Failed to save badge', err);
        toast.error(message);
        return { isSuccess: false, errors: {}, message };
      }
    },
    [badge, isEditing, createFn, updateFn, onSuccess, toast],
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
          defaultValue={badge?.codigo ?? ''}
          error={state.errors.codigo}
          placeholder="ej: nuevo, oferta"
          disabled={isPending || isEditing}
        />

        <Input
          name="nombre"
          label="Nombre"
          isRequired
          defaultValue={badge?.nombre ?? ''}
          error={state.errors.nombre}
          placeholder="Nombre del badge"
          disabled={isPending || isSystem}
        />

        <div className="flex items-end gap-3">
          <div className="flex-1">
            <Input
              name="color"
              label="Color (hex)"
              isRequired
              defaultValue={badge?.color ?? '#f97316'}
              error={state.errors.color}
              placeholder="#FF5500"
              disabled={isPending || isSystem}
              onChange={(e) => {
                if (HEX_COLOR_REGEX.test(e.target.value)) {
                  setColorPreview(e.target.value);
                }
              }}
            />
          </div>
          <div
            className="h-10 w-10 rounded-lg border border-border-default shrink-0"
            style={{ backgroundColor: colorPreview }}
            title={colorPreview}
          />
        </div>

        <Input
          name="icono"
          label="Icono"
          defaultValue={badge?.icono ?? ''}
          placeholder="ej: star, fire"
          disabled={isPending || isSystem}
        />

        {/* Live preview */}
        <div className="pt-2">
          <p className="text-xs text-text-tertiary mb-2">Vista previa:</p>
          <span
            className="inline-flex items-center gap-1 rounded-full px-3 py-1 text-xs font-medium text-white"
            style={{ backgroundColor: colorPreview }}
          >
            {badge?.nombre ?? 'Nombre del badge'}
          </span>
        </div>

        {isSystem ? (
          <p className="text-xs text-text-tertiary">
            Los badges del sistema no pueden ser editados.
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
            {isEditing ? 'Guardar' : 'Crear badge'}
          </Button>
        ) : null}
      </div>
    </form>
  );
}
