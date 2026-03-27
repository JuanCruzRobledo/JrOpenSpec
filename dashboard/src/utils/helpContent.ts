// Centralized help content for all Dashboard pages.
// Each entry provides contextual help shown via HelpButton.

interface HelpContent {
  title: string;
  description: string;
  tips?: string[];
}

type HelpContentKey = 'dashboard' | 'restaurant' | 'branches' | 'categories' | 'subcategories' | 'products';

export const helpContent: Record<HelpContentKey, HelpContent> = {
  dashboard: {
    title: 'Panel Principal',
    description: 'Vista general del estado de tu restaurante. Aqui podras ver estadisticas y metricas clave de tu negocio.',
    tips: [
      'Las metricas se actualizan en tiempo real.',
      'Selecciona una sucursal para ver datos especificos.',
    ],
  },
  restaurant: {
    title: 'Configuracion del Restaurante',
    description: 'Edita la informacion general de tu restaurante: nombre, slug (URL amigable), descripcion, logo, banner e informacion de contacto.',
    tips: [
      'El slug se genera automaticamente desde el nombre, pero podes editarlo.',
      'El logo y banner se configuran con URLs de imagenes.',
      'La informacion de contacto es visible para tus clientes.',
    ],
  },
  branches: {
    title: 'Gestion de Sucursales',
    description: 'Administra las sucursales de tu restaurante. Cada sucursal tiene su propio menu, categorias y productos.',
    tips: [
      'Al crear una sucursal, se genera automaticamente una categoria "General".',
      'Eliminar una sucursal elimina tambien todas sus categorias, subcategorias y productos.',
      'Configura los horarios de apertura y cierre de cada sucursal.',
    ],
  },
  categories: {
    title: 'Gestion de Categorias',
    description: 'Las categorias organizan el menu de tu sucursal. Cada categoria puede tener un icono (emoji) y una imagen.',
    tips: [
      'La categoria "Home" es del sistema y no se puede editar ni eliminar.',
      'El orden determina como aparecen las categorias en el menu.',
      'Eliminar una categoria elimina todas sus subcategorias y productos.',
    ],
  },
  subcategories: {
    title: 'Gestion de Subcategorias',
    description: 'Las subcategorias permiten organizar mejor los productos dentro de cada categoria.',
    tips: [
      'Cada subcategoria pertenece a una categoria padre.',
      'Podes filtrar la lista por categoria usando el dropdown.',
      'Eliminar una subcategoria elimina todos sus productos.',
    ],
  },
  products: {
    title: 'Gestion de Productos',
    description: 'Administra los productos de tu menu. Configura precios, categorias, descripciones y opciones de destacado.',
    tips: [
      'Los precios se ingresan en pesos (ej: 2500.50) y se almacenan en centavos.',
      'Selecciona una categoria para filtrar las subcategorias disponibles.',
      'Los productos "destacados" y "populares" tienen mayor visibilidad en el menu.',
      'La descripcion tiene un limite de 500 caracteres.',
    ],
  },
};
