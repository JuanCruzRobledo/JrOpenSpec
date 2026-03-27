/**
 * Branch pricing tab — toggle availability + per-branch price overrides.
 */
import { useState, useEffect, useCallback } from 'react';
import { Input } from '@/components/ui/Input';
import { Button } from '@/components/ui/Button';
import { Spinner } from '@/components/ui/Spinner';
import { Toggle } from '@/components/ui/Toggle';
import { useToast } from '@/hooks/useToast';
import { branchProductService } from '@/services/branch-product.service';
import { formatCurrency } from '@/lib/format';
import { logger } from '@/lib/logger';
import type { BranchProduct, BranchProductInput } from '@/types/product-extended';

interface Props {
  productId: number;
}

interface BranchRow {
  sucursal_id: number;
  sucursal_nombre: string;
  activo: boolean;
  precio_display: string;
  precio_efectivo_centavos: number;
  has_override: boolean;
}

export function BranchPricingTab({ productId }: Props) {
  const toast = useToast();
  const [rows, setRows] = useState<BranchRow[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isSaving, setIsSaving] = useState(false);

  useEffect(() => {
    let isMounted = true;

    const load = async () => {
      try {
        const data = await branchProductService.listByProduct(productId);
        if (!isMounted) return;
        setRows(
          data.map((bp: BranchProduct) => ({
            sucursal_id: bp.sucursal_id,
            sucursal_nombre: bp.sucursal_nombre,
            activo: bp.activo,
            precio_display: bp.precio_centavos !== null ? (bp.precio_centavos / 100).toFixed(2) : '',
            precio_efectivo_centavos: bp.precio_efectivo_centavos,
            has_override: bp.precio_centavos !== null,
          })),
        );
      } catch (err) {
        logger.error('Failed to load branch products', err);
      } finally {
        if (isMounted) setIsLoading(false);
      }
    };

    load();
    return () => { isMounted = false; };
  }, [productId]);

  const handleToggle = useCallback((sucursalId: number) => {
    setRows((prev) =>
      prev.map((r) =>
        r.sucursal_id === sucursalId ? { ...r, activo: !r.activo } : r,
      ),
    );
  }, []);

  const handlePriceChange = useCallback((sucursalId: number, value: string) => {
    setRows((prev) =>
      prev.map((r) =>
        r.sucursal_id === sucursalId
          ? { ...r, precio_display: value, has_override: value.trim().length > 0 }
          : r,
      ),
    );
  }, []);

  const handleSave = useCallback(async () => {
    const data: BranchProductInput[] = rows.map((r) => {
      const pricePesos = parseFloat(r.precio_display);
      return {
        sucursal_id: r.sucursal_id,
        activo: r.activo,
        precio_centavos: r.has_override && !isNaN(pricePesos) ? Math.round(pricePesos * 100) : null,
      };
    });

    setIsSaving(true);
    try {
      await branchProductService.bulkUpdate(productId, data);
      toast.success('Precios por sucursal actualizados');
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Error al guardar';
      logger.error('Failed to save branch products', err);
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

  if (rows.length === 0) {
    return (
      <p className="text-sm text-text-tertiary text-center py-8">
        No hay sucursales configuradas para este producto.
      </p>
    );
  }

  return (
    <div className="space-y-4">
      <p className="text-sm text-text-secondary">
        Configura disponibilidad y precios por sucursal. Deja el precio en blanco para usar el precio base.
      </p>

      <div className="rounded-lg border border-border-default overflow-hidden">
        <table className="w-full text-sm">
          <thead className="bg-bg-surface border-b border-border-default">
            <tr>
              <th className="px-4 py-3 text-left text-xs font-semibold text-text-secondary">Sucursal</th>
              <th className="px-4 py-3 text-center text-xs font-semibold text-text-secondary w-24">Activo</th>
              <th className="px-4 py-3 text-right text-xs font-semibold text-text-secondary w-44">Precio (pesos)</th>
              <th className="px-4 py-3 text-right text-xs font-semibold text-text-secondary w-36">Precio efectivo</th>
            </tr>
          </thead>
          <tbody>
            {rows.map((row) => (
              <tr key={row.sucursal_id} className="border-b border-border-default">
                <td className="px-4 py-3 font-medium">{row.sucursal_nombre}</td>
                <td className="px-4 py-3 text-center">
                  <Toggle
                    checked={row.activo}
                    onChange={() => handleToggle(row.sucursal_id)}
                  />
                </td>
                <td className="px-4 py-3">
                  <Input
                    type="number"
                    step="0.01"
                    min="0"
                    value={row.precio_display}
                    onChange={(e) => handlePriceChange(row.sucursal_id, e.target.value)}
                    placeholder="Precio base"
                    className="text-right"
                  />
                </td>
                <td className="px-4 py-3 text-right text-text-secondary">
                  {row.has_override && row.precio_display ? (
                    <span className="font-medium text-accent">
                      {formatCurrency(Math.round(parseFloat(row.precio_display) * 100))}
                    </span>
                  ) : (
                    <span className="text-text-tertiary">
                      {formatCurrency(row.precio_efectivo_centavos)}
                    </span>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <div className="flex justify-end pt-4">
        <Button onClick={handleSave} isLoading={isSaving}>
          Guardar precios
        </Button>
      </div>
    </div>
  );
}
