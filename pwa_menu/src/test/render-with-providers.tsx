/**
 * Test utilities — renderWithProviders wraps components with i18n + router context.
 * Use this for component tests that need translation or routing.
 */

import { render, type RenderOptions } from '@testing-library/react';
import { Suspense, type ReactElement, type ReactNode } from 'react';
import { MemoryRouter } from 'react-router-dom';
import { I18nextProvider } from 'react-i18next';
import i18n from 'i18next';
import { initReactI18next } from 'react-i18next';

// Synchronous i18n instance for tests — uses in-memory resources, no HTTP backend
const testI18n = i18n.createInstance();

void testI18n.use(initReactI18next).init({
  lng: 'es',
  fallbackLng: 'es',
  defaultNS: 'allergens',
  ns: ['allergens', 'common', 'session', 'menu', 'filters'],
  resources: {
    es: {
      allergens: {
        presence: {
          contains: 'Contiene',
          may_contain: 'Puede contener',
          free: 'Libre de',
        },
        legend: {
          contains: 'Contiene este alérgeno',
          may_contain: 'Puede contener trazas',
          free: 'No contiene este alérgeno',
        },
        crossReactions: {
          expand: 'Ver reacciones cruzadas',
          collapse: 'Ocultar reacciones cruzadas',
          with: 'Reacción cruzada con {{allergen}}',
        },
        riskLevel: {
          low: 'Riesgo bajo',
          medium: 'Riesgo medio',
          high: 'Riesgo alto',
        },
      },
      common: {},
      session: {
        landing: { anonymous: 'Anónimo' },
        errors: {
          invalidQR: 'QR inválido',
          joinFailed: 'Error al unirse',
          branchNotFound: 'Sucursal no encontrada',
          tableInactive: 'Mesa inactiva',
        },
      },
      menu: {
        crossReactionFeedback: {
          title_one: 'Se ocultó {{count}} producto por reacción cruzada',
          title_other: 'Se ocultaron {{count}} productos por reacción cruzada',
          description:
            'Modo muy estricto activo: también se ocultaron productos con {{crossReactions}} por su reacción cruzada con {{selectedAllergens}}.',
        },
      },
      filters: {},
    },
  },
  interpolation: { escapeValue: false },
  react: { useSuspense: false },
});

interface ProvidersProps {
  children: ReactNode;
  initialRoute?: string;
}

function AllProviders({ children, initialRoute = '/' }: ProvidersProps) {
  return (
    <I18nextProvider i18n={testI18n}>
      <MemoryRouter initialEntries={[initialRoute]}>
        <Suspense fallback={null}>{children}</Suspense>
      </MemoryRouter>
    </I18nextProvider>
  );
}

interface CustomRenderOptions extends Omit<RenderOptions, 'wrapper'> {
  initialRoute?: string;
}

export function renderWithProviders(
  ui: ReactElement,
  { initialRoute, ...options }: CustomRenderOptions = {}
) {
  return render(ui, {
    wrapper: ({ children }) => (
      <AllProviders initialRoute={initialRoute ?? '/'}>{children}</AllProviders>
    ),
    ...options,
  });
}

export { testI18n };
