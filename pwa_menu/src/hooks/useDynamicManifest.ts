import { useEffect } from 'react';

interface DynamicManifestOptions {
  tenant?: string;
  branch?: string;
  branchName?: string;
}

interface PwaManifest {
  name: string;
  short_name: string;
  description: string;
  theme_color: string;
  background_color: string;
  display: string;
  orientation: string;
  start_url: string;
  scope: string;
  lang: string;
  categories: string[];
  icons: Array<{
    src: string;
    sizes: string;
    type: string;
    purpose: string;
  }>;
}

export function buildDynamicManifest({
  tenant,
  branch,
  branchName,
}: DynamicManifestOptions): PwaManifest {
  const hasScopedRoute = Boolean(tenant && branch);
  const scopedPath = hasScopedRoute ? `/${tenant}/${branch}` : '/';
  const resolvedBranchName = branchName?.trim() || 'Buen Sabor';

  return {
    name: `${resolvedBranchName} - Menu`,
    short_name: 'Menu',
    description: `Menú digital de ${resolvedBranchName} con filtrado de alérgenos.`,
    theme_color: '#f97316',
    background_color: '#0a0a0a',
    display: 'standalone',
    orientation: 'portrait',
    start_url: scopedPath,
    scope: scopedPath,
    lang: 'es',
    categories: ['food'],
    icons: [
      {
        src: '/icon-192x192.png',
        sizes: '192x192',
        type: 'image/png',
        purpose: 'any',
      },
      {
        src: '/icon-192x192-maskable.png',
        sizes: '192x192',
        type: 'image/png',
        purpose: 'maskable',
      },
      {
        src: '/icon-512x512.png',
        sizes: '512x512',
        type: 'image/png',
        purpose: 'any',
      },
      {
        src: '/icon-512x512-maskable.png',
        sizes: '512x512',
        type: 'image/png',
        purpose: 'maskable',
      },
    ],
  };
}

function ensureManifestLink(doc: Document): HTMLLinkElement {
  const existing = doc.querySelector('link[rel="manifest"]');
  if (existing instanceof HTMLLinkElement) {
    return existing;
  }

  const link = doc.createElement('link');
  link.rel = 'manifest';
  doc.head.appendChild(link);
  return link;
}

/**
 * Replaces the static manifest link with a route-scoped manifest at runtime.
 * This is the closest standards-compliant approach for tenant/branch-specific
 * start_url values in a single SPA build.
 */
export function useDynamicManifest(options: DynamicManifestOptions): void {
  useEffect(() => {
    const link = ensureManifestLink(document);
    const fallbackHref = '/manifest.json';
    const manifest = buildDynamicManifest(options);
    const manifestJson = JSON.stringify(manifest);
    const blob = new Blob([manifestJson], {
      type: 'application/manifest+json',
    });
    const objectUrl = typeof URL.createObjectURL === 'function'
      ? URL.createObjectURL(blob)
      : `data:application/manifest+json,${encodeURIComponent(manifestJson)}`;

    link.href = objectUrl;

    return () => {
      if (link.href === objectUrl) {
        link.href = fallbackHref;
      }
      if (typeof URL.revokeObjectURL === 'function') {
        URL.revokeObjectURL(objectUrl);
      }
    };
  }, [options.tenant, options.branch, options.branchName]);
}
