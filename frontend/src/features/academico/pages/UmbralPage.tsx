import { useState, useEffect } from 'react'
import { useUmbral, useActualizarUmbral } from '../hooks/useUmbral'

interface UmbralPageProps {
  asignacionId: string
  materiaId: string
}

export function UmbralPage({ asignacionId, materiaId }: UmbralPageProps) {
  const { data: umbral, isLoading } = useUmbral(asignacionId, materiaId)
  const [porcentaje, setPorcentaje] = useState<number>(60)
  const [error, setError] = useState<string | null>(null)
  const [exito, setExito] = useState<string | null>(null)

  const actualizar = useActualizarUmbral(asignacionId, materiaId)

  useEffect(() => {
    if (umbral) {
      setPorcentaje(umbral.umbral_pct)
    }
  }, [umbral])

  const sinContexto = !asignacionId || !materiaId

  function handleGuardar() {
    setError(null)
    setExito(null)
    if (porcentaje < 1 || porcentaje > 100) {
      setError('El valor debe estar entre 1 y 100')
      return
    }
    actualizar.mutate(
      { umbral_pct: porcentaje },
      {
        onSuccess: () => setExito('Umbral guardado correctamente'),
        onError: () => setError('Error al guardar el umbral'),
      },
    )
  }

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold text-text">Configuración de umbral</h1>

      {sinContexto && (
        <p className="text-text-muted">No hay asignación seleccionada.</p>
      )}

      {isLoading && !sinContexto && <p className="text-text-muted">Cargando configuración...</p>}

      {umbral && (
        <div className="max-w-sm space-y-4 rounded-lg border border-surface-subtle p-6">
          <p className="text-sm text-text-muted">
            Porcentaje mínimo de aprobación ({umbral.es_default ? 'valor por defecto' : 'configurado'}).
          </p>

          <div className="flex flex-col gap-1">
            <label htmlFor="porcentaje" className="text-sm font-medium text-text">
              Umbral (%)
            </label>
            <input
              id="porcentaje"
              type="number"
              min={1}
              max={100}
              value={porcentaje}
              onChange={(e) => {
                setPorcentaje(Number(e.target.value))
                setError(null)
              }}
              className="rounded-lg border border-surface-subtle px-3 py-2 text-sm text-text focus:outline-none focus:ring-2 focus:ring-brand-500"
            />
          </div>

          {umbral.valores_aprobatorios.length > 0 && (
            <p className="text-xs text-text-muted">
              Valores aprobatorios: {umbral.valores_aprobatorios.join(', ')}
            </p>
          )}

          {error && <p className="text-sm text-red-600" role="alert">{error}</p>}
          {exito && <p className="text-sm text-green-600" role="status">{exito}</p>}

          <button
            type="button"
            onClick={handleGuardar}
            disabled={actualizar.isPending}
            className="rounded-lg bg-brand-600 px-4 py-2 text-sm font-medium text-white hover:bg-brand-700 disabled:opacity-50"
          >
            {actualizar.isPending ? 'Guardando...' : 'Guardar umbral'}
          </button>
        </div>
      )}
    </div>
  )
}
