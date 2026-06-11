import { useState } from 'react'
import { usePreviewCalificaciones, useImportarCalificaciones } from '../hooks/useImportacion'

interface ImportacionPageProps {
  comisionId: string
}

export function ImportacionPage({ comisionId }: ImportacionPageProps) {
  const [seleccionadas, setSeleccionadas] = useState<string[]>([])
  const [errorSeleccion, setErrorSeleccion] = useState<string | null>(null)
  const [mensajeExito, setMensajeExito] = useState<string | null>(null)

  const { data: actividades, isLoading } = usePreviewCalificaciones(comisionId)
  const importar = useImportarCalificaciones()

  function toggleActividad(id: string) {
    setErrorSeleccion(null)
    setSeleccionadas((prev) =>
      prev.includes(id) ? prev.filter((x) => x !== id) : [...prev, id],
    )
  }

  function handleImportar() {
    if (seleccionadas.length === 0) {
      setErrorSeleccion('Seleccioná al menos una actividad')
      return
    }
    setMensajeExito(null)
    importar.mutate(
      { comision_id: comisionId, actividad_ids: seleccionadas },
      {
        onSuccess: (result) => {
          setMensajeExito(result.mensaje)
          setSeleccionadas([])
        },
        onError: () => {
          setErrorSeleccion('Error al importar. Intentá de nuevo.')
        },
      },
    )
  }

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold text-text">Importar calificaciones</h1>

      {isLoading && <p className="text-text-muted">Cargando actividades...</p>}

      {actividades && actividades.length === 0 && (
        <p className="text-text-muted">No hay actividades disponibles para importar</p>
      )}

      {actividades && actividades.length > 0 && (
        <div className="space-y-4">
          <p className="text-sm text-text-muted">
            Seleccioná las actividades cuyas calificaciones querés importar desde Moodle.
          </p>

          <div className="space-y-2 rounded-lg border border-surface-subtle p-4">
            {actividades.map((act) => (
              <label key={act.id} className="flex cursor-pointer items-center gap-3 hover:bg-surface-subtle rounded p-2">
                <input
                  type="checkbox"
                  id={act.id}
                  aria-label={act.nombre}
                  checked={seleccionadas.includes(act.id)}
                  onChange={() => toggleActividad(act.id)}
                  className="h-4 w-4"
                />
                <span className="text-sm text-text">{act.nombre}</span>
                <span className="ml-auto text-xs text-text-muted">{act.tipo} · {act.fecha}</span>
              </label>
            ))}
          </div>

          {errorSeleccion && (
            <p className="text-sm text-red-600" role="alert">{errorSeleccion}</p>
          )}

          {mensajeExito && (
            <p className="text-sm text-green-600" role="status">{mensajeExito}</p>
          )}

          <button
            type="button"
            onClick={handleImportar}
            disabled={importar.isPending}
            className="rounded-lg bg-brand-600 px-4 py-2 text-sm font-medium text-white hover:bg-brand-700 disabled:opacity-50"
          >
            {importar.isPending ? 'Importando...' : 'Importar seleccionadas'}
          </button>
        </div>
      )}
    </div>
  )
}
