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
            ],
          },
        ],
      },
    ],
  },
]);
