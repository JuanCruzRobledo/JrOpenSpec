import { Outlet } from 'react-router-dom';
import { useBranchStore } from '@/stores/branch.store';
import { Button } from '@/components/ui/Button';

interface Props {}

/**
 * Branch guard — requires a branch to be selected before
 * accessing menu-scoped routes (categories, subcategories, products).
 */
export function BranchGuard(_props: Props) {
  const selectedBranchId = useBranchStore((s) => s.selectedBranchId);

  if (!selectedBranchId) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[60vh] text-center">
        <div className="text-5xl mb-4">🏪</div>
        <h2 className="text-xl font-semibold text-text-primary">
          Selecciona una sucursal
        </h2>
        <p className="mt-2 text-sm text-text-secondary max-w-md">
          Para acceder a esta seccion, primero debes seleccionar una sucursal
          desde el selector en la barra superior.
        </p>
        <Button variant="secondary" className="mt-6" disabled>
          Seleccionar en la barra superior
        </Button>
      </div>
    );
  }

  return <Outlet />;
}
