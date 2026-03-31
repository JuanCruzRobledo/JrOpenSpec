/**
 * TableGrid — CSS Grid layout for TableCards.
 * Presentational: receives tables as props, renders them in a responsive grid.
 */
import { TableCard } from '@/components/tables/TableCard';
import type { Table } from '@/types/table';

interface Props {
  tables: Table[];
  onTableClick: (table: Table) => void;
}

export function TableGrid({ tables, onTableClick }: Props) {
  if (tables.length === 0) {
    return null;
  }

  return (
    <div className="grid gap-4" style={{ gridTemplateColumns: 'repeat(auto-fill, minmax(160px, 1fr))' }}>
      {tables.map((table) => (
        <TableCard
          key={table.id}
          codigo={table.codigo}
          numero={table.numero}
          capacidad={table.capacidad}
          estado={table.estado}
          statusChangedAt={table.status_changed_at}
          onClick={() => onTableClick(table)}
        />
      ))}
    </div>
  );
}
