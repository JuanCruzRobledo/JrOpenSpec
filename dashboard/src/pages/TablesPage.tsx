/**
 * TablesPage — container page for table management.
 * Fetches tables, shows grid sorted by urgency, handles modals.
 */
import { useState, useCallback } from 'react';
import { Button } from '@/components/ui/Button';
import { Modal } from '@/components/ui/Modal';
import { EmptyState } from '@/components/ui/EmptyState';
import { HelpButton } from '@/components/ui/HelpButton';
import { TableGrid } from '@/components/tables/TableGrid';
import { TableFilters } from '@/components/tables/TableFilters';
import { TableStatusModal } from '@/components/tables/TableStatusModal';
import { TableBatchForm } from '@/components/tables/TableBatchForm';
import { StatusLegend } from '@/components/tables/StatusLegend';
import { useTableGrid } from '@/hooks/useTableGrid';
import { useTableStore } from '@/stores/table.store';
import { useToast } from '@/hooks/useToast';
import { useBranch } from '@/hooks/useBranch';
import { logger } from '@/lib/logger';
import { helpContent } from '@/utils/helpContent';
import type { Table, TableStatus } from '@/types/table';

export default function TablesPage() {
  const { selectedBranchId } = useBranch();
  const branchId = selectedBranchId!;
  const toast = useToast();

  const {
    tables,
    sectors,
    isLoading,
    error,
    sectorFilter,
    statusFilter,
    searchQuery,
    setSectorFilter,
    setStatusFilter,
    setSearchQuery,
    refresh,
  } = useTableGrid();

  // Store actions (individual selectors)
  const updateTableStatus = useTableStore((s) => s.updateTableStatus);
  const createTableBatch = useTableStore((s) => s.createTableBatch);

  // Modal state
  const [selectedTable, setSelectedTable] = useState<Table | null>(null);
  const [isStatusModalOpen, setIsStatusModalOpen] = useState(false);
  const [isBatchModalOpen, setIsBatchModalOpen] = useState(false);

  const handleTableClick = useCallback((table: Table) => {
    setSelectedTable(table);
    setIsStatusModalOpen(true);
  }, []);

  const handleStatusTransition = useCallback(
    async (tableId: number, newStatus: TableStatus, version: number) => {
      try {
        await updateTableStatus(branchId, tableId, { estado: newStatus, version });
        toast.success('Estado actualizado');
      } catch (err) {
        const message = err instanceof Error ? err.message : 'Error al cambiar estado';
        toast.error(message);
        logger.error('Failed to transition table status', err);
      }
    },
    [branchId, updateTableStatus, toast],
  );

  const handleBatchSuccess = useCallback(() => {
    setIsBatchModalOpen(false);
    refresh();
  }, [refresh]);

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold text-text-primary">Mesas</h1>
          <p className="mt-1 text-sm text-text-secondary">
            Gestion de mesas por sector y estado en tiempo real
          </p>
        </div>
        <div className="flex items-center gap-3">
          <HelpButton content={helpContent.tables} />
          <Button onClick={() => setIsBatchModalOpen(true)}>Crear mesas</Button>
        </div>
      </div>

      <TableFilters
        sectors={sectors}
        selectedSectorId={sectorFilter}
        selectedStatus={statusFilter}
        searchQuery={searchQuery}
        onSectorChange={setSectorFilter}
        onStatusChange={setStatusFilter}
        onSearchChange={setSearchQuery}
      />

      <StatusLegend className="mb-4" />

      {!isLoading && tables.length === 0 && !error ? (
        <EmptyState
          title="No hay mesas"
          description="Crea tus primeras mesas para comenzar a gestionar el salon."
          actionLabel="Crear mesas"
          onAction={() => setIsBatchModalOpen(true)}
        />
      ) : (
        <TableGrid tables={tables} onTableClick={handleTableClick} />
      )}

      {error ? (
        <div className="text-center py-8">
          <p className="text-error mb-4">{error}</p>
          <Button variant="secondary" onClick={refresh}>
            Reintentar
          </Button>
        </div>
      ) : null}

      {/* Status transition modal */}
      <TableStatusModal
        table={selectedTable}
        isOpen={isStatusModalOpen}
        onClose={() => {
          setIsStatusModalOpen(false);
          setSelectedTable(null);
        }}
        onTransition={handleStatusTransition}
      />

      {/* Batch creation modal */}
      <Modal
        isOpen={isBatchModalOpen}
        onClose={() => setIsBatchModalOpen(false)}
        title="Crear mesas en lote"
      >
        <TableBatchForm
          sectors={sectors}
          onSuccess={handleBatchSuccess}
          onCancel={() => setIsBatchModalOpen(false)}
          createBatchFn={(data) => createTableBatch(branchId, data)}
        />
      </Modal>
    </div>
  );
}
