/**
 * Dietary Profiles CRUD page — tenant-scoped.
 * System profiles (7 predefined) are read-only.
 */
import { useState, useMemo, useCallback } from 'react';
import { Table, type TableColumn } from '@/components/ui/Table';
import { Pagination } from '@/components/ui/Pagination';
import { Button } from '@/components/ui/Button';
import { Badge } from '@/components/ui/Badge';
import { Modal } from '@/components/ui/Modal';
import { EmptyState } from '@/components/ui/EmptyState';
import { HelpButton } from '@/components/ui/HelpButton';
import { DietaryProfileForm } from '@/components/forms/DietaryProfileForm';
import { useCrud } from '@/hooks/useCrud';
import { useConfirm } from '@/hooks/useConfirm';
import { dietaryProfileService } from '@/services/dietary-profile.service';
import { helpContent } from '@/utils/helpContent';
import type {
  DietaryProfile,
  DietaryProfileCreate,
  DietaryProfileUpdate,
} from '@/types/dietary-profile';

export default function DietaryProfilesPage() {
  const confirm = useConfirm();

  const [isModalOpen, setIsModalOpen] = useState(false);
  const [editingProfile, setEditingProfile] = useState<DietaryProfile | null>(null);

  const crud = useCrud<DietaryProfile, DietaryProfileCreate, DietaryProfileUpdate>({
    fetchFn: (params) => dietaryProfileService.list(params),
    createFn: (data) => dietaryProfileService.create(data),
    updateFn: (id, data) => dietaryProfileService.update(id, data),
    deleteFn: (id) => dietaryProfileService.remove(id),
    entityName: 'Perfil dietetico',
  });

  const handleCreate = useCallback(() => {
    setEditingProfile(null);
    setIsModalOpen(true);
  }, []);

  const handleEdit = useCallback((profile: DietaryProfile) => {
    setEditingProfile(profile);
    setIsModalOpen(true);
  }, []);

  const handleDelete = useCallback(async (profile: DietaryProfile) => {
    if (profile.es_sistema) return;

    const confirmed = await confirm({
      title: `Eliminar perfil "${profile.nombre}"?`,
      description: 'El perfil sera eliminado. Los productos asociados perderan esta referencia.',
      confirmLabel: 'Eliminar',
      variant: 'danger',
    });

    if (confirmed) {
      await crud.remove(profile.id);
    }
  }, [confirm, crud]);

  const handleFormSuccess = useCallback(() => {
    setIsModalOpen(false);
    setEditingProfile(null);
    crud.refresh();
  }, [crud]);

  const handleFormCancel = useCallback(() => {
    setIsModalOpen(false);
    setEditingProfile(null);
  }, []);

  const columns: TableColumn<DietaryProfile>[] = useMemo(() => [
    {
      key: 'icono',
      header: 'Icono',
      className: 'w-16',
      render: (p) => (
        <span className="text-lg">{p.icono ?? '—'}</span>
      ),
    },
    {
      key: 'nombre',
      header: 'Nombre',
      render: (p) => <span className="font-medium">{p.nombre}</span>,
    },
    {
      key: 'codigo',
      header: 'Codigo',
      render: (p) => (
        <span className="text-xs text-text-secondary font-mono">{p.codigo}</span>
      ),
    },
    {
      key: 'tipo',
      header: 'Tipo',
      render: (p) => (
        <Badge variant={p.es_sistema ? 'info' : 'default'}>
          {p.es_sistema ? 'Sistema' : 'Personalizado'}
        </Badge>
      ),
    },
    {
      key: 'acciones',
      header: 'Acciones',
      className: 'text-right',
      render: (p) => (
        <div className="flex justify-end gap-2">
          <Button size="sm" variant="ghost" onClick={() => handleEdit(p)}>
            {p.es_sistema ? 'Ver' : 'Editar'}
          </Button>
          {!p.es_sistema ? (
            <Button size="sm" variant="danger" onClick={() => handleDelete(p)}>
              Eliminar
            </Button>
          ) : null}
        </div>
      ),
    },
  ], [handleEdit, handleDelete]);

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold text-text-primary">Perfiles Dieteticos</h1>
          <p className="mt-1 text-sm text-text-secondary">
            Gestiona los perfiles dieteticos para clasificar productos
          </p>
        </div>
        <div className="flex items-center gap-3">
          <HelpButton content={helpContent.dietaryProfiles} />
          <Button onClick={handleCreate}>Crear perfil</Button>
        </div>
      </div>

      {!crud.isLoading && crud.items.length === 0 && !crud.error ? (
        <EmptyState
          title="No hay perfiles dieteticos"
          description="Los perfiles del sistema se cargan automaticamente."
          actionLabel="Crear perfil personalizado"
          onAction={handleCreate}
        />
      ) : (
        <>
          <div className="rounded-xl bg-bg-surface border border-border-default overflow-hidden">
            <Table
              columns={columns}
              data={crud.items}
              keyExtractor={(p) => p.id}
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
        title={editingProfile ? (editingProfile.es_sistema ? 'Ver perfil' : 'Editar perfil') : 'Crear perfil dietetico'}
      >
        <DietaryProfileForm
          key={editingProfile?.id ?? 'new'}
          profile={editingProfile}
          onSuccess={handleFormSuccess}
          onCancel={handleFormCancel}
          createFn={crud.create}
          updateFn={crud.update}
        />
      </Modal>
    </div>
  );
}
