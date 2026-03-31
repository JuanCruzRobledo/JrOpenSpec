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
  | 'seals'
  | 'sectors'
  | 'tables'
  | 'staff'
  | 'roles'
  | 'assignments';

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
  sectors: {
    title: 'Gestion de Sectores',
    description: 'Los sectores organizan el salon de tu sucursal. Cada sector agrupa mesas y puede ser de tipo interior, terraza, barra o VIP.',
    tips: [
      'El prefijo del sector se genera automaticamente desde el nombre.',
      'Cada sector tiene un conteo de mesas totales y disponibles.',
      'Eliminar un sector elimina todas las mesas que contiene.',
      'Podes definir una capacidad maxima opcional por sector.',
    ],
  },
  tables: {
    title: 'Gestion de Mesas',
    description: 'Administra las mesas de tu sucursal. Visualiza el estado en tiempo real y cambia el estado segun el flujo del servicio.',
    tips: [
      'Las mesas se actualizan cada 15 segundos automaticamente.',
      'Los colores indican el estado: verde (libre), rojo (ocupada), amarillo (pedido solicitado), azul (pedido cumplido), violeta (cuenta), gris (inactiva).',
      'Usa "Crear mesas" para generar varias mesas en lote para un sector.',
      'Hace click en una mesa para cambiar su estado.',
      'Las mesas se ordenan por urgencia: cuenta y pedido solicitado primero.',
    ],
  },
  staff: {
    title: 'Gestion de Personal',
    description: 'Administra los miembros de tu equipo. Asigna roles y gestiona el acceso al sistema.',
    tips: [
      'Los roles disponibles son: Propietario, Administrador, Gerente, Mozo, Chef y Cajero.',
      'La contraseña solo se configura al crear un nuevo miembro.',
      'Usa el buscador para filtrar por nombre, email o rol.',
      'El personal es compartido entre todas las sucursales del restaurante.',
    ],
  },
  roles: {
    title: 'Roles y Permisos',
    description: 'Visualiza la matriz de permisos del sistema. Cada rol tiene un conjunto de permisos predefinidos.',
    tips: [
      'Los permisos son de solo lectura — se configuran desde el backend.',
      'La marca verde indica que el rol tiene ese permiso.',
      'Los permisos determinan que acciones puede realizar cada miembro del equipo.',
    ],
  },
  assignments: {
    title: 'Asignaciones de Mozos',
    description: 'Asigna mozos a sectores por fecha y turno. Define quien atiende cada zona del salon.',
    tips: [
      'Selecciona una fecha y un turno para ver las asignaciones.',
      'Marca las casillas para asignar un mozo a un sector.',
      'Un mozo puede estar asignado a multiples sectores en el mismo turno.',
      'Los turnos disponibles son: Mañana, Tarde y Noche.',
      'Guarda los cambios con el boton "Guardar asignaciones".',
    ],
  },
};
