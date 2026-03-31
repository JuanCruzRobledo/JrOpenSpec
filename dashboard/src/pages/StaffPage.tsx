/**
 * StaffPage — paginated table with search for staff management.
 * Staff is tenant-scoped (no branch guard needed).
 */
import { useState, useMemo, useCallback } from 'react';
import { Table, type TableColumn } from '@/components/ui/Table';
import { Pagination } from '@/components/ui/Pagination';
import { Button } from '@/components/ui/Button';
import { Badge } from '@/components/ui/Badge';
import { Modal } from '@/components/ui/Modal';
import { EmptyState } from '@/components/ui/EmptyState';
import { HelpButton } from '@/components/ui/HelpButton';
import { StaffForm } from '@/components/staff/StaffForm';
import { StaffSearch } from '@/components/staff/StaffSearch';
import { useStaffSearch } from '@/hooks/useStaffSearch';
import { useStaffStore } from '@/stores/staff.store';
import { useConfirm } from '@/hooks/useConfirm';
import { useToast } from '@/hooks/useToast';
import { helpContent } from '@/utils/helpContent';
import { logger } from '@/lib/logger';
import type { Staff, StaffCreate, StaffUpdate } from '@/types/staff';

const ROLE_LABELS: Record<string, string> = {
  OWNER: 'Propietario',
  ADMIN: 'Administrador',
  MANAGER: 'Gerente',
  WAITER: 'Mozo',
  CHEF: 'Chef',
  CASHIER: 'Cajero',
};

