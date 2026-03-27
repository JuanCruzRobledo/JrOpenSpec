/**
 * Generate a URL-friendly slug from text.
 * Strips accents, converts to lowercase, replaces spaces with hyphens.
 */
export function generateSlug(text: string): string {
  return text
    .normalize('NFD')
    .replace(/[\u0300-\u036f]/g, '') // strip accents
    .toLowerCase()
    .trim()
    .replace(/[^a-z0-9\s-]/g, '') // remove non-alphanumeric
    .replace(/[\s_]+/g, '-') // spaces/underscores to hyphens
    .replace(/-+/g, '-') // collapse multiple hyphens
    .replace(/^-|-$/g, ''); // trim leading/trailing hyphens
}
