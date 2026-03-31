/**
 * TableStatusModal — shows table details and valid state transition buttons.
 * Presentational: receives table data and callbacks as props.
 */
import { useState } from 'react';
import { Modal } from '@/components/ui/Modal';
import { Button } from '@/components/ui/Button';
import { cn } from '@/lib/cn';
import type { Table, TableStatus } from '@/types/table';

/** Valid FSM transitions for table status. */
const TABLE_TRANSITIONS: Record<TableStatus, TableStatus[]> = {
  libre:             ['ocupada', 'inactiva'],
  ocupada:           ['pedido_solicitado', 'libre'],
  pedido_solicitado: ['pedido_cumplido', 'libre'],
  pedido_cumplido:   ['cuenta', 'pedido_solicitado'],
  cuenta:            ['libre'],
  inactiva:          ['libre'],
};

const STATUS_LABELS: Record<TableStatus, string> = {
  libre:             'Libre',
  ocupada:           'Ocupada',
  pedido_solicitado: 'Pedido Solicitado',
  pedido_cumplido:   'Pedido Cumplido',
  cuenta:            'Cuenta',
  inactiva:          'Inactiva',
};

const STATUS_COLORS: Record<TableStatus, string> = {
  libre:             'bg-green-500 hover:bg-green-600',
  ocupada:           'bg-red-500 hover:bg-red-600',
  pedido_solicitado: 'bg-yellow-500 hover:bg-yellow-600',
  pedido_cumplido:   'bg-blue-500 hover:bg-blue-600',
  cuenta:            'bg-purple-500 hover:bg-purple-600',
  inactiva:          'bg-gray-500 hover:bg-gray-600',
};

interface Props {
  table: Table | null;
  isOpen: boolean;
  onClose: () => void;
  onTransition: (tableId: number, newStatus: TableStatus, version: number) => Promise<void>;
}

export function TableStatusModal({ table, isOpen, onClose, onTransition }: Props) {
  const [isTransitioning, setIsTransitioning] = useState(false);

  if (!table) return null;

  const validTransitions = TABLE_TRANSITIONS[table.estado] ?? [];

  const handleTransition = async (newStatus: TableStatus) => {
    setIsTransitioning(true);
    try {
      await onTransition(table.id, newStatus, table.version);
      onClose();
    } finally {
      setIsTransitioning(false);
    }
  };

  return (
    <Modal isOpen={isOpen} onClose={onClose} title={table.codigo ?? `Mesa ${table.numero}`}>
      <div className="space-y-4">
        {/* Current status */}
        <div className="flex items-center gap-3">
          <span className="text-sm text-text-secondary">Estado actual:</span>
          <span className={cn(
            'px-3 py-1 rounded-full text-xs font-medium text-white',
            STATUS_COLORS[table.estado],
          )}>
            {STATUS_LABELS[table.estado]}
          </span>
        </div>

        {/* Table info */}
        <div className="grid grid-cols-2 gap-3 text-sm">
          <div>
            <span className="text-text-tertiary">Capacidad</span>
            <p className="text-text-primary font-medium">{table.capacidad} personas</p>
          </div>
          <div>
            <span className="text-text-tertiary">Numero</span>
            <p className="text-text-primary font-medium">{table.numero}</p>
          </div>
        </div>

        {/* Transition buttons */}
        {validTransitions.length > 0 ? (
          <div className="pt-2 border-t border-border-default">
            <p className="text-sm text-text-secondary mb-3">Cambiar estado a:</p>
            <div className="flex flex-wrap gap-2">
              {validTransitions.map((status) => (
                <Button
                  key={status}
                  size="sm"
                  variant="secondary"
                  onClick={() => handleTransition(status)}
                  disabled={isTransitioning}
                  isLoading={isTransitioning}
                >
                  {STATUS_LABELS[status]}
                </Button>
              ))}
            </div>
          </div>
        ) : null}
      </div>
    </Modal>
  );
}
