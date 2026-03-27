/**
 * Ingredients tab — sortable list with add/remove for product ingredients.
 */
import { useState, useCallback } from 'react';
import { Input } from '@/components/ui/Input';
import { Select } from '@/components/ui/Select';
import { Button } from '@/components/ui/Button';
import { useToast } from '@/hooks/useToast';
import { productExtendedService } from '@/services/product-extended.service';
import { logger } from '@/lib/logger';
import type { IngredientUnit, ProductIngredientData } from '@/types/product-extended';

interface Props {
  productId: number;
}

interface IngredientRow {
  nombre: string;
  cantidad: string;
  unidad: IngredientUnit;
  es_opcional: boolean;
  notas: string;
}

const UNIT_OPTIONS: { value: IngredientUnit; label: string }[] = [
  { value: 'g', label: 'g' },
  { value: 'kg', label: 'kg' },
  { value: 'ml', label: 'ml' },
  { value: 'l', label: 'l' },
  { value: 'unit', label: 'unidad' },
  { value: 'tbsp', label: 'cda' },
  { value: 'tsp', label: 'cdta' },
  { value: 'cup', label: 'taza' },
  { value: 'oz', label: 'oz' },
  { value: 'lb', label: 'lb' },
  { value: 'pinch', label: 'pizca' },
];

const EMPTY_ROW: IngredientRow = {
  nombre: '',
  cantidad: '',
  unidad: 'g',
  es_opcional: false,
  notas: '',
};

export function IngredientsTab({ productId }: Props) {
  const toast = useToast();
  const [rows, setRows] = useState<IngredientRow[]>([{ ...EMPTY_ROW }]);
  const [isSaving, setIsSaving] = useState(false);

  const handleAddRow = useCallback(() => {
    setRows((prev) => [...prev, { ...EMPTY_ROW }]);
  }, []);

  const handleRemoveRow = useCallback((index: number) => {
    setRows((prev) => prev.filter((_, i) => i !== index));
  }, []);

  const handleMoveUp = useCallback((index: number) => {
    if (index === 0) return;
    setRows((prev) => {
      const next = [...prev];
      const temp = next[index - 1]!;
      next[index - 1] = next[index]!;
      next[index] = temp;
      return next;
    });
  }, []);

  const handleMoveDown = useCallback((index: number) => {
    setRows((prev) => {
      if (index >= prev.length - 1) return prev;
      const next = [...prev];
      const temp = next[index + 1]!;
      next[index + 1] = next[index]!;
      next[index] = temp;
      return next;
    });
  }, []);

  const handleFieldChange = useCallback(
    (index: number, field: keyof IngredientRow, value: string | boolean) => {
      setRows((prev) =>
        prev.map((row, i) =>
          i === index ? { ...row, [field]: value } : row,
        ),
      );
    },
    [],
  );

  const handleSave = useCallback(async () => {
    // Filter out empty rows
    const validRows = rows.filter((r) => r.nombre.trim().length > 0);

    if (validRows.length === 0) {
      // Clear all ingredients
      setIsSaving(true);
      try {
        await productExtendedService.setIngredients(productId, []);
        toast.success('Ingredientes actualizados');
      } catch (err) {
        const message = err instanceof Error ? err.message : 'Error al guardar';
        logger.error('Failed to save ingredients', err);
        toast.error(message);
      } finally {
        setIsSaving(false);
      }
      return;
    }

    // Validate
    for (let i = 0; i < validRows.length; i++) {
      const r = validRows[i]!;
      const qty = parseFloat(r.cantidad);
      if (isNaN(qty) || qty <= 0) {
        toast.error(`Ingrediente "${r.nombre}": la cantidad debe ser mayor a cero`);
        return;
      }
    }

    const data: ProductIngredientData[] = validRows.map((r, idx) => ({
      nombre: r.nombre.trim(),
      cantidad: parseFloat(r.cantidad),
      unidad: r.unidad,
      orden: idx + 1,
      es_opcional: r.es_opcional,
      notas: r.notas || null,
    }));

    setIsSaving(true);
    try {
      await productExtendedService.setIngredients(productId, data);
      toast.success('Ingredientes actualizados');
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Error al guardar';
      logger.error('Failed to save ingredients', err);
      toast.error(message);
    } finally {
      setIsSaving(false);
    }
  }, [productId, rows, toast]);

  return (
    <div className="space-y-4">
      <p className="text-sm text-text-secondary">
        Agrega los ingredientes del producto. Usa las flechas para reordenar.
      </p>

      <div className="space-y-3">
        {rows.map((row, index) => (
          <div
            key={index}
            className="rounded-lg border border-border-default p-3 space-y-2"
          >
            <div className="flex items-center gap-2">
              <span className="text-xs text-text-tertiary font-mono w-6">{index + 1}.</span>
              <div className="flex-1">
                <Input
                  placeholder="Nombre del ingrediente"
                  value={row.nombre}
                  onChange={(e) => handleFieldChange(index, 'nombre', e.target.value)}
                />
              </div>
              <div className="w-24">
                <Input
                  type="number"
                  step="0.001"
                  min="0"
                  placeholder="Cant."
                  value={row.cantidad}
                  onChange={(e) => handleFieldChange(index, 'cantidad', e.target.value)}
                />
              </div>
              <div className="w-24">
                <Select
                  options={UNIT_OPTIONS}
                  value={row.unidad}
                  onChange={(e) => handleFieldChange(index, 'unidad', e.target.value)}
                />
              </div>
            </div>

            <div className="flex items-center gap-3 ml-8">
              <div className="flex items-center gap-2">
                <input
                  type="checkbox"
                  checked={row.es_opcional}
                  onChange={(e) => handleFieldChange(index, 'es_opcional', e.target.checked)}
                  className="h-4 w-4 rounded border-border-default bg-bg-surface text-accent focus:ring-accent"
                />
                <span className="text-xs text-text-secondary">Opcional</span>
              </div>

              <div className="flex-1" />

              <div className="flex items-center gap-1">
                <Button
                  size="sm"
                  variant="ghost"
                  onClick={() => handleMoveUp(index)}
                  disabled={index === 0}
                >
                  ↑
                </Button>
                <Button
                  size="sm"
                  variant="ghost"
                  onClick={() => handleMoveDown(index)}
                  disabled={index === rows.length - 1}
                >
                  ↓
                </Button>
                <Button
                  size="sm"
                  variant="danger"
                  onClick={() => handleRemoveRow(index)}
                >
                  ✕
                </Button>
              </div>
            </div>
          </div>
        ))}
      </div>

      <Button variant="secondary" onClick={handleAddRow}>
        + Agregar ingrediente
      </Button>

      <div className="flex justify-end pt-4">
        <Button onClick={handleSave} isLoading={isSaving}>
          Guardar ingredientes
        </Button>
      </div>
    </div>
  );
}
