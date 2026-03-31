/**
 * PermissionsMatrix — read-only table showing permissions per role.
 * Rows = permissions (union of all), columns = roles, cells = checkmark.
 * Presentational: receives RolesMatrix as prop.
 */
import { useMemo } from 'react';
import { cn } from '@/lib/cn';
import type { RolesMatrix } from '@/types/role';

interface Props {
  matrix: RolesMatrix;
}

function CheckIcon() {
  return (
    <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round" className="text-green-500">
      <polyline points="20 6 9 17 4 12" />
    </svg>
  );
}

export function PermissionsMatrix({ matrix }: Props) {
  // Collect all unique permissions across all roles
  const allPermissions = useMemo(() => {
    const set = new Set<string>();
    for (const role of matrix.roles) {
      for (const perm of role.permisos) {
        set.add(perm);
      }
    }
    return Array.from(set).sort();
  }, [matrix]);

  // Build a lookup: role -> Set<permission> for O(1) checks
  const permissionsByRole = useMemo(() => {
    const map = new Map<string, Set<string>>();
    for (const role of matrix.roles) {
      map.set(role.rol, new Set(role.permisos));
    }
    return map;
  }, [matrix]);

  if (matrix.roles.length === 0) {
    return (
      <p className="text-sm text-text-secondary">No hay roles configurados.</p>
    );
  }

  return (
    <div className="overflow-x-auto rounded-xl border border-border-default">
      <table className="w-full text-sm">
        <thead>
          <tr className="bg-bg-elevated">
            <th className="text-left px-4 py-3 font-medium text-text-primary border-b border-border-default sticky left-0 bg-bg-elevated z-10">
              Permiso
            </th>
            {matrix.roles.map((role) => (
              <th
                key={role.rol}
                className="text-center px-4 py-3 font-medium text-text-primary border-b border-border-default whitespace-nowrap"
              >
                {role.etiqueta}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {allPermissions.map((perm, i) => (
            <tr
              key={perm}
              className={cn(
                'border-b border-border-default last:border-b-0',
                i % 2 === 0 ? 'bg-bg-surface' : 'bg-bg-primary',
              )}
            >
              <td className="px-4 py-2.5 text-text-secondary font-mono text-xs sticky left-0 z-10 bg-inherit">
                {perm}
              </td>
              {matrix.roles.map((role) => (
                <td key={role.rol} className="text-center px-4 py-2.5">
                  {permissionsByRole.get(role.rol)?.has(perm) ? (
                    <div className="flex justify-center">
                      <CheckIcon />
                    </div>
                  ) : null}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
