/**
 * RolesPage — shows read-only permissions matrix.
 * Fetches role permissions from the service.
 */
import { useState, useEffect, useCallback } from 'react';
import { Button } from '@/components/ui/Button';
import { Spinner } from '@/components/ui/Spinner';
import { HelpButton } from '@/components/ui/HelpButton';
import { PermissionsMatrix } from '@/components/roles/PermissionsMatrix';
import { roleService } from '@/services/role.service';
import { helpContent } from '@/utils/helpContent';
import { logger } from '@/lib/logger';
import type { RolesMatrix } from '@/types/role';

export default function RolesPage() {
  const [matrix, setMatrix] = useState<RolesMatrix | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchPermissions = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    try {
      const data = await roleService.getPermissions();
      setMatrix(data);
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Error al cargar permisos';
      setError(message);
      logger.error('Failed to fetch role permissions', err);
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchPermissions();
  }, [fetchPermissions]);

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold text-text-primary">Roles y Permisos</h1>
          <p className="mt-1 text-sm text-text-secondary">
            Visualiza la matriz de permisos por rol del sistema
          </p>
        </div>
        <HelpButton content={helpContent.roles} />
      </div>

      {isLoading ? (
        <div className="flex items-center justify-center py-16">
          <Spinner size="lg" />
        </div>
      ) : null}

      {error ? (
        <div className="text-center py-8">
          <p className="text-error mb-4">{error}</p>
          <Button variant="secondary" onClick={fetchPermissions}>
            Reintentar
          </Button>
        </div>
      ) : null}

      {matrix && !isLoading ? (
        <PermissionsMatrix matrix={matrix} />
      ) : null}
    </div>
  );
}
