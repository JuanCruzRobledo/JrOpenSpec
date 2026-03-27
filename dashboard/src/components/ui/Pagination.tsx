import { Button } from '@/components/ui/Button';

interface Props {
  currentPage: number;
  totalPages: number;
  onPageChange: (page: number) => void;
}

export function Pagination({ currentPage, totalPages, onPageChange }: Props) {
  if (totalPages <= 1) return null;

  return (
    <div className="flex items-center justify-end gap-3 py-4">
      <span className="text-sm text-text-secondary">
        Pagina {currentPage} de {totalPages}
      </span>
      <div className="flex gap-1">
        <Button
          variant="secondary"
          size="sm"
          disabled={currentPage <= 1}
          onClick={() => onPageChange(currentPage - 1)}
        >
          Anterior
        </Button>
        <Button
          variant="secondary"
          size="sm"
          disabled={currentPage >= totalPages}
          onClick={() => onPageChange(currentPage + 1)}
        >
          Siguiente
        </Button>
      </div>
    </div>
  );
}
