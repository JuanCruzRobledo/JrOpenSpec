/**
 * Allergens CRUD page — tenant-scoped.
 * System allergens (EU 14) are read-only.
 */
import { useState, useMemo, useCallback } from 'react';
import { Table, type TableColumn } from '@/components/ui/Table';
import { Pagination } from '@/components/ui/Pagination';
import { Button } from '@/components/ui/Button';
import { Badge } from '@/components/ui/Badge';
import { Modal } from '@/components/ui/Modal';
import { EmptyState } from '@/components/ui/EmptyState';
import { HelpButton } from '@/components/ui/HelpButton';
import { AllergenForm } from '@/components/forms/AllergenForm';
import { useCrud } from '@/hooks/useCrud';
import { useConfirm } from '@/hooks/useConfirm';
import { allergenService } from '@/services/allergen.service';
import { helpContent } from '@/utils/helpContent';
import type { Allergen, AllergenCreate, AllergenUpdate } from '@/types/allergen';

export default function AllergensPage() {
  const confirm = useConfirm();

  const [isModalOpen, setIsModalOpen] = useState(false);
  const [editingAllergen, setEditingAllergen] = useState<Allergen | null>(null);

  const crud = useCrud<Allergen, AllergenCreate, AllergenUpdate>({
    fetchFn: (params) => allergenService.list(params),
    createFn: (data) => allergenService.create(data),
    updateFn: (id, data) => allergenService.update(id, data),
    deleteFn: (id) => allergenService.remove(id),
    entityName: 'Alergeno',
  });

  const handleCreate = useCallback(() => {
    setEditingAllergen(null);
    setIsModalOpen(true);
  }, []);

  const handleEdit = useCallback((allergen: Allergen) => {
    setEditingAllergen(allergen);
    setIsModalOpen(true);
  }, []);

  const handleDelete = useCallback(async (allergen: Allergen) => {
    if (allergen.es_sistema) return;

    const confirmed = await confirm({
      title: `Eliminar alergeno "${allergen.nombre}"?`,
      description: 'El alergeno sera eliminado. Los productos asociados perderan esta referencia.',
      confirmLabel: 'Eliminar',
      variant: 'danger',
    });

    if (confirmed) {
      await crud.remove(allergen.id);
    }
  }, [confirm, crud]);

  const handleFormSuccess = useCallback(() => {
    setIsModalOpen(false);
    setEditingAllergen(null);
    crud.refresh();
  }, [crud]);

  const handleFormCancel = useCallback(() => {
    setIsModalOpen(false);
    setEditingAllergen(null);
  }, []);

  const columns: TableColumn<Allergen>[] = useMemo(() => [
    {
      key: 'icono',
      header: 'Icono',
      className: 'w-16',
      render: (a) => (
        <span className="text-lg">{a.icono ?? '—'}</span>
      ),
    },
    {
      key: 'nombre',
      header: 'Nombre',
      render: (a) => <span className="font-medium">{a.nombre}</span>,
    },
    {
      key: 'codigo',
      header: 'Codigo',
      render: (a) => (
        <span className="text-xs text-text-secondary font-mono">{a.codigo}</span>
      ),
    },
    {
      key: 'tipo',
      header: 'Tipo',
      render: (a) => (
        <Badge variant={a.es_sistema ? 'info' : 'default'}>
          {a.es_sistema ? 'Sistema' : 'Personalizado'}
        </Badge>
      ),
    },
    {
      key: 'acciones',
      header: 'Acciones',
      className: 'text-right',
      render: (a) => (
        <div className="flex justify-end gap-2">
          <Button size="sm" variant="ghost" onClick={() => handleEdit(a)}>
            {a.es_sistema ? 'Ver' : 'Editar'}
          </Button>
          {!a.es_sistema ? (
            <Button size="sm" variant="danger" onClick={() => handleDelete(a)}>
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
          <h1 className="text-2xl font-bold text-text-primary">Alergenos</h1>
          <p className="mt-1 text-sm text-text-secondary">
            Gestiona los alergenos del sistema y personalizados
          </p>
        </div>
        <div className="flex items-center gap-3">
          <HelpButton content={helpContent.allergens} />
          <Button onClick={handleCreate}>Crear alergeno</Button>
        </div>
      </div>

      {!crud.isLoading && crud.items.length === 0 && !crud.error ? (
        <EmptyState
          title="No hay alergenos"
          description="Los alergenos del sistema se cargan automaticamente."
          actionLabel="Crear alergeno personalizado"
          onAction={handleCreate}
        />
      ) : (
        <>
          <div className="rounded-xl bg-bg-surface border border-border-default overflow-hidden">
            <Table
              columns={columns}
              data={crud.items}
              keyExtractor={(a) => a.id}
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
        title={editingAllergen ? (editingAllergen.es_sistema ? 'Ver alergeno' : 'Editar alergeno') : 'Crear alergeno'}
      >
        <AllergenForm
          key={editingAllergen?.id ?? 'new'}
          allergen={editingAllergen}
          onSuccess={handleFormSuccess}
          onCancel={handleFormCancel}
          createFn={crud.create}
          updateFn={crud.update}
        />
      </Modal>
    </div>
  );
}
