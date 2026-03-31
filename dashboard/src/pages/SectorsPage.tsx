/**
 * SectorsPage — CRUD page for sectors, scoped to selected branch.
 */
import { useState, useMemo, useCallback, useEffect } from 'react';
import { useShallow } from 'zustand/react/shallow';
import { Table, type TableColumn } from '@/components/ui/Table';
import { Pagination } from '@/components/ui/Pagination';
import { Button } from '@/components/ui/Button';
import { Badge } from '@/components/ui/Badge';
import { Modal } from '@/components/ui/Modal';
import { EmptyState } from '@/components/ui/EmptyState';
import { HelpButton } from '@/components/ui/HelpButton';
import { SectorForm } from '@/components/forms/SectorForm';
import { useConfirm } from '@/hooks/useConfirm';
import { useBranch } from '@/hooks/useBranch';
import { useToast } from '@/hooks/useToast';
import { useSectorStore, selectSectors, selectSectorsLoading, selectSectorsError } from '@/stores/sector.store';
import { helpContent } from '@/utils/helpContent';
import { logger } from '@/lib/logger';
import type { Sector, SectorCreate, SectorUpdate } from '@/types/sector';

const TIPO_LABELS: Record<string, string> = {
  interior: 'Interior',
  terraza: 'Terraza',
  barra: 'Barra',
  vip: 'VIP',
};

export default function SectorsPage() {
  const { selectedBranchId } = useBranch();
  const branchId = selectedBranchId!;
  const confirm = useConfirm();
  const toast = useToast();

  // Store selectors (never destructure)
  const sectors = useSectorStore(useShallow(selectSectors));
  const isLoading = useSectorStore(selectSectorsLoading);
  const error = useSectorStore(selectSectorsError);
  const fetchSectors = useSectorStore((s) => s.fetchSectors);
  const createSector = useSectorStore((s) => s.createSector);
  const updateSector = useSectorStore((s) => s.updateSector);
  const removeSector = useSectorStore((s) => s.removeSector);

  const [isModalOpen, setIsModalOpen] = useState(false);
  const [editingSector, setEditingSector] = useState<Sector | null>(null);

  useEffect(() => {
    fetchSectors(branchId);
  }, [branchId, fetchSectors]);

  const handleCreate = useCallback(() => {
    setEditingSector(null);
    setIsModalOpen(true);
  }, []);

  const handleEdit = useCallback((sector: Sector) => {
    setEditingSector(sector);
    setIsModalOpen(true);
  }, []);

  const handleDelete = useCallback(async (sector: Sector) => {
    const confirmed = await confirm({
      title: `Eliminar sector "${sector.nombre}"?`,
      description: 'Se eliminaran todas las mesas de este sector. Esta accion no se puede deshacer.',
      confirmLabel: 'Eliminar',
      variant: 'danger',
    });

    if (confirmed) {
      try {
        await removeSector(branchId, sector.id);
        toast.success('Sector eliminado');
      } catch (err) {
        const message = err instanceof Error ? err.message : 'Error al eliminar sector';
        toast.error(message);
        logger.error('Failed to delete sector', err);
      }
    }
  }, [confirm, branchId, removeSector, toast]);

  const handleFormSuccess = useCallback(() => {
    setIsModalOpen(false);
    setEditingSector(null);
    fetchSectors(branchId);
  }, [branchId, fetchSectors]);

  const handleFormCancel = useCallback(() => {
    setIsModalOpen(false);
    setEditingSector(null);
  }, []);

  const handleCreateFn = useCallback(
    async (data: SectorCreate): Promise<Sector | null> => {
      try {
        const result = await createSector(branchId, data);
        toast.success('Sector creado exitosamente');
        return result;
      } catch (err) {
        const message = err instanceof Error ? err.message : 'Error al crear sector';
        toast.error(message);
        logger.error('Failed to create sector', err);
        return null;
      }
    },
    [branchId, createSector, toast],
  );

  const handleUpdateFn = useCallback(
    async (id: number, data: SectorUpdate): Promise<Sector | null> => {
      try {
        const result = await updateSector(branchId, id, data);
        toast.success('Sector actualizado exitosamente');
        return result;
      } catch (err) {
        const message = err instanceof Error ? err.message : 'Error al actualizar sector';
        toast.error(message);
        logger.error('Failed to update sector', err);
        return null;
      }
    },
    [branchId, updateSector, toast],
  );

  const columns: TableColumn<Sector>[] = useMemo(() => [
    {
      key: 'nombre',
      header: 'Nombre',
      render: (s) => <span className="font-medium">{s.nombre}</span>,
    },
    {
      key: 'tipo',
      header: 'Tipo',
      render: (s) => TIPO_LABELS[s.tipo] ?? s.tipo,
    },
    {
      key: 'prefijo',
      header: 'Prefijo',
      className: 'w-24',
      render: (s) => (
        <span className="font-mono text-xs bg-bg-elevated px-2 py-1 rounded">
          {s.prefijo}
        </span>
      ),
    },
    {
      key: 'capacidad',
      header: 'Capacidad',
      className: 'w-28',
      render: (s) => s.capacidad ?? 'Sin limite',
    },
    {
      key: 'mesas',
      header: 'Mesas',
      className: 'w-28',
      render: (s) => `${s.mesas_disponibles}/${s.cantidad_mesas}`,
    },
    {
      key: 'estado',
      header: 'Estado',
      render: (s) => (
        <Badge variant={s.estado === 'activo' ? 'success' : 'default'}>
          {s.estado === 'activo' ? 'Activo' : 'Inactivo'}
        </Badge>
      ),
    },
    {
      key: 'acciones',
      header: 'Acciones',
      className: 'text-right',
      render: (s) => (
        <div className="flex justify-end gap-2">
          <Button size="sm" variant="ghost" onClick={() => handleEdit(s)}>
            Editar
          </Button>
          <Button size="sm" variant="danger" onClick={() => handleDelete(s)}>
            Eliminar
          </Button>
        </div>
      ),
    },
  ], [handleEdit, handleDelete]);

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold text-text-primary">Sectores</h1>
          <p className="mt-1 text-sm text-text-secondary">
            Organiza tu salon en sectores para gestionar mesas
          </p>
        </div>
        <div className="flex items-center gap-3">
          <HelpButton content={helpContent.sectors} />
          <Button onClick={handleCreate}>Crear sector</Button>
        </div>
      </div>

      {!isLoading && sectors.length === 0 && !error ? (
        <EmptyState
          title="No hay sectores"
          description="Crea tu primer sector para organizar las mesas del salon."
          actionLabel="Crear sector"
          onAction={handleCreate}
        />
      ) : (
        <div className="rounded-xl bg-bg-surface border border-border-default overflow-hidden">
          <Table
            columns={columns}
            data={sectors}
            keyExtractor={(s) => s.id}
            isLoading={isLoading}
          />
        </div>
      )}

      {error ? (
        <div className="text-center py-8">
          <p className="text-error mb-4">{error}</p>
          <Button variant="secondary" onClick={() => fetchSectors(branchId)}>
            Reintentar
          </Button>
        </div>
      ) : null}

      <Modal
        isOpen={isModalOpen}
        onClose={handleFormCancel}
        title={editingSector ? 'Editar sector' : 'Crear sector'}
      >
        <SectorForm
          key={editingSector?.id ?? 'new'}
          sector={editingSector}
          onSuccess={handleFormSuccess}
          onCancel={handleFormCancel}
          createFn={handleCreateFn}
          updateFn={handleUpdateFn}
        />
      </Modal>
    </div>
  );
}
