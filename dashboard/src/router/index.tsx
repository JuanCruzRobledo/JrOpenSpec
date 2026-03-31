import { lazy, Suspense } from 'react';
import { createBrowserRouter, Navigate } from 'react-router-dom';
import { ProtectedRoute } from '@/router/ProtectedRoute';
import { BranchGuard } from '@/router/BranchGuard';
import { AuthLayout } from '@/layouts/AuthLayout';
import { DashboardLayout } from '@/layouts/DashboardLayout';
import { Spinner } from '@/components/ui/Spinner';

// Lazy-loaded pages (code splitting)
const LoginPage = lazy(() => import('@/pages/LoginPage'));
const DashboardPage = lazy(() => import('@/pages/DashboardPage'));
const RestaurantPage = lazy(() => import('@/pages/RestaurantPage'));
const BranchesPage = lazy(() => import('@/pages/BranchesPage'));
const CategoriesPage = lazy(() => import('@/pages/CategoriesPage'));
const SubcategoriesPage = lazy(() => import('@/pages/SubcategoriesPage'));
const ProductsPage = lazy(() => import('@/pages/ProductsPage'));
const AllergensPage = lazy(() => import('@/pages/AllergensPage'));
const DietaryProfilesPage = lazy(() => import('@/pages/DietaryProfilesPage'));
const CookingMethodsPage = lazy(() => import('@/pages/CookingMethodsPage'));
const BadgesPage = lazy(() => import('@/pages/BadgesPage'));
const SealsPage = lazy(() => import('@/pages/SealsPage'));
const SectorsPage = lazy(() => import('@/pages/SectorsPage'));
const TablesPage = lazy(() => import('@/pages/TablesPage'));
const StaffPage = lazy(() => import('@/pages/StaffPage'));
const RolesPage = lazy(() => import('@/pages/RolesPage'));
const AssignmentsPage = lazy(() => import('@/pages/AssignmentsPage'));

function PageLoader() {
  return (
    <div className="flex items-center justify-center min-h-[50vh]">
      <Spinner size="lg" />
    </div>
  );
}

function SuspenseWrapper({ children }: { children: React.ReactNode }) {
  return <Suspense fallback={<PageLoader />}>{children}</Suspense>;
}

export const router = createBrowserRouter([
  {
    path: '/login',
    element: <AuthLayout />,
    children: [
      {
        index: true,
        element: (
          <SuspenseWrapper>
            <LoginPage />
          </SuspenseWrapper>
        ),
      },
    ],
  },
  {
    path: '/',
    element: <ProtectedRoute />,
    children: [
      {
        element: <DashboardLayout />,
        children: [
          {
            index: true,
            element: <Navigate to="/dashboard" replace />,
          },
          {
            path: 'dashboard',
            element: (
              <SuspenseWrapper>
                <DashboardPage />
              </SuspenseWrapper>
            ),
          },
          {
            path: 'configuracion',
            element: (
              <SuspenseWrapper>
                <RestaurantPage />
              </SuspenseWrapper>
            ),
          },
          {
            path: 'sucursales',
            element: (
              <SuspenseWrapper>
                <BranchesPage />
              </SuspenseWrapper>
            ),
          },
          {
            element: <BranchGuard />,
            children: [
              {
                path: 'categorias',
                element: (
                  <SuspenseWrapper>
                    <CategoriesPage />
                  </SuspenseWrapper>
                ),
              },
              {
                path: 'subcategorias',
                element: (
                  <SuspenseWrapper>
                    <SubcategoriesPage />
                  </SuspenseWrapper>
                ),
              },
              {
                path: 'productos',
                element: (
                  <SuspenseWrapper>
                    <ProductsPage />
                  </SuspenseWrapper>
                ),
              },
              {
                path: 'sectores',
                element: (
                  <SuspenseWrapper>
                    <SectorsPage />
                  </SuspenseWrapper>
                ),
              },
              {
                path: 'mesas',
                element: (
                  <SuspenseWrapper>
                    <TablesPage />
                  </SuspenseWrapper>
                ),
              },
              {
                path: 'asignaciones',
                element: (
                  <SuspenseWrapper>
                    <AssignmentsPage />
                  </SuspenseWrapper>
                ),
              },
            ],
          },
          // Personal — no branch guard required (tenant-scoped)
          {
            path: 'personal',
            element: (
              <SuspenseWrapper>
                <StaffPage />
              </SuspenseWrapper>
            ),
          },
          {
            path: 'roles',
            element: (
              <SuspenseWrapper>
                <RolesPage />
              </SuspenseWrapper>
            ),
          },
          // Menu Avanzado — no branch guard required (tenant-scoped)
          {
            path: 'alergenos',
            element: (
              <SuspenseWrapper>
                <AllergensPage />
              </SuspenseWrapper>
            ),
          },
          {
            path: 'perfiles-dieteticos',
            element: (
              <SuspenseWrapper>
                <DietaryProfilesPage />
              </SuspenseWrapper>
            ),
          },
          {
            path: 'metodos-coccion',
            element: (
              <SuspenseWrapper>
                <CookingMethodsPage />
              </SuspenseWrapper>
            ),
          },
          {
            path: 'badges',
            element: (
              <SuspenseWrapper>
                <BadgesPage />
              </SuspenseWrapper>
            ),
          },
          {
            path: 'sellos',
            element: (
              <SuspenseWrapper>
                <SealsPage />
              </SuspenseWrapper>
            ),
          },
        ],
      },
    ],
  },
]);
