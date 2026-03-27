/**
 * Batch price update modal — 3-step flow: configure -> preview -> apply.
 * Accessible from ProductsPage via "Actualizar Precios" button.
 */
import { useState, useCallback } from 'react';
import { Modal } from '@/components/ui/Modal';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';
import { Select } from '@/components/ui/Select';
import { useToast } from '@/hooks/useToast';
import { useBranch } from '@/hooks/useBranch';
import { batchPriceService } from '@/services/batch-price.service';
import { formatCurrency } from '@/lib/format';
import { logger } from '@/lib/logger';
import type { BatchPriceOperation, BatchPriceRequest, BatchPricePreview, BatchPriceChange } from '@/types/product-extended';

type Step = 'configure' | 'preview' | 'apply';

interface Props {
  isOpen: boolean;
  onClose: () => void;
  selectedProductIds: number[];
  onSuccess: () => void;
}

const OPERATION_OPTIONS = [
  { value: 'fixed_add', label: 'Aumentar monto fijo ($)' },
  { value: 'fixed_subtract', label: 'Disminuir monto fijo ($)' },
  { value: 'percentage_increase', label: 'Aumentar porcentaje (%)' },
  { value: 'percentage_decrease', label: 'Disminuir porcentaje (%)' },
];

export function BatchPriceModal({ isOpen, onClose, selectedProductIds, onSuccess }: Props) {
  const toast = useToast();
  const { branches } = useBranch();

  const [step, setStep] = useState<Step>('configure');
  const [operation, setOperation] = useState<BatchPriceOperation>('percentage_increase');
  const [amount, setAmount] = useState('');
  const [branchId, setBranchId] = useState<number | null>(null);
  const [preview, setPreview] = useState<BatchPricePreview | null>(null);
  const [isLoading, setIsLoading] = useState(false);

  const branchOptions = [
    { value: 0, label: 'Todas las sucursales' },
    ...branches.map((b) => ({ value: b.id, label: b.nombre })),
  ];

  const buildRequest = useCallback((): BatchPriceRequest | null => {
    const parsedAmount = parseFloat(amount);
    if (isNaN(parsedAmount) || parsedAmount <= 0) {
      toast.error('Ingresa un monto valido mayor a cero');
      return null;
    }

    // For fixed operations, convert pesos input to cents
    const isFixed = operation === 'fixed_add' || operation === 'fixed_subtract';
    const finalAmount = isFixed ? Math.round(parsedAmount * 100) : parsedAmount;

    return {
      producto_ids: selectedProductIds,
      operacion: operation,
      monto: finalAmount,
      sucursal_id: branchId,
    };
  }, [amount, operation, branchId, selectedProductIds, toast]);

  const handlePreview = useCallback(async () => {
    const request = buildRequest();
    if (!request) return;

    setIsLoading(true);
    try {
      const result = await batchPriceService.preview(request);
      setPreview(result);
      setStep('preview');
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Error al generar vista previa';
      logger.error('Batch price preview failed', err);
      toast.error(message);
    } finally {
      setIsLoading(false);
    }
  }, [buildRequest, toast]);

  const handleApply = useCallback(async () => {
    const request = buildRequest();
    if (!request) return;

    setIsLoading(true);
    try {
      const result = await batchPriceService.apply(request);
      toast.success(`Se actualizaron ${result.aplicados} precios exitosamente`);
      onSuccess();
      handleReset();
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Error al aplicar cambios';
      logger.error('Batch price apply failed', err);
      toast.error(message);
    } finally {
      setIsLoading(false);
    }
  }, [buildRequest, toast, onSuccess]);

  const handleReset = useCallback(() => {
    setStep('configure');
    setOperation('percentage_increase');
    setAmount('');
    setBranchId(null);
    setPreview(null);
    setIsLoading(false);
    onClose();
  }, [onClose]);

  const isFixed = operation === 'fixed_add' || operation === 'fixed_subtract';

  return (
    <Modal isOpen={isOpen} onClose={handleReset} title="Actualizar Precios en Lote">
      {step === 'configure' ? (
        <div className="space-y-4">
          <p className="text-sm text-text-secondary">
            {selectedProductIds.length} producto(s) seleccionado(s)
          </p>

          <Select
            label="Operacion"
            isRequired
            options={OPERATION_OPTIONS}
            value={operation}
            onChange={(e) => setOperation(e.target.value as BatchPriceOperation)}
          />

          <Input
            label={isFixed ? 'Monto (en pesos)' : 'Porcentaje (%)'}
            isRequired
            type="number"
            step={isFixed ? '0.01' : '0.01'}
            min="0"
            value={amount}
            onChange={(e) => setAmount(e.target.value)}
            placeholder={isFixed ? '250.00' : '10.5'}
          />

          <Select
            label="Sucursal destino"
            options={branchOptions}
            value={branchId?.toString() ?? '0'}
            onChange={(e) => {
              const val = parseInt(e.target.value, 10);
              setBranchId(val === 0 ? null : val);
            }}
          />

          <div className="flex justify-end gap-3 pt-4">
            <Button variant="secondary" onClick={handleReset}>
              Cancelar
            </Button>
            <Button onClick={handlePreview} isLoading={isLoading}>
              Ver vista previa
            </Button>
          </div>
        </div>
      ) : null}

      {step === 'preview' && preview ? (
        <div className="space-y-4">
          <p className="text-sm text-text-secondary">
            {preview.total_cambios} cambio(s) en {preview.total_productos} producto(s) y{' '}
            {preview.total_sucursales} sucursal(es)
          </p>

          <div className="max-h-80 overflow-y-auto rounded-lg border border-border-default">
            <table className="w-full text-sm">
              <thead className="sticky top-0 bg-bg-surface border-b border-border-default">
                <tr>
                  <th className="px-3 py-2 text-left text-xs font-semibold text-text-secondary">Producto</th>
                  <th className="px-3 py-2 text-left text-xs font-semibold text-text-secondary">Sucursal</th>
                  <th className="px-3 py-2 text-right text-xs font-semibold text-text-secondary">Precio actual</th>
                  <th className="px-3 py-2 text-right text-xs font-semibold text-text-secondary">Precio nuevo</th>
                  <th className="px-3 py-2 text-right text-xs font-semibold text-text-secondary">Diferencia</th>
                </tr>
              </thead>
              <tbody>
                {preview.cambios.map((change: BatchPriceChange, idx: number) => {
                  const diff = change.precio_nuevo_centavos - change.precio_anterior_centavos;
                  const isIncrease = diff > 0;
                  return (
                    <tr key={`${change.producto_id}-${change.sucursal_id}-${idx}`} className="border-b border-border-default">
                      <td className="px-3 py-2 font-medium">{change.producto_nombre}</td>
                      <td className="px-3 py-2 text-text-secondary">{change.sucursal_nombre}</td>
                      <td className="px-3 py-2 text-right">{formatCurrency(change.precio_anterior_centavos)}</td>
                      <td className="px-3 py-2 text-right font-medium">{formatCurrency(change.precio_nuevo_centavos)}</td>
                      <td className={`px-3 py-2 text-right font-medium ${isIncrease ? 'text-green-500' : 'text-red-500'}`}>
                        {isIncrease ? '+' : ''}{formatCurrency(diff)}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>

          <div className="flex justify-end gap-3 pt-4">
            <Button variant="secondary" onClick={() => setStep('configure')}>
              Volver
            </Button>
            <Button onClick={handleApply} isLoading={isLoading}>
              Confirmar y aplicar
            </Button>
          </div>
        </div>
      ) : null}
    </Modal>
  );
}
