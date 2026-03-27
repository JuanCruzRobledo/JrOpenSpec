import type { ReactNode } from 'react';
import { cn } from '@/lib/cn';

// ---- Column definition ----
export interface TableColumn<T> {
  key: string;
  header: string;
  render: (item: T) => ReactNode;
  className?: string;
}

// ---- Table Props ----
interface Props<T> {
  columns: TableColumn<T>[];
  data: T[];
  keyExtractor: (item: T) => string | number;
  isLoading?: boolean;
  className?: string;
}

export function Table<T>({ columns, data, keyExtractor, isLoading, className }: Props<T>) {
  return (
    <div className={cn('overflow-x-auto', className)}>
      <table className="w-full">
        <thead>
          <tr className="sticky top-0 bg-bg-surface border-b border-border-default">
            {columns.map((col) => (
              <th
                key={col.key}
                className={cn(
                  'px-4 py-3 text-left text-xs font-semibold uppercase text-text-secondary tracking-wider',
                  col.className,
                )}
              >
                {col.header}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {isLoading ? (
            // Skeleton rows
            Array.from({ length: 5 }).map((_, i) => (
              <tr key={`skeleton-${i}`} className="border-b border-border-default">
                {columns.map((col) => (
                  <td key={col.key} className="px-4 py-4">
                    <div className="h-4 w-24 animate-pulse rounded bg-bg-elevated" />
                  </td>
                ))}
              </tr>
            ))
          ) : data.length === 0 ? (
            <tr>
              <td
                colSpan={columns.length}
                className="px-4 py-16 text-center text-text-tertiary"
              >
                No hay datos para mostrar
              </td>
            </tr>
          ) : (
            data.map((item) => (
              <tr
                key={keyExtractor(item)}
                className="border-b border-border-default hover:bg-bg-elevated transition-colors h-14"
              >
                {columns.map((col) => (
                  <td
                    key={col.key}
                    className={cn('px-4 py-3 text-sm text-text-primary', col.className)}
                  >
                    {col.render(item)}
                  </td>
                ))}
              </tr>
            ))
          )}
        </tbody>
      </table>
    </div>
  );
}
