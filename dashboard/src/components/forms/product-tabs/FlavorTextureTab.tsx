/**
 * Flavor & Texture profiles tab — toggle chips for enum arrays.
 */
import { useState, useCallback } from 'react';
import { Button } from '@/components/ui/Button';
import { useToast } from '@/hooks/useToast';
import { productExtendedService } from '@/services/product-extended.service';
import { logger } from '@/lib/logger';
import type { FlavorProfile, TextureProfile } from '@/types/product-extended';

interface Props {
  productId: number;
}

const FLAVOR_OPTIONS: { value: FlavorProfile; label: string }[] = [
  { value: 'sweet', label: 'Dulce' },
  { value: 'salty', label: 'Salado' },
  { value: 'sour', label: 'Acido' },
  { value: 'bitter', label: 'Amargo' },
  { value: 'umami', label: 'Umami' },
  { value: 'spicy', label: 'Picante' },
];

const TEXTURE_OPTIONS: { value: TextureProfile; label: string }[] = [
  { value: 'crispy', label: 'Crocante' },
  { value: 'creamy', label: 'Cremoso' },
  { value: 'crunchy', label: 'Crujiente' },
  { value: 'soft', label: 'Suave' },
  { value: 'chewy', label: 'Masticable' },
  { value: 'liquid', label: 'Liquido' },
];

export function FlavorTextureTab({ productId }: Props) {
  const toast = useToast();
  const [selectedFlavors, setSelectedFlavors] = useState<Set<FlavorProfile>>(new Set());
  const [selectedTextures, setSelectedTextures] = useState<Set<TextureProfile>>(new Set());
  const [isSaving, setIsSaving] = useState(false);

  const toggleFlavor = useCallback((value: FlavorProfile) => {
    setSelectedFlavors((prev) => {
      const next = new Set(prev);
      if (next.has(value)) {
        next.delete(value);
      } else {
        next.add(value);
      }
      return next;
    });
  }, []);

  const toggleTexture = useCallback((value: TextureProfile) => {
    setSelectedTextures((prev) => {
      const next = new Set(prev);
      if (next.has(value)) {
        next.delete(value);
      } else {
        next.add(value);
      }
      return next;
    });
  }, []);

  const handleSave = useCallback(async () => {
    setIsSaving(true);
    try {
      await Promise.all([
        productExtendedService.setFlavorProfiles(productId, Array.from(selectedFlavors)),
        productExtendedService.setTextureProfiles(productId, Array.from(selectedTextures)),
      ]);
      toast.success('Perfiles de sabor y textura actualizados');
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Error al guardar';
      logger.error('Failed to save flavor/texture profiles', err);
      toast.error(message);
    } finally {
      setIsSaving(false);
    }
  }, [productId, selectedFlavors, selectedTextures, toast]);

  return (
    <div className="space-y-6">
      {/* Flavor section */}
      <div>
        <h3 className="text-sm font-semibold text-text-primary mb-3">Perfiles de Sabor</h3>
        <div className="flex flex-wrap gap-3">
          {FLAVOR_OPTIONS.map((opt) => {
            const isSelected = selectedFlavors.has(opt.value);
            return (
              <button
                key={opt.value}
                type="button"
                onClick={() => toggleFlavor(opt.value)}
                className={`rounded-full px-4 py-2 text-sm font-medium border transition-colors ${
                  isSelected
                    ? 'bg-accent text-white border-accent'
                    : 'bg-bg-surface text-text-secondary border-border-default hover:border-accent'
                }`}
              >
                {opt.label}
              </button>
            );
          })}
        </div>
      </div>

      {/* Texture section */}
      <div>
        <h3 className="text-sm font-semibold text-text-primary mb-3">Perfiles de Textura</h3>
        <div className="flex flex-wrap gap-3">
          {TEXTURE_OPTIONS.map((opt) => {
            const isSelected = selectedTextures.has(opt.value);
            return (
              <button
                key={opt.value}
                type="button"
                onClick={() => toggleTexture(opt.value)}
                className={`rounded-full px-4 py-2 text-sm font-medium border transition-colors ${
                  isSelected
                    ? 'bg-accent text-white border-accent'
                    : 'bg-bg-surface text-text-secondary border-border-default hover:border-accent'
                }`}
              >
                {opt.label}
              </button>
            );
          })}
        </div>
      </div>

      <div className="flex justify-end pt-4">
        <Button onClick={handleSave} isLoading={isSaving}>
          Guardar sabor y textura
        </Button>
      </div>
    </div>
  );
}
