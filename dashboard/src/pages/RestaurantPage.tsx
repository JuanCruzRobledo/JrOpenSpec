/**
 * Restaurant configuration page — edit-only.
 * Loads current restaurant config and allows editing.
 */
import { RestaurantForm } from '@/components/forms/RestaurantForm';
import { HelpButton } from '@/components/ui/HelpButton';
import { helpContent } from '@/utils/helpContent';

export default function RestaurantPage() {
  return (
    <div className="max-w-3xl">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold text-text-primary">Configuracion del Restaurante</h1>
          <p className="mt-1 text-sm text-text-secondary">
            Edita la informacion general de tu restaurante
          </p>
        </div>
        <HelpButton content={helpContent.restaurant} />
      </div>

      <div className="rounded-xl bg-bg-surface border border-border-default p-6">
        <RestaurantForm />
      </div>
    </div>
  );
}
