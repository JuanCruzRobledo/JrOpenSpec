/**
 * AssignmentMatrix — matrix UI for waiter-sector assignments.
 * Rows = waiters, columns = sectors, cells = toggle checkboxes.
 * Presentational: receives all data and callbacks as props.
 */
import { cn } from '@/lib/cn';
import type { Staff } from '@/types/staff';
import type { Sector } from '@/types/sector';

interface Props {
  waiters: Staff[];
  sectors: Sector[];
  /** Set of "waiterId:sectorId" keys representing active assignments */
  selectedCells: Set<string>;
  onToggle: (waiterId: number, sectorId: number) => void;
  disabled?: boolean;
}

/** Creates a unique cell key from waiter and sector IDs. */
export function cellKey(waiterId: number, sectorId: number): string {
  return `${waiterId}:${sectorId}`;
}

export function AssignmentMatrix({ waiters, sectors, selectedCells, onToggle, disabled = false }: Props) {
  if (waiters.length === 0) {
    return (
      <p className="text-sm text-text-secondary py-4">
        No hay mozos disponibles para asignar.
      </p>
    );
  }

  if (sectors.length === 0) {
    return (
      <p className="text-sm text-text-secondary py-4">
        No hay sectores disponibles.
      </p>
    );
  }

  return (
    <div className="overflow-x-auto rounded-xl border border-border-default">
      <table className="w-full text-sm">
        <thead>
          <tr className="bg-bg-elevated">
            <th className="text-left px-4 py-3 font-medium text-text-primary border-b border-border-default sticky left-0 bg-bg-elevated z-10">
              Mozo
            </th>
            {sectors.map((sector) => (
              <th
                key={sector.id}
                className="text-center px-4 py-3 font-medium text-text-primary border-b border-border-default whitespace-nowrap"
              >
                {sector.nombre}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {waiters.map((waiter, i) => (
            <tr
              key={waiter.id}
              className={cn(
                'border-b border-border-default last:border-b-0',
                i % 2 === 0 ? 'bg-bg-surface' : 'bg-bg-primary',
              )}
            >
              <td className="px-4 py-2.5 text-text-primary font-medium sticky left-0 z-10 bg-inherit">
                {waiter.nombre_completo}
              </td>
              {sectors.map((sector) => {
                const key = cellKey(waiter.id, sector.id);
                const isChecked = selectedCells.has(key);

                return (
                  <td key={sector.id} className="text-center px-4 py-2.5">
                    <input
                      type="checkbox"
                      checked={isChecked}
                      onChange={() => onToggle(waiter.id, sector.id)}
                      disabled={disabled}
                      className="h-4 w-4 rounded border-border-default bg-bg-surface text-accent focus:ring-accent cursor-pointer disabled:cursor-not-allowed disabled:opacity-50"
                    />
                  </td>
                );
              })}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
