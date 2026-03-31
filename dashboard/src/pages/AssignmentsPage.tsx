/**
 * AssignmentsPage — waiter-sector assignment management with date + shift selection.
 */
import { Button } from '@/components/ui/Button';
import { Spinner } from '@/components/ui/Spinner';
import { HelpButton } from '@/components/ui/HelpButton';
import { AssignmentMatrix } from '@/components/assignments/AssignmentMatrix';
import { ShiftSelector } from '@/components/assignments/ShiftSelector';
import { useAssignmentMatrix } from '@/hooks/useAssignmentMatrix';
import { helpContent } from '@/utils/helpContent';

export default function AssignmentsPage() {
  const {
    waiters,
    sectors,
    selectedCells,
    isLoading,
    isSaving,
    error,
    selectedDate,
    selectedShift,
    setSelectedDate,
    setSelectedShift,
    handleToggle,
    handleSave,
    refresh,
  } = useAssignmentMatrix();

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold text-text-primary">Asignaciones</h1>
          <p className="mt-1 text-sm text-text-secondary">
            Asigna mozos a sectores por fecha y turno
          </p>
        </div>
        <div className="flex items-center gap-3">
          <HelpButton content={helpContent.assignments} />
          <Button
            onClick={handleSave}
            isLoading={isSaving}
            disabled={!selectedShift || isSaving}
          >
            Guardar asignaciones
          </Button>
        </div>
      </div>

      {/* Controls: date picker + shift selector */}
      <div className="flex flex-wrap items-end gap-4 mb-6">
        <div>
          <label className="block text-sm text-text-secondary mb-1.5">Fecha</label>
          <input
            type="date"
            value={selectedDate}
            onChange={(e) => setSelectedDate(e.target.value)}
            className="h-10 rounded-lg border border-border-default bg-bg-surface px-3 text-sm text-text-primary focus:outline-none focus:border-border-focus focus:ring-1 focus:ring-border-focus"
          />
        </div>

        <div>
          <label className="block text-sm text-text-secondary mb-1.5">Turno</label>
          <ShiftSelector
            selected={selectedShift}
            onChange={setSelectedShift}
          />
        </div>
      </div>

      {/* Loading state */}
      {isLoading ? (
        <div className="flex items-center justify-center py-16">
          <Spinner size="lg" />
        </div>
      ) : null}

      {/* Error state */}
      {error ? (
        <div className="text-center py-8">
          <p className="text-error mb-4">{error}</p>
          <Button variant="secondary" onClick={refresh}>
            Reintentar
          </Button>
        </div>
      ) : null}

      {/* Matrix */}
      {!isLoading && !error ? (
        <>
          {!selectedShift ? (
            <div className="text-center py-8 text-text-secondary">
              Selecciona un turno para ver y editar las asignaciones
            </div>
          ) : (
            <AssignmentMatrix
              waiters={waiters}
              sectors={sectors}
              selectedCells={selectedCells}
              onToggle={handleToggle}
              disabled={isSaving}
            />
          )}
        </>
      ) : null}
    </div>
  );
}
