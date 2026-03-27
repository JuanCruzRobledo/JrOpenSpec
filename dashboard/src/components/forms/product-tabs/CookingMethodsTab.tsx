/**
 * Cooking methods tab — chip multiselect for cooking methods.
 */
import { useState, useEffect, useCallback } from 'react';
import { Button } from '@/components/ui/Button';
import { Spinner } from '@/components/ui/Spinner';
import { useToast } from '@/hooks/useToast';
import { cookingMethodService } from '@/services/cooking-method.service';
import { productExtendedService } from '@/services/product-extended.service';
import { logger } from '@/lib/logger';
import type { CookingMethod } from '@/types/cooking-method';

interface Props {
  productId: number;
}

export function CookingMethodsTab({ productId }: Props) {
  const toast = useToast();
  const [methods, setMethods] = useState<CookingMethod[]>([]);
  const [selectedIds, setSelectedIds] = useState<Set<number>>(new Set());
  const [isLoading, setIsLoading] = useState(true);
  const [isSaving, setIsSaving] = useState(false);

  useEffect(() => {
    let isMounted = true;

    const load = async () => {
      try {
        const res = await cookingMethodService.list({ page: 1, limit: 100 });
        if (!isMounted) return;
        setMethods(res.data);
      } catch (err) {
        logger.error('Failed to load cooking methods', err);
      } finally {
        if (isMounted) setIsLoading(false);
      }
    };

    load();
    return () => { isMounted = false; };
  }, []);

  const handleToggle = useCallback((id: number) => {
    setSelectedIds((prev) => {
      const next = new Set(prev);
      if (next.has(id)) {
        next.delete(id);
      } else {
        next.add(id);
      }
      return next;
    });
  }, []);

  const handleSave = useCallback(async () => {
    setIsSaving(true);
    try {
      await productExtendedService.setCookingMethods(productId, Array.from(selectedIds));
      toast.success('Metodos de coccion actualizados');
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Error al guardar';
      logger.error('Failed to save cooking methods', err);
      toast.error(message);
    } finally {
      setIsSaving(false);
    }
  }, [productId, selectedIds, toast]);

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
        Selecciona los metodos de coccion utilizados en este producto.
      </p>

      <div className="flex flex-wrap gap-3">
        {methods.map((method) => {
          const isSelected = selectedIds.has(method.id);
          return (
            <button
              key={method.id}
              type="button"
              onClick={() => handleToggle(method.id)}
              className={`flex items-center gap-2 rounded-full px-4 py-2 text-sm font-medium border transition-colors ${
                isSelected
                  ? 'bg-accent text-white border-accent'
                  : 'bg-bg-surface text-text-secondary border-border-default hover:border-accent'
              }`}
            >
              {method.icono ? <span>{method.icono}</span> : null}
              {method.nombre}
            </button>
          );
        })}
      </div>

      <div className="flex justify-end pt-4">
        <Button onClick={handleSave} isLoading={isSaving}>
          Guardar metodos
        </Button>
      </div>
    </div>
  );
}
