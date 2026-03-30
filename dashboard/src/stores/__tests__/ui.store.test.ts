/**
 * UI store tests — S21 (toast stacking) and S22 (auto-dismiss).
 */
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { useUIStore } from '../ui.store';

function resetStore() {
  useUIStore.setState({
    toasts: [],
    confirmDialog: null,
    sidebarCollapsed: false,
  });
}

describe('S21 — Toast stacking: evicts oldest when limit exceeded', () => {
  beforeEach(() => {
    resetStore();
    vi.clearAllMocks();
    vi.useFakeTimers();
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  it('keeps at most MAX_TOASTS (5) toasts when 6 are added', () => {
    const { addToast } = useUIStore.getState();

    for (let i = 1; i <= 6; i++) {
      addToast({ type: 'info', message: `Toast ${i}`, duration: 60_000 });
    }

    const { toasts } = useUIStore.getState();
    expect(toasts).toHaveLength(5);
  });

  it('evicts the oldest toast — only the newest 5 remain', () => {
    const { addToast } = useUIStore.getState();

    for (let i = 1; i <= 6; i++) {
      addToast({ type: 'info', message: `Toast ${i}`, duration: 60_000 });
    }

    const { toasts } = useUIStore.getState();
    const messages = toasts.map((t) => t.message);
    // Toast 1 should be evicted; toasts 2-6 remain
    expect(messages).not.toContain('Toast 1');
    expect(messages).toContain('Toast 6');
  });
});

describe('S22 — Toast auto-dismiss after default duration', () => {
  beforeEach(() => {
    resetStore();
    vi.clearAllMocks();
    vi.useFakeTimers();
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  it('removes a toast after its duration elapses', () => {
    const { addToast } = useUIStore.getState();

    addToast({ type: 'success', message: 'Auto-dismiss me' });

    // Toast should be present right away
    expect(useUIStore.getState().toasts).toHaveLength(1);

    // Advance past default TOAST_DURATION_MS (5000ms)
    vi.advanceTimersByTime(5_001);

    expect(useUIStore.getState().toasts).toHaveLength(0);
  });

  it('respects a custom duration when provided', () => {
    const { addToast } = useUIStore.getState();

    addToast({ type: 'info', message: 'Custom duration', duration: 2_000 });

    vi.advanceTimersByTime(1_999);
    expect(useUIStore.getState().toasts).toHaveLength(1);

    vi.advanceTimersByTime(2);
    expect(useUIStore.getState().toasts).toHaveLength(0);
  });
});

describe('Confirm dialog — showConfirm resolves promises', () => {
  beforeEach(() => {
    resetStore();
  });

  it('resolves true when onConfirm is called', async () => {
    const promise = useUIStore.getState().showConfirm({
      title: 'Confirm?',
      description: 'Are you sure?',
    });

    useUIStore.getState().confirmDialog?.onConfirm();

    expect(await promise).toBe(true);
    expect(useUIStore.getState().confirmDialog).toBeNull();
  });

  it('resolves false when onCancel is called', async () => {
    const promise = useUIStore.getState().showConfirm({
      title: 'Confirm?',
      description: 'Are you sure?',
    });

    useUIStore.getState().confirmDialog?.onCancel();

    expect(await promise).toBe(false);
    expect(useUIStore.getState().confirmDialog).toBeNull();
  });
});
