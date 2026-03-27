import { useActionState, useCallback, useEffect, useState } from 'react';
import { Input } from '@/components/ui/Input';
import { Textarea } from '@/components/ui/Textarea';
import { Button } from '@/components/ui/Button';
import { Spinner } from '@/components/ui/Spinner';
import { useToast } from '@/hooks/useToast';
import { restaurantService } from '@/services/restaurant.service';
import { generateSlug } from '@/lib/slug';
import { logger } from '@/lib/logger';
import type { Restaurant, RestaurantUpdate } from '@/types/restaurant';

interface FormState {
  isSuccess: boolean;
  errors: Record<string, string>;
  message?: string;
}

interface Props {
  className?: string;
}

/**
 * Restaurant configuration form — edit-only (no create).
 * Uses useActionState for form handling per React 19 pattern.
 */
export function RestaurantForm({ className }: Props) {
  const toast = useToast();
  const [restaurant, setRestaurant] = useState<Restaurant | null>(null);
  const [isLoadingData, setIsLoadingData] = useState(true);
  const [loadError, setLoadError] = useState<string | null>(null);

  // Local controlled state for slug auto-generation
  const [nombre, setNombre] = useState('');
  const [slug, setSlug] = useState('');
  const [slugManuallyEdited, setSlugManuallyEdited] = useState(false);
  const [descripcion, setDescripcion] = useState('');

  // Load restaurant data on mount
  useEffect(() => {
    let isMounted = true;

    const load = async () => {
      try {
        const data = await restaurantService.getMe();
        if (!isMounted) return;
        setRestaurant(data);
        setNombre(data.nombre);
        setSlug(data.slug);
        setDescripcion(data.descripcion ?? '');
        setSlugManuallyEdited(true); // Don't override existing slug
      } catch (err) {
        if (!isMounted) return;
        const message = err instanceof Error ? err.message : 'Error al cargar datos';
        setLoadError(message);
        logger.error('Failed to load restaurant config', err);
      } finally {
        if (isMounted) setIsLoadingData(false);
      }
    };

    load();
    return () => { isMounted = false; };
  }, []);

  // Auto-generate slug from nombre
  const handleNombreChange = useCallback((value: string) => {
    setNombre(value);
    if (!slugManuallyEdited) {
      setSlug(generateSlug(value));
    }
  }, [slugManuallyEdited]);

  const handleSlugChange = useCallback((value: string) => {
    setSlug(value);
    setSlugManuallyEdited(true);
  }, []);

  const submitAction = useCallback(
    async (_prevState: FormState, formData: FormData): Promise<FormState> => {
      if (!restaurant) {
        return { isSuccess: false, errors: {}, message: 'No se pudo cargar el restaurante' };
      }

      const data: RestaurantUpdate = {
        nombre: formData.get('nombre') as string,
        slug: formData.get('slug') as string,
        descripcion: (formData.get('descripcion') as string) || null,
        logo_url: (formData.get('logo_url') as string) || null,
        banner_url: (formData.get('banner_url') as string) || null,
        telefono: (formData.get('telefono') as string) || null,
        email: (formData.get('email') as string) || null,
        direccion: (formData.get('direccion') as string) || null,
      };

      // Validation
      const errors: Record<string, string> = {};
      if (!data.nombre || data.nombre.trim().length < 2) {
        errors.nombre = 'El nombre debe tener al menos 2 caracteres';
      }
      if (!data.slug || data.slug.trim().length < 2) {
        errors.slug = 'El slug debe tener al menos 2 caracteres';
      }

      if (Object.keys(errors).length > 0) {
        return { isSuccess: false, errors };
      }

      try {
        const updated = await restaurantService.update(restaurant.id, data);
        setRestaurant(updated);
        toast.success('Configuracion guardada exitosamente');
        return { isSuccess: true, errors: {} };
      } catch (err) {
        const message = err instanceof Error ? err.message : 'Error al guardar';
        logger.error('Failed to update restaurant', err);
        toast.error(message);
        return { isSuccess: false, errors: {}, message };
      }
    },
    [restaurant, toast],
  );

  const [state, formAction, isPending] = useActionState<FormState, FormData>(
    submitAction,
    { isSuccess: false, errors: {} },
  );

  if (isLoadingData) {
    return (
      <div className="flex items-center justify-center py-16">
        <Spinner size="lg" />
      </div>
    );
  }

  if (loadError) {
    return (
      <div className="text-center py-16">
        <p className="text-error mb-4">{loadError}</p>
        <Button onClick={() => window.location.reload()}>Reintentar</Button>
      </div>
    );
  }

  return (
    <form action={formAction} className={className}>
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <Input
          name="nombre"
          label="Nombre"
          isRequired
          value={nombre}
          onChange={(e) => handleNombreChange(e.target.value)}
          error={state.errors.nombre}
          placeholder="Nombre del restaurante"
          disabled={isPending}
        />
        <Input
          name="slug"
          label="Slug (URL)"
          isRequired
          value={slug}
          onChange={(e) => handleSlugChange(e.target.value)}
          error={state.errors.slug}
          placeholder="mi-restaurante"
          disabled={isPending}
        />
      </div>

      <div className="mt-4">
        <Textarea
          name="descripcion"
          label="Descripcion"
          value={descripcion}
          onChange={(e) => setDescripcion(e.target.value)}
          placeholder="Descripcion del restaurante"
          maxLength={500}
          showCount
          disabled={isPending}
        />
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mt-4">
        <Input
          name="logo_url"
          label="Logo URL"
          defaultValue={restaurant?.logo_url ?? ''}
          placeholder="https://ejemplo.com/logo.png"
          disabled={isPending}
        />
        <Input
          name="banner_url"
          label="Banner URL"
          defaultValue={restaurant?.banner_url ?? ''}
          placeholder="https://ejemplo.com/banner.jpg"
          disabled={isPending}
        />
      </div>

      <h3 className="text-sm font-semibold text-text-secondary mt-6 mb-3 uppercase tracking-wider">
        Contacto
      </h3>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <Input
          name="telefono"
          label="Telefono"
          defaultValue={restaurant?.telefono ?? ''}
          placeholder="+54 9 261 555-1234"
          disabled={isPending}
        />
        <Input
          name="email"
          label="Email"
          type="email"
          defaultValue={restaurant?.email ?? ''}
          placeholder="contacto@restaurante.com"
          disabled={isPending}
        />
      </div>

      <div className="mt-4">
        <Input
          name="direccion"
          label="Direccion"
          defaultValue={restaurant?.direccion ?? ''}
          placeholder="Calle 123, Ciudad"
          disabled={isPending}
        />
      </div>

      {state.message && !state.isSuccess ? (
        <p className="mt-4 text-sm text-error">{state.message}</p>
      ) : null}

      <div className="mt-6 flex justify-end">
        <Button type="submit" isLoading={isPending}>
          Guardar cambios
        </Button>
      </div>
    </form>
  );
}
