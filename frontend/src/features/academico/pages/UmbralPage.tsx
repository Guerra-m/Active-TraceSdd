import { useState, useEffect } from 'react'
import { useUmbral, useActualizarUmbral } from '../hooks/useUmbral'

interface UmbralPageProps {
  comisionId: string
}

export function UmbralPage({ comisionId }: UmbralPageProps) {
  const { data: umbral, isLoading } = useUmbral(comisionId)
  const [porcentaje, setPorcentaje] = useState<number>(60)
  const [error, setError] = useState<string | null>(null)
  const [exito, setExito] = useState<string | null>(null)

  const umbralId = umbral?.id ?? ''
  const actualizar = useActualizarUmbral(umbralId, comisionId)

  useEffect(() => {
    if (umbral) {
      setPorcentaje(umbral.porcentaje)
    }
  }, [umbral])

  function handleGuardar() {
    setError(null)
    setExito(null)
    if (porcentaje < 0 || porcentaje > 100) {
      setError('El valor debe estar entre 0 y 100')
      return
    }
    actualizar.mutate(
      { porcentaje },
      {
        onSuccess: () => setExito('Umbral guardado correctamente'),
        onError: () => setError('Error al guardar el umbral'),
      },
    )
  }

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold text-text">Configuración de umbral</h1>

      {isLoading && <p className="text-text-muted">Cargando configuración...</p>}

      {umbral && (
        <div className="max-w-sm space-y-4 rounded-lg border border-surface-subtle p-6">
          <p className="text-sm text-text-muted">
            Porcentaje mínimo de aprobación para la comisión.
          </p>

          <div className="flex flex-col gap-1">
            <label htmlFor="porcentaje" className="text-sm font-medium text-text">
              Umbral (%)
            </label>
            <input
              id="porcentaje"
              type="number"
              min={0}
              max={100}
              value={porcentaje}
              onChange={(e) => {
                setPorcentaje(Number(e.target.value))
                setError(null)
              }}
              className="rounded-lg border border-surface-subtle px-3 py-2 text-sm text-text focus:outline-none focus:ring-2 focus:ring-brand-500"
            />
          </div>

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
