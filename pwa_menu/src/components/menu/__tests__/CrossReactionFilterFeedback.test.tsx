import { screen } from '@testing-library/react';
import { CrossReactionFilterFeedback } from '@/components/menu/CrossReactionFilterFeedback';
import { renderWithProviders } from '@/test/render-with-providers';

describe('CrossReactionFilterFeedback', () => {
  it('renders localized visible feedback for hidden products', () => {
    renderWithProviders(
      <CrossReactionFilterFeedback
        summary={{
          hiddenProductCount: 2,
          selectedAllergenNames: ['Huevo'],
          crossReactionAllergenNames: ['Ave'],
        }}
      />
    );

    expect(
      screen.getByText('Se ocultaron 2 productos por reacción cruzada')
    ).toBeInTheDocument();
    expect(
      screen.getByText(
        'Modo muy estricto activo: también se ocultaron productos con Ave por su reacción cruzada con Huevo.'
      )
    ).toBeInTheDocument();
  });
});
