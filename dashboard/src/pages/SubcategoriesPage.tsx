/**
 * Subcategories CRUD page — scoped to selected branch.
 * Filterable by parent category via dropdown.
 */
import { useState, useMemo, useCallback, useEffect } from 'react';
import { Table, type TableColumn } from '@/components/ui/Table';
import { Pagination } from '@/components/ui/Pagination';
import { Button } from '@/components/ui/Button';
import { Badge } from '@/components/ui/Badge';
import { Select } from '@/components/ui/Select';
import { Modal } from '@/components/ui/Modal';
import { EmptyState } from '@/components/ui/EmptyState';
import { HelpButton } from '@/components/ui/HelpButton';
import { SubcategoryForm } from '@/components/forms/SubcategoryForm';
import { useCrud } from '@/hooks/useCrud';
import { useConfirm } from '@/hooks/useConfirm';
import { useBranch } from '@/hooks/useBranch';
import { subcategoryService } from '@/services/subcategory.service';
import { categoryService } from '@/services/category.service';
import { logger } from '@/lib/logger';
import { helpContent } from '@/utils/helpContent';
import type { Subcategory, SubcategoryCreate, SubcategoryUpdate } from '@/types/subcategory';
import type { Category } from '@/types/category';

export default function SubcategoriesPage() {
  const { selectedBranchId } = useBranch();
  const confirm = useConfirm();
  const branchId = selectedBranchId!; // BranchGuard ensures this

  const [isModalOpen, setIsModalOpen] = useState(false);
  const [editingSubcategory, setEditingSubcategory] = useState<Subcategory | null>(null);
  const [categories, setCategories] = useState<Category[]>([]);
  const [filterCategoryId, setFilterCategoryId] = useState<number | null>(null);

  // Load categories for the dropdown filter and form
  useEffect(() => {
    let isMounted = true;

    const loadCategories = async () => {
      try {
        const res = await categoryService.list(branchId, { page: 1, limit: 100 });
        if (!isMounted) return;
        // Filter out Home category
        setCategories(res.data.filter((c) => !c.es_home));
      } catch (err) {
        logger.error('Failed to load categories for subcategories page', err);
      }
    };

    loadCategories();
    return () => { isMounted = false; };
  }, [branchId]);

  const crud = useCrud<Subcategory, SubcategoryCreate, SubcategoryUpdate>({
    fetchFn: (params) => {
      const extendedParams = filterCategoryId
        ? { ...params, category_id: filterCategoryId }
        : params;
      return subcategoryService.list(branchId, extendedParams);
    },
    createFn: (data) => subcategoryService.create(branchId, data),
    updateFn: (id, data) => subcategoryService.update(branchId, id, data),
    deleteFn: (id) => subcategoryService.remove(branchId, id),
    entityName: 'Subcategoria',
  });

  // Refresh when filter changes
  useEffect(() => {
    crud.refresh();
    // eslint-disable-next-line react-compiler/react-compiler
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [filterCategoryId]);

  const categoryFilterOptions = useMemo(() => [
    ...categories.map((c) => ({ value: c.id, label: c.nombre })),
  ], [categories]);

  const handleCreate = useCallback(() => {
    setEditingSubcategory(null);
    setIsModalOpen(true);
  }, []);

  const handleEdit = useCallback((subcategory: Subcategory) => {
    setEditingSubcategory(subcategory);
    setIsModalOpen(true);
  }, []);

  const handleDelete = useCallback(async (subcategory: Subcategory) => {
    const confirmed = await confirm({
      title: `Eliminar subcategoria "${subcategory.nombre}"?`,
      description: `Se eliminaran ${subcategory.productos_count} producto(s) de esta subcategoria. Esta accion no se puede deshacer.`,
      confirmLabel: 'Eliminar',
      variant: 'danger',
    });

    if (confirmed) {
      await crud.remove(subcategory.id);
    }
  }, [confirm, crud]);

  const handleFormSuccess = useCallback(() => {
    setIsModalOpen(false);
    setEditingSubcategory(null);
    crud.refresh();
  }, [crud]);

  const handleFormCancel = useCallback(() => {
    setIsModalOpen(false);
    setEditingSubcategory(null);
  }, []);

  const columns: TableColumn<Subcategory>[] = useMemo(() => [
    {
      key: 'nombre',
      header: 'Nombre',
      render: (s) => <span className="font-medium">{s.nombre}</span>,
    },
    {
      key: 'categoria',
      header: 'Categoria',
      render: (s) => (
        <span className="text-text-secondary">
          {s.categoria_nombre ?? '—'}
        </span>
      ),
    },
    {
      key: 'orden',
      header: 'Orden',
      className: 'w-20',
      render: (s) => s.orden,
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
      key: 'productos',
      header: 'Productos',
      className: 'w-24',
      render: (s) => (
        <span className="text-text-secondary">{s.productos_count}</span>
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
          <h1 className="text-2xl font-bold text-text-primary">Subcategorias</h1>
          <p className="mt-1 text-sm text-text-secondary">
            Organiza los productos dentro de cada categoria
          </p>
        </div>
        <div className="flex items-center gap-3">
          <HelpButton content={helpContent.subcategories} />
          <Button onClick={handleCreate}>Crear subcategoria</Button>
        </div>
      </div>

      {/* Category filter */}
      <div className="mb-4 max-w-xs">
        <Select
          options={categoryFilterOptions}
          placeholder="Todas las categorias"
          value={filterCategoryId?.toString() ?? ''}
          onChange={(e) => {
            const val = e.target.value;
            setFilterCategoryId(val ? parseInt(val, 10) : null);
          }}
        />
      </div>

      {!crud.isLoading && crud.items.length === 0 && !crud.error ? (
        <EmptyState
          title="No hay subcategorias"
          description="Crea tu primera subcategoria para organizar los productos."
          actionLabel="Crear subcategoria"
          onAction={handleCreate}
        />
      ) : (
        <>
          <div className="rounded-xl bg-bg-surface border border-border-default overflow-hidden">
            <Table
              columns={columns}
              data={crud.items}
              keyExtractor={(s) => s.id}
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
        title={editingSubcategory ? 'Editar subcategoria' : 'Crear subcategoria'}
      >
        <SubcategoryForm
          key={editingSubcategory?.id ?? 'new'}
          subcategory={editingSubcategory}
          categories={categories}
          onSuccess={handleFormSuccess}
          onCancel={handleFormCancel}
          createFn={crud.create}
          updateFn={crud.update}
        />
      </Modal>
    </div>
  );
}
