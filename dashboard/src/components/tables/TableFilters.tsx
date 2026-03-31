/**
 * TableFilters — filter bar with sector dropdown, status dropdown, and search.
 * Presentational: receives filter state and callbacks as props.
 */
import { Select } from '@/components/ui/Select';
import { Input } from '@/components/ui/Input';
import type { TableStatus } from '@/types/table';
import type { Sector } from '@/types/sector';
import { useMemo } from 'react';

const STATUS_OPTIONS: Array<{ value: string; label: string }> = [
  { value: 'libre', label: 'Libre' },
  { value: 'ocupada', label: 'Ocupada' },
  { value: 'pedido_solicitado', label: 'Pedido Solicitado' },
  { value: 'pedido_cumplido', label: 'Pedido Cumplido' },
  { value: 'cuenta', label: 'Cuenta' },
  { value: 'inactiva', label: 'Inactiva' },
];

interface Props {
  sectors: Sector[];
  selectedSectorId: number | null;
  selectedStatus: TableStatus | null;
  searchQuery: string;
  onSectorChange: (sectorId: number | null) => void;
  onStatusChange: (status: TableStatus | null) => void;
  onSearchChange: (query: string) => void;
}

export function TableFilters({
  sectors,
  selectedSectorId,
  selectedStatus,
  searchQuery,
  onSectorChange,
  onStatusChange,
  onSearchChange,
}: Props) {
  const sectorOptions = useMemo(
    () => sectors.map((s) => ({ value: s.id, label: s.nombre })),
    [sectors],
  );

  return (
    <div className="flex flex-wrap items-end gap-4 mb-6">
      <div className="w-48">
        <Select
          label="Sector"
          options={sectorOptions}
          placeholder="Todos los sectores"
          value={selectedSectorId ?? ''}
          onChange={(e) => {
            const val = e.target.value;
            onSectorChange(val ? parseInt(val, 10) : null);
          }}
        />
      </div>

      <div className="w-48">
        <Select
          label="Estado"
          options={STATUS_OPTIONS}
          placeholder="Todos los estados"
          value={selectedStatus ?? ''}
          onChange={(e) => {
            const val = e.target.value;
            onStatusChange((val || null) as TableStatus | null);
          }}
        />
      </div>

      <div className="w-56">
        <Input
          label="Buscar"
          placeholder="Buscar mesa..."
          value={searchQuery}
          onChange={(e) => onSearchChange(e.target.value)}
        />
      </div>
    </div>
  );
}
