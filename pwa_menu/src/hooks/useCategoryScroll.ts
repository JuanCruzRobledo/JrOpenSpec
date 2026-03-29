import { useState, useEffect, useCallback, useRef } from 'react';

interface UseCategoryScrollResult {
  /** The category id currently in view */
  activeCategory: string | null;
  /** Smoothly scrolls the section for a given category id into view */
  scrollToCategory: (id: string) => void;
}

/**
 * Syncs the active category tab with the visible section using IntersectionObserver.
 *
 * @param sectionRefs - Map of category id → HTMLElement (section container)
 *
 * Usage:
 *   const refs = useRef(new Map<string, HTMLElement>())
 *   const { activeCategory, scrollToCategory } = useCategoryScroll(refs.current)
 */
export function useCategoryScroll(
  sectionRefs: Map<string, HTMLElement>
): UseCategoryScrollResult {
  const [activeCategory, setActiveCategory] = useState<string | null>(null);

  // Track whether a programmatic scroll is in progress to avoid observer feedback loop
  const isProgrammaticScrollRef = useRef(false);

  useEffect(() => {
    if (sectionRefs.size === 0) return;

    const observer = new IntersectionObserver(
      (entries) => {
        // Ignore observer callbacks triggered by our own programmatic scrolls
        if (isProgrammaticScrollRef.current) return;

        // Find the first entry that is intersecting (topmost visible section)
        const visible = entries.find((entry) => entry.isIntersecting);
        if (visible) {
          // Resolve the category id from the observed element
          for (const [id, el] of sectionRefs.entries()) {
            if (el === visible.target) {
              setActiveCategory(id);
              break;
            }
          }
        }
      },
      {
        threshold: 0.3,
        // Use viewport as root
        root: null,
      }
    );

    // Observe all registered section elements
    for (const el of sectionRefs.values()) {
      observer.observe(el);
    }

    return () => {
      observer.disconnect();
    };
  }, [sectionRefs]);

  const scrollToCategory = useCallback(
    (id: string) => {
      const el = sectionRefs.get(id);
      if (!el) return;

      isProgrammaticScrollRef.current = true;
      setActiveCategory(id);

      el.scrollIntoView({ behavior: 'smooth', block: 'start' });

      // Reset the programmatic flag after scroll animation finishes (~600ms)
      setTimeout(() => {
        isProgrammaticScrollRef.current = false;
      }, 700);
    },
    [sectionRefs]
  );

  return { activeCategory, scrollToCategory };
}
