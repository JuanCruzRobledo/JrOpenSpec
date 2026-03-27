import { useAuthStore } from '@/stores/auth.store';

interface Props {}

/**
 * Dashboard page — placeholder for sprint 3.
 * Will show stats, recent activity, etc. in future sprints.
 */
export default function DashboardPage(_props: Props) {
  const user = useAuthStore((s) => s.user);

  return (
    <div>
      <h1 className="text-2xl font-bold text-text-primary">Dashboard</h1>
      <p className="mt-2 text-text-secondary">
        Bienvenido{user ? `, ${user.first_name}` : ''}. Este es el panel de administracion.
      </p>

      {/* Placeholder cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mt-8">
        {[
          { label: 'Sucursales', value: '—', icon: '🏪' },
          { label: 'Categorias', value: '—', icon: '📂' },
          { label: 'Productos', value: '—', icon: '📦' },
          { label: 'Pedidos hoy', value: '—', icon: '🧾' },
        ].map((card) => (
          <div
            key={card.label}
            className="rounded-xl bg-bg-surface border border-border-default p-6"
          >
            <div className="flex items-center gap-3">
              <span className="text-2xl">{card.icon}</span>
              <div>
                <p className="text-sm text-text-secondary">{card.label}</p>
                <p className="text-2xl font-bold text-text-primary mt-1">{card.value}</p>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
