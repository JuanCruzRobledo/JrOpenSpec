/**
 * Seals CRUD page — tenant-scoped.
 * System seals (6 predefined) are read-only.
 */
import { useState, useMemo, useCallback } from 'react';
import { Table, type TableColumn } from '@/components/ui/Table';
import { Pagination } from '@/components/ui/Pagination';
import { Button } from '@/components/ui/Button';
import { Badge } from '@/components/ui/Badge';
import { Modal } from '@/components/ui/Modal';
import { EmptyState } from '@/components/ui/EmptyState';
import { HelpButton } from '@/components/ui/HelpButton';
import { SealForm } from '@/components/forms/SealForm';
import { useCrud } from '@/hooks/useCrud';
import { useConfirm } from '@/hooks/useConfirm';
import { sealService } from '@/services/seal.service';
import { helpContent } from '@/utils/helpContent';
import type { Seal, SealCreate, SealUpdate } from '@/types/seal';

export default function SealsPage() {
  const confirm = useConfirm();

  const [isModalOpen, setIsModalOpen] = useState(false);
  const [editingSeal, setEditingSeal] = useState<Seal | null>(null);

  const crud = useCrud<Seal, SealCreate, SealUpdate>({
    fetchFn: (params) => sealService.list(params),
    createFn: (data) => sealService.create(data),
    updateFn: (id, data) => sealService.update(id, data),
    deleteFn: (id) => sealService.remove(id),
    entityName: 'Sello',
  });

  const handleCreate = useCallback(() => {
    setEditingSeal(null);
    setIsModalOpen(true);
  }, []);

  const handleEdit = useCallback((seal: Seal) => {
    setEditingSeal(seal);
    setIsModalOpen(true);
  }, []);

  const handleDelete = useCallback(async (seal: Seal) => {
    if (seal.es_sistema) return;

    const confirmed = await confirm({
      title: `Eliminar sello "${seal.nombre}"?`,
      description: 'El sello sera eliminado de todos los productos asociados.',
      confirmLabel: 'Eliminar',
      variant: 'danger',
    });

    if (confirmed) {
      await crud.remove(seal.id);
    }
  }, [confirm, crud]);

  const handleFormSuccess = useCallback(() => {
    setIsModalOpen(false);
    setEditingSeal(null);
    crud.refresh();
  }, [crud]);

  const handleFormCancel = useCallback(() => {
    setIsModalOpen(false);
    setEditingSeal(null);
  }, []);

  const columns: TableColumn<Seal>[] = useMemo(() => [
    {
      key: 'preview',
      header: 'Vista previa',
      className: 'w-40',
      render: (s) => (
        <span
          className="inline-flex items-center gap-1 rounded-full px-2.5 py-0.5 text-xs font-medium text-white"
          style={{ backgroundColor: s.color }}
        >
          {s.icono ? <span>{s.icono}</span> : null}
          {s.nombre}
        </span>
      ),
    },
    {
      key: 'nombre',
      header: 'Nombre',
      render: (s) => <span className="font-medium">{s.nombre}</span>,
    },
    {
      key: 'codigo',
      header: 'Codigo',
      render: (s) => (
        <span className="text-xs text-text-secondary font-mono">{s.codigo}</span>
      ),
    },
    {
      key: 'color',
      header: 'Color',
      className: 'w-28',
      render: (s) => (
        <div className="flex items-center gap-2">
          <div
            className="h-5 w-5 rounded border border-border-default"
            style={{ backgroundColor: s.color }}
          />
          <span className="text-xs font-mono text-text-secondary">{s.color}</span>
        </div>
      ),
    },
    {
      key: 'tipo',
      header: 'Tipo',
      render: (s) => (
        <Badge variant={s.es_sistema ? 'info' : 'default'}>
          {s.es_sistema ? 'Sistema' : 'Personalizado'}
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
            {s.es_sistema ? 'Ver' : 'Editar'}
          </Button>
          {!s.es_sistema ? (
            <Button size="sm" variant="danger" onClick={() => handleDelete(s)}>
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
          <h1 className="text-2xl font-bold text-text-primary">Sellos</h1>
          <p className="mt-1 text-sm text-text-secondary">
            Sellos de calidad y certificacion para productos
          </p>
        </div>
        <div className="flex items-center gap-3">
          <HelpButton content={helpContent.seals} />
          <Button onClick={handleCreate}>Crear sello</Button>
        </div>
      </div>

      {!crud.isLoading && crud.items.length === 0 && !crud.error ? (
        <EmptyState
          title="No hay sellos"
          description="Los sellos del sistema se cargan automaticamente."
          actionLabel="Crear sello personalizado"
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
        title={editingSeal ? (editingSeal.es_sistema ? 'Ver sello' : 'Editar sello') : 'Crear sello'}
      >
        <SealForm
          key={editingSeal?.id ?? 'new'}
          seal={editingSeal}
          onSuccess={handleFormSuccess}
          onCancel={handleFormCancel}
          createFn={crud.create}
          updateFn={crud.update}
        />
      </Modal>
    </div>
  );
}
