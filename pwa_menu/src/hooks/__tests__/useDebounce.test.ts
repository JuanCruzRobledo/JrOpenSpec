/**
 * Unit tests for useDebounce hook.
 * Uses vi.useFakeTimers() to control timer execution precisely.
 */

import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import { renderHook, act } from '@testing-library/react';
import { useDebounce } from '../useDebounce';

beforeEach(() => {
  vi.useFakeTimers();
});

afterEach(() => {
  vi.useRealTimers();
});

describe('useDebounce', () => {
  it('returns the initial value immediately', () => {
    const { result } = renderHook(() => useDebounce('initial', 300));
    expect(result.current).toBe('initial');
  });

  it('does not update before the delay has elapsed', () => {
    const { result, rerender } = renderHook(
      ({ value, delay }) => useDebounce(value, delay),
      { initialProps: { value: 'initial', delay: 300 } }
    );

    rerender({ value: 'updated', delay: 300 });

    // Advance only partially — should still be the old value
    act(() => {
      vi.advanceTimersByTime(299);
    });

    expect(result.current).toBe('initial');
  });

  it('returns updated value after the delay has elapsed', () => {
    const { result, rerender } = renderHook(
      ({ value, delay }) => useDebounce(value, delay),
      { initialProps: { value: 'initial', delay: 300 } }
    );

    rerender({ value: 'updated', delay: 300 });

    act(() => {
      vi.advanceTimersByTime(300);
    });

    expect(result.current).toBe('updated');
  });

  it('resets the timer when value changes before delay elapses', () => {
    const { result, rerender } = renderHook(
      ({ value, delay }) => useDebounce(value, delay),
      { initialProps: { value: 'initial', delay: 300 } }
    );

    // First change
    rerender({ value: 'first-change', delay: 300 });

    act(() => {
      vi.advanceTimersByTime(200); // 200ms in — timer not fired yet
    });

    expect(result.current).toBe('initial'); // still initial

    // Second change — resets the timer
    rerender({ value: 'second-change', delay: 300 });

    act(() => {
      vi.advanceTimersByTime(200); // 200ms more — still before new 300ms window
    });

    expect(result.current).toBe('initial'); // still initial

    act(() => {
      vi.advanceTimersByTime(100); // full 300ms from second change
    });

    expect(result.current).toBe('second-change'); // now updated
  });

  it('works with numeric values', () => {
    const { result, rerender } = renderHook(
      ({ value, delay }) => useDebounce(value, delay),
      { initialProps: { value: 0, delay: 200 } }
    );

    rerender({ value: 42, delay: 200 });

    act(() => {
      vi.advanceTimersByTime(200);
    });

    expect(result.current).toBe(42);
  });

  it('works with object values (reference equality)', () => {
    const initial = { a: 1 };
    const updated = { a: 2 };

    const { result, rerender } = renderHook(
      ({ value, delay }) => useDebounce(value, delay),
      { initialProps: { value: initial, delay: 300 } }
    );

    rerender({ value: updated, delay: 300 });

    act(() => {
      vi.advanceTimersByTime(300);
    });

    expect(result.current).toBe(updated);
  });

  it('respects different delay values', () => {
    const { result, rerender } = renderHook(
      ({ value, delay }) => useDebounce(value, delay),
      { initialProps: { value: 'initial', delay: 500 } }
    );

    rerender({ value: 'updated', delay: 500 });

    // 300ms — not yet fired (delay is 500)
    act(() => {
      vi.advanceTimersByTime(300);
    });
    expect(result.current).toBe('initial');

    // 500ms total — should fire now
    act(() => {
      vi.advanceTimersByTime(200);
    });
    expect(result.current).toBe('updated');
  });

  it('clears previous timer when delay changes', () => {
    const { result, rerender } = renderHook(
      ({ value, delay }) => useDebounce(value, delay),
      { initialProps: { value: 'initial', delay: 300 } }
    );

    rerender({ value: 'updated', delay: 300 });

    // Change delay to 100 — should restart timer with new delay
    rerender({ value: 'updated', delay: 100 });

    act(() => {
      vi.advanceTimersByTime(100);
    });

    expect(result.current).toBe('updated');
  });
});
