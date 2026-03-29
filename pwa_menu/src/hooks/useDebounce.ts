import { useState, useEffect } from 'react';

/**
 * Returns a debounced version of `value` that only updates after
 * `delay` milliseconds have elapsed since the last change.
 *
 * @param value - The value to debounce
 * @param delay - Delay in milliseconds (use DEBOUNCE_MS from constants)
 *
 * @example
 *   const debouncedSearch = useDebounce(searchQuery, DEBOUNCE_MS);
 */
export function useDebounce<T>(value: T, delay: number): T {
  const [debouncedValue, setDebouncedValue] = useState<T>(value);

  useEffect(() => {
    const timer = setTimeout(() => {
      setDebouncedValue(value);
    }, delay);

    return () => {
      clearTimeout(timer);
    };
  }, [value, delay]);

  return debouncedValue;
}
