/**
 * Badges CRUD page — tenant-scoped.
 * System badges (4 predefined) are read-only.
 */
import { useState, useMemo, useCallback } from 'react';
import { Table, type TableColumn } from '@/components/ui/Table';
import { Pagination } from '@/components/ui/Pagination';
import { Button } from '@/components/ui/Button';
import { Badge as BadgeUI } from '@/components/ui/Badge';
import { Modal } from '@/components/ui/Modal';
import { EmptyState } from '@/components/ui/EmptyState';
import { HelpButton } from '@/components/ui/HelpButton';
import { BadgeForm } from '@/components/forms/BadgeForm';
import { useCrud } from '@/hooks/useCrud';
import { useConfirm } from '@/hooks/useConfirm';
import { badgeService } from '@/services/badge.service';
import { helpContent } from '@/utils/helpContent';
import type { Badge, BadgeCreate, BadgeUpdate } from '@/types/badge';

export default function BadgesPage() {
  const confirm = useConfirm();

  const [isModalOpen, setIsModalOpen] = useState(false);
  const [editingBadge, setEditingBadge] = useState<Badge | null>(null);

  const crud = useCrud<Badge, BadgeCreate, BadgeUpdate>({
    fetchFn: (params) => badgeService.list(params),
    createFn: (data) => badgeService.create(data),
    updateFn: (id, data) => badgeService.update(id, data),
    deleteFn: (id) => badgeService.remove(id),
    entityName: 'Badge',
  });

  const handleCreate = useCallback(() => {
    setEditingBadge(null);
    setIsModalOpen(true);
  }, []);

  const handleEdit = useCallback((badge: Badge) => {
    setEditingBadge(badge);
    setIsModalOpen(true);
  }, []);

  const handleDelete = useCallback(async (badge: Badge) => {
    if (badge.es_sistema) return;

    const confirmed = await confirm({
      title: `Eliminar badge "${badge.nombre}"?`,
      description: 'El badge sera eliminado de todos los productos asociados.',
      confirmLabel: 'Eliminar',
      variant: 'danger',
    });

    if (confirmed) {
      await crud.remove(badge.id);
    }
  }, [confirm, crud]);

  const handleFormSuccess = useCallback(() => {
    setIsModalOpen(false);
    setEditingBadge(null);
    crud.refresh();
  }, [crud]);

  const handleFormCancel = useCallback(() => {
    setIsModalOpen(false);
    setEditingBadge(null);
  }, []);

  const columns: TableColumn<Badge>[] = useMemo(() => [
    {
      key: 'preview',
      header: 'Vista previa',
      className: 'w-40',
      render: (b) => (
        <span
          className="inline-flex items-center gap-1 rounded-full px-2.5 py-0.5 text-xs font-medium text-white"
          style={{ backgroundColor: b.color }}
        >
          {b.icono ? <span>{b.icono}</span> : null}
          {b.nombre}
        </span>
      ),
    },
    {
      key: 'nombre',
      header: 'Nombre',
      render: (b) => <span className="font-medium">{b.nombre}</span>,
    },
    {
      key: 'codigo',
      header: 'Codigo',
      render: (b) => (
        <span className="text-xs text-text-secondary font-mono">{b.codigo}</span>
      ),
    },
    {
      key: 'color',
      header: 'Color',
      className: 'w-28',
      render: (b) => (
        <div className="flex items-center gap-2">
          <div
            className="h-5 w-5 rounded border border-border-default"
            style={{ backgroundColor: b.color }}
          />
          <span className="text-xs font-mono text-text-secondary">{b.color}</span>
        </div>
      ),
    },
    {
      key: 'tipo',
      header: 'Tipo',
      render: (b) => (
        <BadgeUI variant={b.es_sistema ? 'info' : 'default'}>
          {b.es_sistema ? 'Sistema' : 'Personalizado'}
        </BadgeUI>
      ),
    },
    {
      key: 'acciones',
      header: 'Acciones',
      className: 'text-right',
      render: (b) => (
        <div className="flex justify-end gap-2">
          <Button size="sm" variant="ghost" onClick={() => handleEdit(b)}>
            {b.es_sistema ? 'Ver' : 'Editar'}
          </Button>
          {!b.es_sistema ? (
            <Button size="sm" variant="danger" onClick={() => handleDelete(b)}>
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
          <h1 className="text-2xl font-bold text-text-primary">Badges</h1>
          <p className="mt-1 text-sm text-text-secondary">
            Etiquetas visuales para destacar productos en el menu
          </p>
        </div>
        <div className="flex items-center gap-3">
          <HelpButton content={helpContent.badges} />
          <Button onClick={handleCreate}>Crear badge</Button>
        </div>
      </div>

      {!crud.isLoading && crud.items.length === 0 && !crud.error ? (
        <EmptyState
          title="No hay badges"
          description="Los badges del sistema se cargan automaticamente."
          actionLabel="Crear badge personalizado"
          onAction={handleCreate}
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
        title={editingBadge ? (editingBadge.es_sistema ? 'Ver badge' : 'Editar badge') : 'Crear badge'}
      >
        <BadgeForm
          key={editingBadge?.id ?? 'new'}
          badge={editingBadge}
          onSuccess={handleFormSuccess}
          onCancel={handleFormCancel}
          createFn={crud.create}
          updateFn={crud.update}
        />
      </Modal>
    </div>
  );
}
