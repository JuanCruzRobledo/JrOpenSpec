import { lazy, Suspense } from 'react';
import { createBrowserRouter, Navigate } from 'react-router-dom';
import { ROUTES } from './routes';
import { SessionGuard } from './SessionGuard';
import { LandingLayout } from '@/layouts/LandingLayout';
import { MenuLayout } from '@/layouts/MenuLayout';
import { MenuSkeleton } from '@/components/menu/MenuSkeleton';

// ---------------------------------------------------------------------------
// Lazy-loaded page components
// Route chunks are code-split so the initial bundle stays small.
// ---------------------------------------------------------------------------

const LandingPage = lazy(
  () => import('@/components/session/LandingPage')
);

const MenuPage = lazy(
  () => import('@/components/menu/MenuPage')
);

// ---------------------------------------------------------------------------
// Router
// ---------------------------------------------------------------------------

export const router = createBrowserRouter([
  {
    // Landing / QR entry — no session required
    path: ROUTES.LANDING,
    element: <LandingLayout />,
    children: [
      {
        index: true,
        element: (
          <Suspense fallback={<MenuSkeleton />}>
            <LandingPage />
          </Suspense>
        ),
      },
    ],
  },
  {
    // Menu root — session required
    path: ROUTES.MENU,
    element: <SessionGuard />,
    children: [
      {
        element: <MenuLayout />,
        children: [
          {
            index: true,
            element: (
              <Suspense fallback={<MenuSkeleton />}>
                <MenuPage />
              </Suspense>
            ),
          },
        ],
      },
    ],
  },
  {
    // Product detail overlay — session required.
    // MenuPage reads the :productId param and opens the detail modal inline.
    path: ROUTES.PRODUCT_DETAIL,
    element: <SessionGuard />,
    children: [
      {
        element: <MenuLayout />,
        children: [
          {
            index: true,
            element: (
              <Suspense fallback={<MenuSkeleton />}>
                <MenuPage />
              </Suspense>
            ),
          },
        ],
      },
    ],
  },
  {
    // Catch-all redirect — unmatched paths fall back to root
    path: '*',
    element: <Navigate to="/" replace />,
  },
]);
