/**
 * Categories CRUD page — scoped to selected branch.
 * Filters out Home category (es_home=true).
 */
import { useState, useMemo, useCallback } from 'react';
import { Table, type TableColumn } from '@/components/ui/Table';
import { Pagination } from '@/components/ui/Pagination';
import { Button } from '@/components/ui/Button';
import { Badge } from '@/components/ui/Badge';
import { Modal } from '@/components/ui/Modal';
import { EmptyState } from '@/components/ui/EmptyState';
import { HelpButton } from '@/components/ui/HelpButton';
import { CategoryForm } from '@/components/forms/CategoryForm';
import { useCrud } from '@/hooks/useCrud';
import { useConfirm } from '@/hooks/useConfirm';
import { useBranch } from '@/hooks/useBranch';
import { categoryService } from '@/services/category.service';
import { helpContent } from '@/utils/helpContent';
import type { Category, CategoryCreate, CategoryUpdate } from '@/types/category';

export default function CategoriesPage() {
  const { selectedBranchId } = useBranch();
  const confirm = useConfirm();
  const branchId = selectedBranchId!; // BranchGuard ensures this is non-null

  const [isModalOpen, setIsModalOpen] = useState(false);
  const [editingCategory, setEditingCategory] = useState<Category | null>(null);

  const crud = useCrud<Category, CategoryCreate, CategoryUpdate>({
    fetchFn: (params) => categoryService.list(branchId, params),
    createFn: (data) => categoryService.create(branchId, data),
    updateFn: (id, data) => categoryService.update(branchId, id, data),
    deleteFn: (id) => categoryService.remove(branchId, id),
    entityName: 'Categoria',
  });

  // Filter out Home category from display
  const visibleCategories = useMemo(
    () => crud.items.filter((c) => !c.es_home),
    [crud.items],
  );

  const handleCreate = useCallback(() => {
    setEditingCategory(null);
    setIsModalOpen(true);
  }, []);

  const handleEdit = useCallback((category: Category) => {
    setEditingCategory(category);
    setIsModalOpen(true);
  }, []);

  const handleDelete = useCallback(async (category: Category) => {
    const confirmed = await confirm({
      title: `Eliminar categoria "${category.nombre}"?`,
      description: 'Se eliminaran todas las subcategorias y productos de esta categoria. Esta accion no se puede deshacer.',
      confirmLabel: 'Eliminar',
      variant: 'danger',
    });

    if (confirmed) {
      await crud.remove(category.id);
    }
  }, [confirm, crud]);

  const handleFormSuccess = useCallback(() => {
    setIsModalOpen(false);
    setEditingCategory(null);
    crud.refresh();
  }, [crud]);

  const handleFormCancel = useCallback(() => {
    setIsModalOpen(false);
    setEditingCategory(null);
  }, []);

  const columns: TableColumn<Category>[] = useMemo(() => [
    {
      key: 'icono',
      header: 'Icono',
      className: 'w-16',
      render: (c) => (
        <span className="text-xl">{c.icono ?? '—'}</span>
      ),
    },
    {
      key: 'nombre',
      header: 'Nombre',
      render: (c) => <span className="font-medium">{c.nombre}</span>,
    },
    {
      key: 'orden',
      header: 'Orden',
      className: 'w-20',
      render: (c) => c.orden,
    },
    {
      key: 'estado',
      header: 'Estado',
      render: (c) => (
        <Badge variant={c.estado === 'activo' ? 'success' : 'default'}>
          {c.estado === 'activo' ? 'Activo' : 'Inactivo'}
        </Badge>
      ),
    },
    {
      key: 'acciones',
      header: 'Acciones',
      className: 'text-right',
      render: (c) => (
        <div className="flex justify-end gap-2">
          <Button size="sm" variant="ghost" onClick={() => handleEdit(c)}>
            Editar
          </Button>
          <Button size="sm" variant="danger" onClick={() => handleDelete(c)}>
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
          <h1 className="text-2xl font-bold text-text-primary">Categorias</h1>
          <p className="mt-1 text-sm text-text-secondary">
            Organiza el menu de tu sucursal en categorias
          </p>
        </div>
        <div className="flex items-center gap-3">
          <HelpButton content={helpContent.categories} />
          <Button onClick={handleCreate}>Crear categoria</Button>
        </div>
      </div>

      {!crud.isLoading && visibleCategories.length === 0 && !crud.error ? (
        <EmptyState
          title="No hay categorias"
          description="Crea tu primera categoria para organizar el menu."
          actionLabel="Crear categoria"
          onAction={handleCreate}
        />
      ) : (
        <>
          <div className="rounded-xl bg-bg-surface border border-border-default overflow-hidden">
            <Table
              columns={columns}
              data={visibleCategories}
              keyExtractor={(c) => c.id}
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
        title={editingCategory ? 'Editar categoria' : 'Crear categoria'}
      >
        <CategoryForm
          key={editingCategory?.id ?? 'new'}
          category={editingCategory}
          onSuccess={handleFormSuccess}
          onCancel={handleFormCancel}
          createFn={crud.create}
          updateFn={crud.update}
        />
      </Modal>
    </div>
  );
}
