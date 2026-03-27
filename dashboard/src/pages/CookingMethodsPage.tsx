/**
 * Cooking Methods CRUD page — tenant-scoped.
 * System methods (10 predefined) are read-only.
 */
import { useState, useMemo, useCallback } from 'react';
import { Table, type TableColumn } from '@/components/ui/Table';
import { Pagination } from '@/components/ui/Pagination';
import { Button } from '@/components/ui/Button';
import { Badge } from '@/components/ui/Badge';
import { Modal } from '@/components/ui/Modal';
import { EmptyState } from '@/components/ui/EmptyState';
import { HelpButton } from '@/components/ui/HelpButton';
import { CookingMethodForm } from '@/components/forms/CookingMethodForm';
import { useCrud } from '@/hooks/useCrud';
import { useConfirm } from '@/hooks/useConfirm';
import { cookingMethodService } from '@/services/cooking-method.service';
import { helpContent } from '@/utils/helpContent';
import type {
  CookingMethod,
  CookingMethodCreate,
  CookingMethodUpdate,
} from '@/types/cooking-method';

export default function CookingMethodsPage() {
  const confirm = useConfirm();

  const [isModalOpen, setIsModalOpen] = useState(false);
  const [editingMethod, setEditingMethod] = useState<CookingMethod | null>(null);

  const crud = useCrud<CookingMethod, CookingMethodCreate, CookingMethodUpdate>({
    fetchFn: (params) => cookingMethodService.list(params),
    createFn: (data) => cookingMethodService.create(data),
    updateFn: (id, data) => cookingMethodService.update(id, data),
    deleteFn: (id) => cookingMethodService.remove(id),
    entityName: 'Metodo de coccion',
  });

  const handleCreate = useCallback(() => {
    setEditingMethod(null);
    setIsModalOpen(true);
  }, []);

  const handleEdit = useCallback((method: CookingMethod) => {
    setEditingMethod(method);
    setIsModalOpen(true);
  }, []);

  const handleDelete = useCallback(async (method: CookingMethod) => {
    if (method.es_sistema) return;

    const confirmed = await confirm({
      title: `Eliminar metodo "${method.nombre}"?`,
      description: 'El metodo sera eliminado. Los productos asociados perderan esta referencia.',
      confirmLabel: 'Eliminar',
      variant: 'danger',
    });

    if (confirmed) {
      await crud.remove(method.id);
    }
  }, [confirm, crud]);

  const handleFormSuccess = useCallback(() => {
    setIsModalOpen(false);
    setEditingMethod(null);
    crud.refresh();
  }, [crud]);

  const handleFormCancel = useCallback(() => {
    setIsModalOpen(false);
    setEditingMethod(null);
  }, []);

  const columns: TableColumn<CookingMethod>[] = useMemo(() => [
    {
      key: 'icono',
      header: 'Icono',
      className: 'w-16',
      render: (m) => (
        <span className="text-lg">{m.icono ?? '—'}</span>
      ),
    },
    {
      key: 'nombre',
      header: 'Nombre',
      render: (m) => <span className="font-medium">{m.nombre}</span>,
    },
    {
      key: 'codigo',
      header: 'Codigo',
      render: (m) => (
        <span className="text-xs text-text-secondary font-mono">{m.codigo}</span>
      ),
    },
    {
      key: 'tipo',
      header: 'Tipo',
      render: (m) => (
        <Badge variant={m.es_sistema ? 'info' : 'default'}>
          {m.es_sistema ? 'Sistema' : 'Personalizado'}
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
            {m.es_sistema ? 'Ver' : 'Editar'}
          </Button>
          {!m.es_sistema ? (
            <Button size="sm" variant="danger" onClick={() => handleDelete(m)}>
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
          <h1 className="text-2xl font-bold text-text-primary">Metodos de Coccion</h1>
          <p className="mt-1 text-sm text-text-secondary">
            Gestiona los metodos de coccion para clasificar productos
          </p>
        </div>
        <div className="flex items-center gap-3">
          <HelpButton content={helpContent.cookingMethods} />
          <Button onClick={handleCreate}>Crear metodo</Button>
        </div>
      </div>

      {!crud.isLoading && crud.items.length === 0 && !crud.error ? (
        <EmptyState
          title="No hay metodos de coccion"
          description="Los metodos del sistema se cargan automaticamente."
          actionLabel="Crear metodo personalizado"
          onAction={handleCreate}
        />
      ) : (
        <>
          <div className="rounded-xl bg-bg-surface border border-border-default overflow-hidden">
            <Table
              columns={columns}
              data={crud.items}
              keyExtractor={(m) => m.id}
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
        title={editingMethod ? (editingMethod.es_sistema ? 'Ver metodo' : 'Editar metodo') : 'Crear metodo de coccion'}
      >
        <CookingMethodForm
          key={editingMethod?.id ?? 'new'}
          method={editingMethod}
          onSuccess={handleFormSuccess}
          onCancel={handleFormCancel}
          createFn={crud.create}
          updateFn={crud.update}
        />
      </Modal>
    </div>
  );
}
