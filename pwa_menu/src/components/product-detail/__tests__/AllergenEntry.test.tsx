/**
 * Component tests for AllergenEntry.tsx
 * Tests traffic-light coloring by presence type and cross-reaction rendering.
 * Uses renderWithProviders for i18n context.
 */

import { describe, it, expect } from 'vitest';
import { screen, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { AllergenEntry } from '../AllergenEntry';
import { renderWithProviders } from '@/test/render-with-providers';
import type { ProductAllergenDetail } from '@/types/product-detail';

// ---------------------------------------------------------------------------
// Fixtures
// ---------------------------------------------------------------------------

function makeAllergen(overrides: Partial<ProductAllergenDetail>): ProductAllergenDetail {
  return {
    allergenId: '1',
    allergenSlug: 'gluten',
    allergenName: 'Gluten',
    presence: 'contains',
    crossReactions: [],
    ...overrides,
  };
}

// ---------------------------------------------------------------------------
// S8: Presence-type styling
// ---------------------------------------------------------------------------

describe('AllergenEntry — presence type styling (S8)', () => {
  it('renders the allergen name', () => {
    renderWithProviders(
      <AllergenEntry allergen={makeAllergen({ allergenName: 'Gluten' })} />
    );
    expect(screen.getByText('Gluten')).toBeInTheDocument();
  });

  it('shows "contains" presence label from i18n for contains allergen', () => {
    renderWithProviders(
      <AllergenEntry allergen={makeAllergen({ presence: 'contains' })} />
    );
    // The presence label (t(`presence.contains`)) = "Contiene"
    expect(screen.getByText('Contiene')).toBeInTheDocument();
  });

  it('shows "may_contain" presence label from i18n for may_contain allergen', () => {
    renderWithProviders(
      <AllergenEntry allergen={makeAllergen({ presence: 'may_contain' })} />
    );
    // t(`presence.may_contain`) = "Puede contener"
    expect(screen.getByText('Puede contener')).toBeInTheDocument();
  });

  it('shows "free" presence label from i18n for free allergen', () => {
    renderWithProviders(
      <AllergenEntry allergen={makeAllergen({ presence: 'free' })} />
    );
    // t(`presence.free`) = "Libre de"
    expect(screen.getByText('Libre de')).toBeInTheDocument();
  });

  it('shows legend badge for "contains" allergen', () => {
    renderWithProviders(
      <AllergenEntry allergen={makeAllergen({ presence: 'contains' })} />
    );
    // t(`legend.contains`) = "Contiene este alérgeno"
    expect(screen.getByText('Contiene este alérgeno')).toBeInTheDocument();
  });

  it('shows legend badge for "may_contain" allergen', () => {
    renderWithProviders(
      <AllergenEntry allergen={makeAllergen({ presence: 'may_contain' })} />
    );
    // t(`legend.may_contain`) = "Puede contener trazas"
    expect(screen.getByText('Puede contener trazas')).toBeInTheDocument();
  });

  it('shows legend badge for "free" allergen', () => {
    renderWithProviders(
      <AllergenEntry allergen={makeAllergen({ presence: 'free' })} />
    );
    // t(`legend.free`) = "No contiene este alérgeno"
    expect(screen.getByText('No contiene este alérgeno')).toBeInTheDocument();
  });

  it('S8: contains allergen li has contains-bg CSS class', () => {
    renderWithProviders(
      <AllergenEntry allergen={makeAllergen({ presence: 'contains' })} />
    );
    const li = screen.getByRole('listitem');
    expect(li.className).toContain('bg-allergen-contains-bg');
  });

  it('S8: may_contain allergen li has may-contain-bg CSS class', () => {
    renderWithProviders(
      <AllergenEntry allergen={makeAllergen({ presence: 'may_contain' })} />
    );
    const li = screen.getByRole('listitem');
    expect(li.className).toContain('bg-allergen-may-contain-bg');
  });

  it('S8: free allergen li has free-bg CSS class', () => {
    renderWithProviders(
      <AllergenEntry allergen={makeAllergen({ presence: 'free' })} />
    );
    const li = screen.getByRole('listitem');
    expect(li.className).toContain('bg-allergen-free-bg');
  });
});

// ---------------------------------------------------------------------------
// Cross-reactions
// ---------------------------------------------------------------------------

describe('AllergenEntry — cross-reactions', () => {
  it('does not render cross-reaction section when crossReactions is empty', () => {
    renderWithProviders(
      <AllergenEntry allergen={makeAllergen({ crossReactions: [] })} />
    );
    expect(screen.queryByText('Ver reacciones cruzadas')).not.toBeInTheDocument();
  });

  it('renders expand button when cross-reactions exist', () => {
    const allergen = makeAllergen({
      crossReactions: [
        {
          allergenId: '2',
          allergenSlug: 'cacahuetes',
          allergenName: 'Cacahuetes',
          riskLevel: 'medium',
        },
      ],
    });

    renderWithProviders(<AllergenEntry allergen={allergen} />);

    expect(screen.getByText(/Ver reacciones cruzadas/)).toBeInTheDocument();
  });

  it('shows cross-reaction list on expand button click', async () => {
    const user = userEvent.setup({ advanceTimers: () => Promise.resolve() });

    const allergen = makeAllergen({
      crossReactions: [
        {
          allergenId: '2',
          allergenSlug: 'cacahuetes',
          allergenName: 'Cacahuetes',
          riskLevel: 'high',
        },
      ],
    });

    renderWithProviders(<AllergenEntry allergen={allergen} />);

    const expandButton = screen.getByRole('button');
    await user.click(expandButton);

    // After expanding, cross-reaction with name should be visible
    expect(screen.getByText(/Cacahuetes/)).toBeInTheDocument();
  });

  it('shows count of cross-reactions in the expand button', () => {
    const allergen = makeAllergen({
      crossReactions: [
        { allergenId: '2', allergenSlug: 'cacahuetes', allergenName: 'Cacahuetes', riskLevel: 'medium' },
        { allergenId: '3', allergenSlug: 'soja', allergenName: 'Soja', riskLevel: 'low' },
      ],
    });

    renderWithProviders(<AllergenEntry allergen={allergen} />);

    // Button text includes count: "(2)"
    expect(screen.getByText(/\(2\)/)).toBeInTheDocument();
  });

  it('renders allergen name and presence together', () => {
    renderWithProviders(
      <AllergenEntry
        allergen={makeAllergen({ allergenName: 'Lácteos', presence: 'may_contain' })}
      />
    );

    const li = screen.getByRole('listitem');
    expect(within(li).getByText('Lácteos')).toBeInTheDocument();
    expect(within(li).getByText('Puede contener')).toBeInTheDocument();
  });
});
