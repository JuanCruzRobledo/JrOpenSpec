// Centralized help content for all Dashboard pages.
// Each entry provides contextual help shown via HelpButton.

interface HelpContent {
  title: string;
  description: string;
  tips?: string[];
}

type HelpContentKey =
  | 'dashboard'
  | 'restaurant'
  | 'branches'
  | 'categories'
  | 'subcategories'
  | 'products'
  | 'allergens'
  | 'dietaryProfiles'
  | 'cookingMethods'
  | 'badges'
  | 'seals';

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
      'Usa las pestanas del formulario para configurar alergenos, ingredientes, badges y precios por sucursal.',
      'El boton "Actualizar Precios" permite cambiar precios en lote.',
    ],
  },
  allergens: {
    title: 'Gestion de Alergenos',
    description: 'Administra los alergenos del sistema y personalizados. Los 14 alergenos obligatorios de la UE estan precargados.',
    tips: [
      'Los alergenos del sistema (UE 14) no pueden ser editados ni eliminados.',
      'Podes crear alergenos personalizados para necesidades especificas.',
      'Los alergenos se asignan a productos desde la pestaña de alergenos del formulario de producto.',
      'Las reacciones cruzadas se gestionan desde la vista de detalle de cada alergeno.',
    ],
  },
  dietaryProfiles: {
    title: 'Perfiles Dieteticos',
    description: 'Gestiona los perfiles dieteticos para clasificar tus productos (vegetariano, vegano, sin gluten, etc.).',
    tips: [
      'Los 7 perfiles del sistema estan precargados y no pueden modificarse.',
      'Podes crear perfiles personalizados para dietas especificas.',
      'Los perfiles se asignan desde la pestaña "Dieta" del formulario de producto.',
      'Los clientes podran filtrar el menu publico por perfil dietetico.',
    ],
  },
  cookingMethods: {
    title: 'Metodos de Coccion',
    description: 'Gestiona los metodos de coccion disponibles para clasificar tus productos.',
    tips: [
      'Los 10 metodos del sistema estan precargados (parrilla, horno, fritura, etc.).',
      'Podes crear metodos personalizados.',
      'Los metodos se asignan desde la pestaña "Coccion" del formulario de producto.',
    ],
  },
  badges: {
    title: 'Gestion de Badges',
    description: 'Los badges son etiquetas visuales que destacan productos en el menu (Nuevo, Mas vendido, Chef recomienda, Oferta).',
    tips: [
      'Los 4 badges del sistema estan precargados con sus colores.',
      'Podes crear badges personalizados con color e icono.',
      'Los badges se asignan desde la pestaña "Badges/Sellos" del formulario de producto.',
      'Aparecen como etiquetas de color en el menu publico.',
    ],
  },
  seals: {
    title: 'Gestion de Sellos',
    description: 'Los sellos representan certificaciones y atributos de calidad (Organico, Local, Artesanal, Sustentable, etc.).',
    tips: [
      'Los 6 sellos del sistema estan precargados con sus colores.',
      'Podes crear sellos personalizados para certificaciones especificas.',
      'Los sellos se asignan desde la pestaña "Badges/Sellos" del formulario de producto.',
      'Comunican calidad y valores a los clientes.',
    ],
  },
};
