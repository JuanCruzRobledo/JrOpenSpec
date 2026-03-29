import { StrictMode, Suspense } from 'react';
import { createRoot } from 'react-dom/client';
import './i18n/index';
import './i18n/types'; // augment i18next module for type-safe keys
import './index.css';
import App from './App';

// Service worker registration is driven by useSWUpdate (via virtual:pwa-register/react)
// which is mounted in App.tsx through UpdateToast. No separate registerSW call here
// to avoid double registration.

const rootElement = document.getElementById('root');
if (!rootElement) {
  throw new Error('Root element #root not found in document');
}

createRoot(rootElement).render(
  <StrictMode>
    {/* Outer Suspense boundary for lazy i18n namespace loading */}
    <Suspense fallback={null}>
      <App />
    </Suspense>
  </StrictMode>
);
