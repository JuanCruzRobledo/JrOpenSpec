/**
 * Badges & Seals tab — selectable cards with visual preview.
 */
import { useState, useEffect, useCallback } from 'react';
import { Button } from '@/components/ui/Button';
import { Spinner } from '@/components/ui/Spinner';
import { useToast } from '@/hooks/useToast';
import { badgeService } from '@/services/badge.service';
import { sealService } from '@/services/seal.service';
import { productExtendedService } from '@/services/product-extended.service';
import { logger } from '@/lib/logger';
import type { Badge } from '@/types/badge';
import type { Seal } from '@/types/seal';

interface Props {
  productId: number;
}

export function BadgesSealsTab({ productId }: Props) {
  const toast = useToast();
  const [badges, setBadges] = useState<Badge[]>([]);
  const [seals, setSeals] = useState<Seal[]>([]);
  const [selectedBadgeIds, setSelectedBadgeIds] = useState<Set<number>>(new Set());
  const [selectedSealIds, setSelectedSealIds] = useState<Set<number>>(new Set());
  const [isLoading, setIsLoading] = useState(true);
  const [isSaving, setIsSaving] = useState(false);

  useEffect(() => {
    let isMounted = true;

    const load = async () => {
      try {
        const [badgeRes, sealRes] = await Promise.all([
          badgeService.list({ page: 1, limit: 100 }),
          sealService.list({ page: 1, limit: 100 }),
        ]);
        if (!isMounted) return;
        setBadges(badgeRes.data);
        setSeals(sealRes.data);
      } catch (err) {
        logger.error('Failed to load badges/seals', err);
      } finally {
        if (isMounted) setIsLoading(false);
      }
    };

    load();
    return () => { isMounted = false; };
  }, []);

  const toggleBadge = useCallback((id: number) => {
    setSelectedBadgeIds((prev) => {
      const next = new Set(prev);
      if (next.has(id)) {
        next.delete(id);
      } else {
        next.add(id);
      }
      return next;
    });
  }, []);

  const toggleSeal = useCallback((id: number) => {
    setSelectedSealIds((prev) => {
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
      const badgeData = Array.from(selectedBadgeIds).map((id, idx) => ({
        badge_id: id,
        orden: idx + 1,
      }));
      const sealData = Array.from(selectedSealIds).map((id, idx) => ({
        seal_id: id,
        orden: idx + 1,
      }));

      await Promise.all([
        productExtendedService.setBadges(productId, badgeData),
        productExtendedService.setSeals(productId, sealData),
      ]);
      toast.success('Badges y sellos actualizados');
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Error al guardar';
      logger.error('Failed to save badges/seals', err);
      toast.error(message);
    } finally {
      setIsSaving(false);
    }
  }, [productId, selectedBadgeIds, selectedSealIds, toast]);

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-12">
        <Spinner size="lg" />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Badges section */}
      <div>
        <h3 className="text-sm font-semibold text-text-primary mb-3">Badges</h3>
        <div className="flex flex-wrap gap-3">
          {badges.map((badge) => {
            const isSelected = selectedBadgeIds.has(badge.id);
            return (
              <button
                key={badge.id}
                type="button"
                onClick={() => toggleBadge(badge.id)}
                className={`flex items-center gap-2 rounded-lg px-4 py-2.5 text-sm font-medium border-2 transition-colors ${
                  isSelected
                    ? 'border-accent bg-accent/10'
                    : 'border-border-default bg-bg-surface hover:border-border-default/80'
                }`}
              >
                <span
                  className="inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-xs font-medium text-white"
                  style={{ backgroundColor: badge.color }}
                >
                  {badge.icono ? <span>{badge.icono}</span> : null}
                  {badge.nombre}
                </span>
              </button>
            );
          })}
        </div>
      </div>

      {/* Seals section */}
      <div>
        <h3 className="text-sm font-semibold text-text-primary mb-3">Sellos</h3>
        <div className="flex flex-wrap gap-3">
          {seals.map((seal) => {
            const isSelected = selectedSealIds.has(seal.id);
            return (
              <button
                key={seal.id}
                type="button"
                onClick={() => toggleSeal(seal.id)}
                className={`flex items-center gap-2 rounded-lg px-4 py-2.5 text-sm font-medium border-2 transition-colors ${
                  isSelected
                    ? 'border-accent bg-accent/10'
                    : 'border-border-default bg-bg-surface hover:border-border-default/80'
                }`}
              >
                <span
                  className="inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-xs font-medium text-white"
                  style={{ backgroundColor: seal.color }}
                >
                  {seal.icono ? <span>{seal.icono}</span> : null}
                  {seal.nombre}
                </span>
              </button>
            );
          })}
        </div>
      </div>

      <div className="flex justify-end pt-4">
        <Button onClick={handleSave} isLoading={isSaving}>
          Guardar badges y sellos
        </Button>
      </div>
    </div>
  );
}
