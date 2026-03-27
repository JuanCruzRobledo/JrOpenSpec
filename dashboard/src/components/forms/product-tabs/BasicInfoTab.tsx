/**
 * Basic product info tab — name, description, category, price, etc.
 * Uses useActionState per React 19 pattern.
 */
import { useActionState, useCallback, useState, useMemo } from 'react';
import { Input } from '@/components/ui/Input';
import { Textarea } from '@/components/ui/Textarea';
import { Select } from '@/components/ui/Select';
import { Button } from '@/components/ui/Button';
import { useToast } from '@/hooks/useToast';
import { logger } from '@/lib/logger';
import type { Category } from '@/types/category';
import type { Subcategory } from '@/types/subcategory';
import type { Product, ProductCreate, ProductUpdate } from '@/types/product';

interface FormState {
  isSuccess: boolean;
  errors: Record<string, string>;
  message?: string;
}

interface Props {
  product: Product | null;
  categories: Category[];
  subcategories: Subcategory[];
  onSuccess: (product: Product | null) => void;
  onCancel: () => void;
  createFn: (data: ProductCreate) => Promise<Product | null>;
  updateFn: (id: number, data: ProductUpdate) => Promise<Product | null>;
}

export function BasicInfoTab({
  product,
  categories,
  subcategories,
  onSuccess,
  onCancel,
  createFn,
  updateFn,
}: Props) {
  const toast = useToast();
  const isEditing = product !== null;

  const [selectedCategoryId, setSelectedCategoryId] = useState<number | null>(
    product?.categoria_id ?? null,
  );
  const [descripcion, setDescripcion] = useState(product?.descripcion ?? '');
  const [precioDisplay, setPrecioDisplay] = useState(
    product ? (product.precio / 100).toFixed(2) : '',
  );

  const categoryOptions = categories
    .filter((c) => !c.es_home)
    .map((c) => ({ value: c.id, label: c.nombre }));

  const filteredSubcategoryOptions = useMemo(() => {
    if (!selectedCategoryId) return [];
    return subcategories
      .filter((s) => s.categoria_id === selectedCategoryId)
      .map((s) => ({ value: s.id, label: s.nombre }));
  }, [subcategories, selectedCategoryId]);

  const submitAction = useCallback(
    async (_prevState: FormState, formData: FormData): Promise<FormState> => {
      const nombre = formData.get('nombre') as string;
      const desc = formData.get('descripcion') as string;
      const categoria_id_str = formData.get('categoria_id') as string;
      const categoria_id = categoria_id_str ? parseInt(categoria_id_str, 10) : 0;
      const subcategoria_id_str = formData.get('subcategoria_id') as string;
      const subcategoria_id = subcategoria_id_str ? parseInt(subcategoria_id_str, 10) : null;
      const precio_str = formData.get('precio') as string;
      const precio_pesos = parseFloat(precio_str);
      const imagen_url = (formData.get('imagen_url') as string) || null;
      const destacado = formData.get('destacado') === 'on';
      const popular = formData.get('popular') === 'on';
      const estado = formData.get('estado') === 'on' ? 'activo' as const : 'inactivo' as const;

      const errors: Record<string, string> = {};
      if (!nombre || nombre.trim().length < 2) {
        errors.nombre = 'El nombre debe tener al menos 2 caracteres';
      }
      if (nombre && nombre.trim().length > 100) {
        errors.nombre = 'El nombre no puede superar los 100 caracteres';
      }
      if (desc && desc.length > 500) {
        errors.descripcion = 'La descripcion no puede superar los 500 caracteres';
      }
      if (!categoria_id) {
        errors.categoria_id = 'Selecciona una categoria';
      }
      if (isNaN(precio_pesos) || precio_pesos < 0) {
        errors.precio = 'Ingresa un precio valido';
      }

      if (Object.keys(errors).length > 0) {
        return { isSuccess: false, errors };
      }

      const precio = Math.round(precio_pesos * 100);

      try {
        const data: ProductCreate = {
          nombre,
          descripcion: desc || null,
          categoria_id,
          subcategoria_id,
          precio,
          imagen_url,
          destacado,
          popular,
          estado,
        };

        let result: Product | null;
        if (isEditing && product) {
          result = await updateFn(product.id, data);
        } else {
          result = await createFn(data);
        }

        onSuccess(result);
        return { isSuccess: true, errors: {} };
      } catch (err) {
        const message = err instanceof Error ? err.message : 'Error al guardar';
        logger.error('Failed to save product', err);
        toast.error(message);
        return { isSuccess: false, errors: {}, message };
      }
    },
    [product, isEditing, createFn, updateFn, onSuccess, toast],
  );

  const [state, formAction, isPending] = useActionState<FormState, FormData>(
    submitAction,
    { isSuccess: false, errors: {} },
  );

  return (
    <form action={formAction}>
      <div className="space-y-4">
        <Input
          name="nombre"
          label="Nombre"
          isRequired
          defaultValue={product?.nombre ?? ''}
          error={state.errors.nombre}
          placeholder="Nombre del producto"
          disabled={isPending}
        />

        <Textarea
          name="descripcion"
          label="Descripcion"
          value={descripcion}
          onChange={(e) => setDescripcion(e.target.value)}
          error={state.errors.descripcion}
          placeholder="Descripcion del producto (opcional)"
          maxLength={500}
          showCount
          disabled={isPending}
        />

        <Select
          name="categoria_id"
          label="Categoria"
          isRequired
          options={categoryOptions}
          placeholder="Seleccionar categoria"
          defaultValue={product?.categoria_id?.toString() ?? ''}
          error={state.errors.categoria_id}
          disabled={isPending}
          onChange={(e) => {
            const val = e.target.value;
            setSelectedCategoryId(val ? parseInt(val, 10) : null);
          }}
        />

        <Select
          name="subcategoria_id"
          label="Subcategoria"
          options={filteredSubcategoryOptions}
          placeholder={selectedCategoryId ? 'Seleccionar subcategoria (opcional)' : 'Selecciona una categoria primero'}
          defaultValue={product?.subcategoria_id?.toString() ?? ''}
          disabled={isPending || !selectedCategoryId}
        />

        <Input
          name="precio"
          label="Precio base (en pesos)"
          isRequired
          type="number"
          step="0.01"
          min="0"
          value={precioDisplay}
          onChange={(e) => setPrecioDisplay(e.target.value)}
          error={state.errors.precio}
          placeholder="2500.00"
          disabled={isPending}
        />

        <Input
          name="imagen_url"
          label="Imagen URL"
          defaultValue={product?.imagen_url ?? ''}
          placeholder="https://ejemplo.com/imagen.jpg"
          disabled={isPending}
        />

        <div className="flex flex-wrap gap-6">
          <div className="flex items-center gap-3">
            <input
              type="checkbox"
              id="product-destacado"
              name="destacado"
              defaultChecked={product?.destacado ?? false}
              className="h-4 w-4 rounded border-border-default bg-bg-surface text-accent focus:ring-accent"
              disabled={isPending}
            />
            <label htmlFor="product-destacado" className="text-sm text-text-secondary">
              Destacado
            </label>
          </div>

          <div className="flex items-center gap-3">
            <input
              type="checkbox"
              id="product-popular"
              name="popular"
              defaultChecked={product?.popular ?? false}
              className="h-4 w-4 rounded border-border-default bg-bg-surface text-accent focus:ring-accent"
              disabled={isPending}
            />
            <label htmlFor="product-popular" className="text-sm text-text-secondary">
              Popular
            </label>
          </div>

          <div className="flex items-center gap-3">
            <input
              type="checkbox"
              id="product-estado"
              name="estado"
              defaultChecked={product ? product.estado === 'activo' : true}
              className="h-4 w-4 rounded border-border-default bg-bg-surface text-accent focus:ring-accent"
              disabled={isPending}
            />
            <label htmlFor="product-estado" className="text-sm text-text-secondary">
              Activo
            </label>
          </div>
        </div>
      </div>

      {state.message && !state.isSuccess ? (
        <p className="mt-4 text-sm text-error">{state.message}</p>
      ) : null}

      <div className="mt-6 flex justify-end gap-3">
        <Button type="button" variant="secondary" onClick={onCancel} disabled={isPending}>
          Cancelar
        </Button>
        <Button type="submit" isLoading={isPending}>
          {isEditing ? 'Guardar' : 'Crear producto'}
        </Button>
      </div>
    </form>
  );
}