export default function StaffPage() {
  const confirm = useConfirm();
  const toast = useToast();

  const {
    staff,
    isLoading,
    error,
    searchQuery,
    roleFilter,
    page,
    totalPages,
    handleSearchChange,
    setRoleFilter,
    setPage,
    refresh,
  } = useStaffSearch();

  // Store actions (individual selectors)
  const createStaff = useStaffStore((s) => s.createStaff);
  const updateStaff = useStaffStore((s) => s.updateStaff);
  const removeStaff = useStaffStore((s) => s.removeStaff);

  const [isModalOpen, setIsModalOpen] = useState(false);
  const [editingStaff, setEditingStaff] = useState<Staff | null>(null);

  const handleCreate = useCallback(() => {
    setEditingStaff(null);
    setIsModalOpen(true);
  }, []);

  const handleEdit = useCallback((member: Staff) => {
    setEditingStaff(member);
    setIsModalOpen(true);
  }, []);

  const handleDelete = useCallback(async (member: Staff) => {
    const confirmed = await confirm({
      title: `Eliminar a "${member.nombre_completo}"?`,
      description: 'Esta accion no se puede deshacer.',
      confirmLabel: 'Eliminar',
      variant: 'danger',
    });

    if (confirmed) {
      try {
        await removeStaff(member.id);
        toast.success('Miembro eliminado');
      } catch (err) {
        const message = err instanceof Error ? err.message : 'Error al eliminar';
        toast.error(message);
        logger.error('Failed to delete staff member', err);
      }
    }
  }, [confirm, removeStaff, toast]);

  const handleFormSuccess = useCallback(() => {
    setIsModalOpen(false);
    setEditingStaff(null);
    refresh();
  }, [refresh]);

  const handleFormCancel = useCallback(() => {
    setIsModalOpen(false);
    setEditingStaff(null);
  }, []);

  const handleCreateFn = useCallback(
    async (data: StaffCreate): Promise<Staff | null> => {
      try {
        const result = await createStaff(data);
        toast.success('Miembro creado exitosamente');
        return result;
      } catch (err) {
        const message = err instanceof Error ? err.message : 'Error al crear miembro';
        toast.error(message);
        logger.error('Failed to create staff member', err);
        return null;
      }
    },
    [createStaff, toast],
  );

  const handleUpdateFn = useCallback(
    async (id: number, data: StaffUpdate): Promise<Staff | null> => {
      try {
        const result = await updateStaff(id, data);
        toast.success('Miembro actualizado exitosamente');
        return result;
      } catch (err) {
        const message = err instanceof Error ? err.message : 'Error al actualizar';
        toast.error(message);
        logger.error('Failed to update staff member', err);
        return null;
      }
    },
    [updateStaff, toast],
  );

  const formatDate = useCallback((dateStr: string | null) => {
    if (!dateStr) return '—';
    try {
      return new Date(dateStr).toLocaleDateString('es-AR');
    } catch {
      return dateStr;
    }
  }, []);

  const columns: TableColumn<Staff>[] = useMemo(() => [
    {
      key: 'nombre',
      header: 'Nombre',
      render: (m) => <span className="font-medium">{m.nombre_completo}</span>,
    },
    {
      key: 'email',
      header: 'Email',
      render: (m) => <span className="text-text-secondary">{m.email}</span>,
    },
    {
      key: 'rol',
      header: 'Rol',
      render: (m) => (
        <Badge variant="default">
          {m.rol ? (ROLE_LABELS[m.rol] ?? m.rol) : '—'}
        </Badge>
      ),
    },
    {
      key: 'dni',
      header: 'DNI',
      className: 'w-32',
      render: (m) => m.dni ?? '—',
    },
    {
      key: 'fecha_contratacion',
      header: 'Contratacion',
      className: 'w-36',
      render: (m) => formatDate(m.fecha_contratacion),
    },
    {
      key: 'estado',
      header: 'Estado',
      render: (m) => (
        <Badge variant={m.estado === 'activo' ? 'success' : 'default'}>
          {m.estado === 'activo' ? 'Activo' : 'Inactivo'}
        </Badge>
      ),
    },
    {
      key: 'acciones',
      header: 'Acciones',
      className: 'text-right',
      render: (m) => (
        <div className="flex justify-end gap-2">
          <Button size="sm" variant="ghost" onClick={() => handleEdit(m)}>
            Editar
          </Button>
          <Button size="sm" variant="danger" onClick={() => handleDelete(m)}>
            Eliminar
          </Button>
        </div>
      ),
    },
  ], [handleEdit, handleDelete, formatDate]);

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold text-text-primary">Personal</h1>
          <p className="mt-1 text-sm text-text-secondary">
            Administra los miembros del equipo y sus roles
          </p>
        </div>
        <div className="flex items-center gap-3">
          <HelpButton content={helpContent.staff} />
          <Button onClick={handleCreate}>Agregar miembro</Button>
        </div>
      </div>

      <StaffSearch
        searchQuery={searchQuery}
        roleFilter={roleFilter}
        onSearchChange={handleSearchChange}
        onRoleChange={setRoleFilter}
      />

      {!isLoading && staff.length === 0 && !error ? (
        <EmptyState
          title="No hay personal"
          description="Agrega los miembros de tu equipo para gestionar roles y permisos."
          actionLabel="Agregar miembro"
          onAction={handleCreate}
        />
      ) : (
        <>
          <div className="rounded-xl bg-bg-surface border border-border-default overflow-hidden">
            <Table
              columns={columns}
              data={staff}
              keyExtractor={(m) => m.id}
              isLoading={isLoading}
            />
          </div>
          <Pagination
            currentPage={page}
            totalPages={totalPages}
            onPageChange={setPage}
          />
        </>
      )}

      {error ? (
        <div className="text-center py-8">
          <p className="text-error mb-4">{error}</p>
          <Button variant="secondary" onClick={() => refresh()}>
            Reintentar
          </Button>
        </div>
      ) : null}

      <Modal
        isOpen={isModalOpen}
        onClose={handleFormCancel}
        title={editingStaff ? 'Editar miembro' : 'Agregar miembro'}
      >
        <StaffForm
          key={editingStaff?.id ?? 'new'}
          staff={editingStaff}
          onSuccess={handleFormSuccess}
          onCancel={handleFormCancel}
          createFn={handleCreateFn}
          updateFn={handleUpdateFn}
        />
      </Modal>
    </div>
  );
}
