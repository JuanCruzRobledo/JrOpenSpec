/**
 * Allergens tab — assign allergens to a product with presence type and risk level.
 */
import { useState, useEffect, useCallback } from 'react';
import { Button } from '@/components/ui/Button';
import { Select } from '@/components/ui/Select';
import { Spinner } from '@/components/ui/Spinner';
import { useToast } from '@/hooks/useToast';
import { allergenService } from '@/services/allergen.service';
import { productExtendedService } from '@/services/product-extended.service';
import { logger } from '@/lib/logger';
import type { Allergen, PresenceType, AllergenSeverity } from '@/types/allergen';
import type { ProductAllergenData } from '@/types/product-extended';

interface Props {
  productId: number;
}

interface AllergenRow {
  alergeno_id: number;
  selected: boolean;
  tipo_presencia: PresenceType;
  nivel_riesgo: AllergenSeverity;
  notas: string;
}

const PRESENCE_OPTIONS = [
  { value: 'contains', label: 'Contiene' },
  { value: 'may_contain', label: 'Puede contener' },
  { value: 'free_of', label: 'Libre de' },
];

const RISK_OPTIONS = [
  { value: 'low', label: 'Bajo' },
  { value: 'moderate', label: 'Moderado' },
  { value: 'severe', label: 'Severo' },
  { value: 'life_threatening', label: 'Peligro de vida' },
];

export function AllergensTab({ productId }: Props) {
  const toast = useToast();
  const [allergens, setAllergens] = useState<Allergen[]>([]);
  const [rows, setRows] = useState<AllergenRow[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isSaving, setIsSaving] = useState(false);

  useEffect(() => {
    let isMounted = true;

    const load = async () => {
      try {
        const res = await allergenService.list({ page: 1, limit: 100 });
        if (!isMounted) return;
        setAllergens(res.data);
        // Initialize rows — all unselected by default
        setRows(
          res.data.map((a) => ({
            alergeno_id: a.id,
            selected: false,
            tipo_presencia: 'contains' as PresenceType,
            nivel_riesgo: 'moderate' as AllergenSeverity,
            notas: '',
          })),
        );
      } catch (err) {
        logger.error('Failed to load allergens', err);
      } finally {
        if (isMounted) setIsLoading(false);
      }
    };

    load();
    return () => { isMounted = false; };
  }, []);

  const handleToggle = useCallback((allergenId: number) => {
    setRows((prev) =>
      prev.map((r) =>
        r.alergeno_id === allergenId ? { ...r, selected: !r.selected } : r,
      ),
    );
  }, []);

  const handlePresenceChange = useCallback((allergenId: number, value: string) => {
    setRows((prev) =>
      prev.map((r) => {
        if (r.alergeno_id !== allergenId) return r;
        const tipo_presencia = value as PresenceType;
        // Auto-set risk to low for free_of
        const nivel_riesgo = tipo_presencia === 'free_of' ? 'low' as AllergenSeverity : r.nivel_riesgo;
        return { ...r, tipo_presencia, nivel_riesgo };
      }),
    );
  }, []);

  const handleRiskChange = useCallback((allergenId: number, value: string) => {
    setRows((prev) =>
      prev.map((r) =>
        r.alergeno_id === allergenId ? { ...r, nivel_riesgo: value as AllergenSeverity } : r,
      ),
    );
  }, []);

  const handleSave = useCallback(async () => {
    const selectedRows = rows.filter((r) => r.selected);
    const data: ProductAllergenData[] = selectedRows.map((r) => ({
      alergeno_id: r.alergeno_id,
      tipo_presencia: r.tipo_presencia,
      nivel_riesgo: r.nivel_riesgo,
      notas: r.notas || null,
    }));

    setIsSaving(true);
    try {
      await productExtendedService.setAllergens(productId, data);
      toast.success('Alergenos actualizados');
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Error al guardar alergenos';
      logger.error('Failed to save product allergens', err);
      toast.error(message);
    } finally {
      setIsSaving(false);
    }
  }, [productId, rows, toast]);

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-12">
        <Spinner size="lg" />
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <p className="text-sm text-text-secondary">
        Selecciona los alergenos presentes en este producto y configura el tipo de presencia y nivel de riesgo.
      </p>

      <div className="space-y-2 max-h-96 overflow-y-auto">
        {allergens.map((allergen) => {
          const row = rows.find((r) => r.alergeno_id === allergen.id);
          if (!row) return null;

          return (
            <div
              key={allergen.id}
              className="rounded-lg border border-border-default p-3 space-y-2"
            >
              <div className="flex items-center gap-3">
                <input
                  type="checkbox"
                  checked={row.selected}
                  onChange={() => handleToggle(allergen.id)}
                  className="h-4 w-4 rounded border-border-default bg-bg-surface text-accent focus:ring-accent"
                />
                <span className="text-sm font-medium">
                  {allergen.icono ? `${allergen.icono} ` : ''}{allergen.nombre}
                </span>
                <span className="text-xs text-text-tertiary font-mono">{allergen.codigo}</span>
              </div>

              {row.selected ? (
                <div className="ml-7 flex flex-wrap gap-3">
                  <div className="w-40">
                    <Select
                      label="Presencia"
                      options={PRESENCE_OPTIONS}
                      value={row.tipo_presencia}
                      onChange={(e) => handlePresenceChange(allergen.id, e.target.value)}
                    />
                  </div>
                  <div className="w-40">
                    <Select
                      label="Riesgo"
                      options={RISK_OPTIONS}
                      value={row.nivel_riesgo}
                      onChange={(e) => handleRiskChange(allergen.id, e.target.value)}
                      disabled={row.tipo_presencia === 'free_of'}
                    />
                  </div>
                </div>
              ) : null}
            </div>
          );
        })}
      </div>

      <div className="flex justify-end pt-4">
        <Button onClick={handleSave} isLoading={isSaving}>
          Guardar alergenos
        </Button>
      </div>
    </div>
  );
}
