import { render, waitFor } from '@testing-library/react';
import { MemoryRouter, Route, Routes, useParams } from 'react-router-dom';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { buildDynamicManifest, useDynamicManifest } from '../useDynamicManifest';

function Harness() {
  const params = useParams<{ tenant: string; branch: string }>();

  useDynamicManifest({
    tenant: params.tenant,
    branch: params.branch,
    branchName: 'Buen Sabor Centro',
  });

  return <div>manifest harness</div>;
}

let manifestBlob: Blob | null = null;
const createObjectURLMock = vi.fn((blob: Blob) => {
  manifestBlob = blob;
  return 'blob:manifest-url';
});
const revokeObjectURLMock = vi.fn();
const originalCreateObjectURL = (URL as typeof URL & { createObjectURL?: typeof URL.createObjectURL }).createObjectURL;
const originalRevokeObjectURL = (URL as typeof URL & { revokeObjectURL?: typeof URL.revokeObjectURL }).revokeObjectURL;

beforeEach(() => {
  manifestBlob = null;
  createObjectURLMock.mockClear();
  revokeObjectURLMock.mockClear();
  Object.assign(URL, {
    createObjectURL: createObjectURLMock,
    revokeObjectURL: revokeObjectURLMock,
  });
});

afterEach(() => {
  if (originalCreateObjectURL) {
    Object.assign(URL, { createObjectURL: originalCreateObjectURL });
  } else {
    delete (URL as typeof URL & { createObjectURL?: typeof URL.createObjectURL }).createObjectURL;
  }

  if (originalRevokeObjectURL) {
    Object.assign(URL, { revokeObjectURL: originalRevokeObjectURL });
  } else {
    delete (URL as typeof URL & { revokeObjectURL?: typeof URL.revokeObjectURL }).revokeObjectURL;
  }

  document.head.innerHTML = '';
});

describe('buildDynamicManifest', () => {
  it('builds a scoped manifest for tenant/branch routes', () => {
    expect(
      buildDynamicManifest({
        tenant: 'buen-sabor',
        branch: 'centro',
        branchName: 'Buen Sabor Centro',
      })
    ).toMatchObject({
      start_url: '/buen-sabor/centro',
      scope: '/buen-sabor/centro',
      name: 'Buen Sabor Centro - Menu',
    });
  });
});

describe('useDynamicManifest', () => {
  it('replaces the static manifest link with a route-scoped runtime manifest', async () => {
    const manifestLink = document.createElement('link');
    manifestLink.rel = 'manifest';
    manifestLink.href = '/manifest.json';
    document.head.appendChild(manifestLink);

    render(
      <MemoryRouter initialEntries={['/buen-sabor/centro']}>
        <Routes>
          <Route path="/:tenant/:branch" element={<Harness />} />
        </Routes>
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(manifestLink.getAttribute('href')).toBe('blob:manifest-url');
    });

    expect(createObjectURLMock).toHaveBeenCalledTimes(1);
    expect(manifestBlob).not.toBeNull();
  });
});
