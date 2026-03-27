/**
 * Branches CRUD page — full list with create, edit, and delete.
 * MANAGER role: can edit but NOT create or delete.
 */
import { useState, useMemo, useCallback } from 'react';
import { Table, type TableColumn } from '@/components/ui/Table';
import { Pagination } from '@/components/ui/Pagination';
import { Button } from '@/components/ui/Button';
import { Badge } from '@/components/ui/Badge';
import { Modal } from '@/components/ui/Modal';
import { EmptyState } from '@/components/ui/EmptyState';
import { HelpButton } from '@/components/ui/HelpButton';
import { BranchForm } from '@/components/forms/BranchForm';
import { useCrud } from '@/hooks/useCrud';
import { useConfirm } from '@/hooks/useConfirm';
import { useAuth } from '@/hooks/useAuth';
import { branchService } from '@/services/branch.service';
import { helpContent } from '@/utils/helpContent';
import type { Branch, BranchCreate, BranchUpdate } from '@/types/branch';

export default function BranchesPage() {
  const { user } = useAuth();
  const confirm = useConfirm();
  const isManager = user?.roles?.includes('MANAGER') ?? false;
  const canCreate = !isManager;
  const canDelete = !isManager;

  const [isModalOpen, setIsModalOpen] = useState(false);
  const [editingBranch, setEditingBranch] = useState<Branch | null>(null);

  const crud = useCrud<Branch, BranchCreate, BranchUpdate>({
    fetchFn: (params) => branchService.list(params),
    createFn: (data) => branchService.create(data),
    updateFn: (id, data) => branchService.update(id, data),
    deleteFn: (id) => branchService.remove(id),
    entityName: 'Sucursal',
  });

  const handleCreate = useCallback(() => {
    setEditingBranch(null);
    setIsModalOpen(true);
  }, []);

  const handleEdit = useCallback((branch: Branch) => {
    setEditingBranch(branch);
    setIsModalOpen(true);
  }, []);

  const handleDelete = useCallback(async (branch: Branch) => {
    const confirmed = await confirm({
      title: `Eliminar sucursal "${branch.nombre}"?`,
      description: 'Se eliminaran todas las categorias, subcategorias y productos asociados. Esta accion no se puede deshacer.',
      confirmLabel: 'Eliminar',
      variant: 'danger',
    });

    if (confirmed) {
      await crud.remove(branch.id);
    }
  }, [confirm, crud]);

  const handleFormSuccess = useCallback(() => {
    setIsModalOpen(false);
    setEditingBranch(null);
    crud.refresh();
  }, [crud]);

  const handleFormCancel = useCallback(() => {
    setIsModalOpen(false);
    setEditingBranch(null);
  }, []);

  const columns: TableColumn<Branch>[] = useMemo(() => [
    {
      key: 'nombre',
      header: 'Nombre',
      render: (b) => <span className="font-medium">{b.nombre}</span>,
    },
    {
      key: 'direccion',
      header: 'Direccion',
      render: (b) => b.direccion ?? <span className="text-text-tertiary">—</span>,
    },
    {
      key: 'telefono',
      header: 'Telefono',
      render: (b) => b.telefono ?? <span className="text-text-tertiary">—</span>,
    },
    {
      key: 'horario',
      header: 'Horario',
      render: (b) => (
        <span className="text-text-secondary text-xs">
          {b.horario_apertura ?? '09:00'} - {b.horario_cierre ?? '23:00'}
        </span>
      ),
    },
    {
      key: 'estado',
      header: 'Estado',
      render: (b) => (
        <Badge variant={b.estado === 'activo' ? 'success' : 'default'}>
          {b.estado === 'activo' ? 'Activo' : 'Inactivo'}
        </Badge>
      ),
    },
    {
      key: 'acciones',
      header: 'Acciones',
      className: 'text-right',
      render: (b) => (
        <div className="flex justify-end gap-2">
          <Button size="sm" variant="ghost" onClick={() => handleEdit(b)}>
            Editar
          </Button>
          {canDelete ? (
            <Button size="sm" variant="danger" onClick={() => handleDelete(b)}>
              Eliminar
            </Button>
          ) : null}
        </div>
      ),
    },
  ], [canDelete, handleEdit, handleDelete]);

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold text-text-primary">Sucursales</h1>
          <p className="mt-1 text-sm text-text-secondary">
            Administra las sucursales de tu restaurante
          </p>
        </div>
        <div className="flex items-center gap-3">
          <HelpButton content={helpContent.branches} />
          {canCreate ? (
            <Button onClick={handleCreate}>Crear sucursal</Button>
          ) : null}
        </div>
      </div>

      {!crud.isLoading && crud.items.length === 0 && !crud.error ? (
        <EmptyState
          title="No hay sucursales"
          description="Crea tu primera sucursal para empezar a configurar el menu."
          actionLabel={canCreate ? 'Crear sucursal' : undefined}
          onAction={canCreate ? handleCreate : undefined}
        />
      ) : (
        <>
          <div className="rounded-xl bg-bg-surface border border-border-default overflow-hidden">
            <Table
              columns={columns}
              data={crud.items}
              keyExtractor={(b) => b.id}
              isLoading={crud.isLoading}
            />
          </div>
          <Pagination
            currentPage={crud.page}
            totalPages={crud.totalPages}
            onPageChange={crud.setPage}
          />
        </>
      )}

      {crud.error ? (
        <div className="text-center py-8">
          <p className="text-error mb-4">{crud.error}</p>
          <Button variant="secondary" onClick={crud.refresh}>
            Reintentar
          </Button>
        </div>
      ) : null}

      <Modal
        isOpen={isModalOpen}
        onClose={handleFormCancel}
        title={editingBranch ? 'Editar sucursal' : 'Crear sucursal'}
      >
        <BranchForm
          key={editingBranch?.id ?? 'new'}
          branch={editingBranch}
          onSuccess={handleFormSuccess}
          onCancel={handleFormCancel}
          createFn={crud.create}
          updateFn={crud.update}
        />
      </Modal>
    </div>
  );
}
