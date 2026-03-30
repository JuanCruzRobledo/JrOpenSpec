const LAST_TABLE_CONTEXT_KEY = 'buen-sabor-last-table-context';

export interface LastTableContext {
  tenant: string;
  branch: string;
  table: string;
}

export function buildLandingPath(tenant: string, branch: string, table: string): string {
  return `/${tenant}/${branch}/mesa/${table}`;
}

export function persistLastTableContext(context: LastTableContext): void {
  try {
    localStorage.setItem(LAST_TABLE_CONTEXT_KEY, JSON.stringify(context));
  } catch {
    // Ignore storage errors — redirect fallback remains '/'
  }
}

export function readLastTableContext(): LastTableContext | null {
  try {
    const raw = localStorage.getItem(LAST_TABLE_CONTEXT_KEY);
    if (!raw) return null;

    const parsed = JSON.parse(raw) as Partial<LastTableContext>;
    if (
      typeof parsed.tenant !== 'string' ||
      typeof parsed.branch !== 'string' ||
      typeof parsed.table !== 'string'
    ) {
      return null;
    }

    return {
      tenant: parsed.tenant,
      branch: parsed.branch,
      table: parsed.table,
    };
  } catch {
    return null;
  }
}

export function resolveRememberedLandingPath(
  tenant?: string,
  branch?: string
): string | null {
  if (!tenant || !branch) return null;

  const remembered = readLastTableContext();
  if (!remembered) return null;

  if (remembered.tenant !== tenant || remembered.branch !== branch) {
    return null;
  }

  return buildLandingPath(remembered.tenant, remembered.branch, remembered.table);
}

export { LAST_TABLE_CONTEXT_KEY };
