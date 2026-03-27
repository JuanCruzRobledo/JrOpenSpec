/**
 * Products CRUD page — scoped to selected branch.
 * Prices displayed in pesos, sent to API in cents.
 */
import { useState, useMemo, useCallback, useEffect } from 'react';
import { Table, type TableColumn } from '@/components/ui/Table';
import { Pagination } from '@/components/ui/Pagination';
import { Button } from '@/components/ui/Button';
import { Badge } from '@/components/ui/Badge';
import { Modal } from '@/components/ui/Modal';
import { EmptyState } from '@/components/ui/EmptyState';
import { HelpButton } from '@/components/ui/HelpButton';
import { ProductForm } from '@/components/forms/ProductForm';
import { useCrud } from '@/hooks/useCrud';
import { useConfirm } from '@/hooks/useConfirm';
import { useBranch } from '@/hooks/useBranch';
import { productService } from '@/services/product.service';
import { categoryService } from '@/services/category.service';
import { subcategoryService } from '@/services/subcategory.service';
import { formatCurrency } from '@/lib/format';
import { logger } from '@/lib/logger';
import { helpContent } from '@/utils/helpContent';
import type { Product, ProductCreate, ProductUpdate } from '@/types/product';
import type { Category } from '@/types/category';
import type { Subcategory } from '@/types/subcategory';

export default function ProductsPage() {
  const { selectedBranchId } = useBranch();
  const confirm = useConfirm();
  const branchId = selectedBranchId!; // BranchGuard ensures this

  const [isModalOpen, setIsModalOpen] = useState(false);
  const [editingProduct, setEditingProduct] = useState<Product | null>(null);
  const [categories, setCategories] = useState<Category[]>([]);
  const [subcategories, setSubcategories] = useState<Subcategory[]>([]);

  // Load categories and subcategories for the product form dropdowns
  useEffect(() => {
    let isMounted = true;

    const loadRelated = async () => {
      try {
        const [catRes, subRes] = await Promise.all([
          categoryService.list(branchId, { page: 1, limit: 100 }),
          subcategoryService.list(branchId, { page: 1, limit: 200 }),
        ]);
        if (!isMounted) return;
        setCategories(catRes.data.filter((c) => !c.es_home));
        setSubcategories(subRes.data);
      } catch (err) {
        logger.error('Failed to load categories/subcategories for products page', err);
      }
    };

    loadRelated();
    return () => { isMounted = false; };
  }, [branchId]);

  const crud = useCrud<Product, ProductCreate, ProductUpdate>({
    fetchFn: (params) => productService.list(branchId, params),
    createFn: (data) => productService.create(branchId, data),
    updateFn: (id, data) => productService.update(branchId, id, data),
    deleteFn: (id) => productService.remove(branchId, id),
    entityName: 'Producto',
  });

  const handleCreate = useCallback(() => {
    setEditingProduct(null);
    setIsModalOpen(true);
  }, []);

  const handleEdit = useCallback((product: Product) => {
    setEditingProduct(product);
    setIsModalOpen(true);
  }, []);

  const handleDelete = useCallback(async (product: Product) => {
    const confirmed = await confirm({
      title: `Eliminar producto "${product.nombre}"?`,
      description: 'El producto sera eliminado permanentemente. Esta accion no se puede deshacer.',
      confirmLabel: 'Eliminar',
      variant: 'danger',
    });

    if (confirmed) {
      await crud.remove(product.id);
    }
  }, [confirm, crud]);

  const handleFormSuccess = useCallback(() => {
    setIsModalOpen(false);
    setEditingProduct(null);
    crud.refresh();
  }, [crud]);

  const handleFormCancel = useCallback(() => {
    setIsModalOpen(false);
    setEditingProduct(null);
  }, []);

  const columns: TableColumn<Product>[] = useMemo(() => [
    {
      key: 'nombre',
      header: 'Nombre',
      render: (p) => <span className="font-medium">{p.nombre}</span>,
    },
    {
      key: 'subcategoria',
      header: 'Categoria / Subcategoria',
      render: (p) => (
        <span className="text-text-secondary text-xs">
          {p.categoria_nombre ?? '—'}
          {p.subcategoria_nombre ? ` / ${p.subcategoria_nombre}` : ''}
        </span>
      ),
    },
    {
      key: 'precio',
      header: 'Precio',
      render: (p) => (
        <span className="font-medium text-accent">
          {formatCurrency(p.precio)}
        </span>
      ),
    },
    {
      key: 'estado',
      header: 'Estado',
      render: (p) => (
        <Badge variant={p.estado === 'activo' ? 'success' : 'default'}>
          {p.estado === 'activo' ? 'Activo' : 'Inactivo'}
        </Badge>
      ),
    },
    {
      key: 'destacado',
      header: 'Destacado',
      className: 'w-24 text-center',
      render: (p) => (
        <span className="text-lg" title={p.destacado ? 'Destacado' : ''}>
          {p.destacado ? '⭐' : ''}
        </span>
      ),
    },
    {
      key: 'popular',
      header: 'Popular',
      className: 'w-24 text-center',
      render: (p) => (
        <span className="text-lg" title={p.popular ? 'Popular' : ''}>
          {p.popular ? '🔥' : ''}
        </span>
      ),
    },
    {
      key: 'acciones',
      header: 'Acciones',
      className: 'text-right',
      render: (p) => (
        <div className="flex justify-end gap-2">
          <Button size="sm" variant="ghost" onClick={() => handleEdit(p)}>
            Editar
          </Button>
          <Button size="sm" variant="danger" onClick={() => handleDelete(p)}>
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
          <h1 className="text-2xl font-bold text-text-primary">Productos</h1>
          <p className="mt-1 text-sm text-text-secondary">
            Administra los productos de tu menu
          </p>
        </div>
        <div className="flex items-center gap-3">
          <HelpButton content={helpContent.products} />
          <Button onClick={handleCreate}>Crear producto</Button>
        </div>
      </div>

      {!crud.isLoading && crud.items.length === 0 && !crud.error ? (
        <EmptyState
          title="No hay productos"
          description="Crea tu primer producto para armarel menu."
          actionLabel="Crear producto"
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
        title={editingProduct ? 'Editar producto' : 'Crear producto'}
      >
        <ProductForm
          key={editingProduct?.id ?? 'new'}
          product={editingProduct}
          categories={categories}
          subcategories={subcategories}
          onSuccess={handleFormSuccess}
          onCancel={handleFormCancel}
          createFn={crud.create}
          updateFn={crud.update}
        />
      </Modal>
    </div>
  );
}
