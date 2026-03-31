/**
 * StaffSearch — search bar with debounce (300ms) + role filter dropdown.
 * Presentational: receives state and callbacks as props.
 */
import { Input } from '@/components/ui/Input';
import { Select } from '@/components/ui/Select';

const ROLE_FILTER_OPTIONS = [
  { value: 'OWNER', label: 'Propietario' },
  { value: 'ADMIN', label: 'Administrador' },
  { value: 'MANAGER', label: 'Gerente' },
  { value: 'WAITER', label: 'Mozo' },
  { value: 'CHEF', label: 'Chef' },
  { value: 'CASHIER', label: 'Cajero' },
];

interface Props {
  searchQuery: string;
  roleFilter: string | null;
  onSearchChange: (query: string) => void;
  onRoleChange: (role: string | null) => void;
}

export function StaffSearch({ searchQuery, roleFilter, onSearchChange, onRoleChange }: Props) {
  return (
    <div className="flex flex-wrap items-end gap-4 mb-6">
      <div className="w-64">
        <Input
          label="Buscar personal"
          placeholder="Nombre o email..."
          value={searchQuery}
          onChange={(e) => onSearchChange(e.target.value)}
        />
      </div>

      <div className="w-48">
        <Select
          label="Rol"
          options={ROLE_FILTER_OPTIONS}
          placeholder="Todos los roles"
          value={roleFilter ?? ''}
          onChange={(e) => {
            const val = e.target.value;
            onRoleChange(val || null);
          }}
        />
      </div>
    </div>
  );
}
