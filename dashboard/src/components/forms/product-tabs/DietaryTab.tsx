/**
 * Dietary profiles tab — checkbox list to assign dietary profiles to a product.
 */
import { useState, useEffect, useCallback } from 'react';
import { Button } from '@/components/ui/Button';
import { Spinner } from '@/components/ui/Spinner';
import { useToast } from '@/hooks/useToast';
import { dietaryProfileService } from '@/services/dietary-profile.service';
import { productExtendedService } from '@/services/product-extended.service';
import { logger } from '@/lib/logger';
import type { DietaryProfile } from '@/types/dietary-profile';

interface Props {
  productId: number;
}

export function DietaryTab({ productId }: Props) {
  const toast = useToast();
  const [profiles, setProfiles] = useState<DietaryProfile[]>([]);
  const [selectedIds, setSelectedIds] = useState<Set<number>>(new Set());
  const [isLoading, setIsLoading] = useState(true);
  const [isSaving, setIsSaving] = useState(false);

  useEffect(() => {
    let isMounted = true;

    const load = async () => {
      try {
        const res = await dietaryProfileService.list({ page: 1, limit: 100 });
        if (!isMounted) return;
        setProfiles(res.data);
      } catch (err) {
        logger.error('Failed to load dietary profiles', err);
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
      await productExtendedService.setDietaryProfiles(productId, Array.from(selectedIds));
      toast.success('Perfiles dieteticos actualizados');
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Error al guardar';
      logger.error('Failed to save dietary profiles', err);
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
        Selecciona los perfiles dieteticos que aplican a este producto.
      </p>

      <div className="flex flex-wrap gap-3">
        {profiles.map((profile) => {
          const isSelected = selectedIds.has(profile.id);
          return (
            <button
              key={profile.id}
              type="button"
              onClick={() => handleToggle(profile.id)}
              className={`flex items-center gap-2 rounded-full px-4 py-2 text-sm font-medium border transition-colors ${
                isSelected
                  ? 'bg-accent text-white border-accent'
                  : 'bg-bg-surface text-text-secondary border-border-default hover:border-accent'
              }`}
            >
              {profile.icono ? <span>{profile.icono}</span> : null}
              {profile.nombre}
            </button>
          );
        })}
      </div>

      <div className="flex justify-end pt-4">
        <Button onClick={handleSave} isLoading={isSaving}>
          Guardar perfiles
        </Button>
      </div>
    </div>
  );
}
