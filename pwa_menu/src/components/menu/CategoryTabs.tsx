import { useRef, useCallback } from 'react';
import { useTranslation } from 'react-i18next';
import { cn } from '@/lib/cn';
import type { MenuCategory } from '@/types/menu';

interface CategoryTabsProps {
  categories: MenuCategory[];
  activeId: string;
  onSelect: (id: string) => void;
}

/**
 * Horizontal scrollable category tab bar.
 * - role="tablist" with individual role="tab" items
 * - Arrow key (← →) navigation
 * - Auto-scrolls active tab into view
 * - No visible scrollbar
 */
export function CategoryTabs({ categories, activeId, onSelect }: CategoryTabsProps) {
  const { t } = useTranslation('menu');
  const listRef = useRef<HTMLDivElement>(null);

  const scrollTabIntoView = useCallback((tabEl: HTMLButtonElement) => {
    tabEl.scrollIntoView({ behavior: 'smooth', block: 'nearest', inline: 'center' });
  }, []);

  const handleKeyDown = useCallback(
    (e: React.KeyboardEvent<HTMLDivElement>) => {
      if (!['ArrowLeft', 'ArrowRight', 'Home', 'End'].includes(e.key)) return;
      e.preventDefault();

      const currentIndex = categories.findIndex((c) => c.id === activeId);
      let nextIndex = currentIndex;

      if (e.key === 'ArrowRight') {
        nextIndex = (currentIndex + 1) % categories.length;
      } else if (e.key === 'ArrowLeft') {
        nextIndex = (currentIndex - 1 + categories.length) % categories.length;
      } else if (e.key === 'Home') {
        nextIndex = 0;
      } else if (e.key === 'End') {
        nextIndex = categories.length - 1;
      }

      const nextCategory = categories[nextIndex];
      if (!nextCategory) return;

      onSelect(nextCategory.id);

      // Focus the newly selected tab button
      const listEl = listRef.current;
      if (listEl) {
        const tabBtn = listEl.querySelector<HTMLButtonElement>(
          `[data-tab-id="${nextCategory.id}"]`
        );
        if (tabBtn) {
          tabBtn.focus();
          scrollTabIntoView(tabBtn);
        }
      }
    },
    [categories, activeId, onSelect, scrollTabIntoView]
  );

  const handleTabClick = useCallback(
    (id: string, tabEl: HTMLButtonElement) => {
      onSelect(id);
      scrollTabIntoView(tabEl);
    },
    [onSelect, scrollTabIntoView]
  );

  return (
    <nav aria-label={t('categories.ariaLabel')}>
      <div
        ref={listRef}
        role="tablist"
        aria-label={t('categories.ariaLabel')}
        onKeyDown={handleKeyDown}
        className={cn(
          'flex gap-2 overflow-x-auto px-4 py-3',
          // Hide scrollbar across browsers
          '[&::-webkit-scrollbar]:hidden [-ms-overflow-style:none] [scrollbar-width:none]'
        )}
      >
        {categories.map((category) => {
          const isActive = category.id === activeId;
          return (
            <button
              key={category.id}
              type="button"
              role="tab"
              aria-selected={isActive}
              data-tab-id={category.id}
              tabIndex={isActive ? 0 : -1}
              onClick={(e) => handleTabClick(category.id, e.currentTarget)}
              className={cn(
                'inline-flex items-center whitespace-nowrap rounded-full px-4 font-medium text-sm',
                'min-h-[44px] flex-shrink-0',
                'transition-colors duration-150',
                'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent focus-visible:ring-offset-2',
                isActive
                  ? 'bg-accent text-white'
                  : 'bg-surface-muted text-text-secondary hover:text-surface-text hover:bg-surface-card'
              )}
            >
              {category.name}
            </button>
          );
        })}
      </div>
    </nav>
  );
}
