import { useState, useEffect } from 'react'
import { SlidersHorizontal, Info, CheckCircle2, AlertCircle, ChevronRight } from 'lucide-react'
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
      {/* Header */}
      <div className="flex justify-between items-end">
        <div>
          <nav className="flex items-center gap-1 text-xs text-[#43474c] mb-1">
            <span>Gestión Académica</span>
            <ChevronRight className="w-3 h-3" />
            <span className="text-primary font-medium">Configuración de Umbral</span>
          </nav>
          <h1 className="text-[30px] font-semibold leading-tight tracking-tight text-primary">
            Configuración de Umbral
          </h1>
          <p className="text-sm text-[#4b6076] mt-0.5">
            Porcentaje mínimo de aprobación para la asignación seleccionada.
          </p>
        </div>
      </div>

      {sinContexto && (
        <div className="rounded-xl border border-[#c4c6cd] bg-[#f5f3f4] p-8 text-center">
          <AlertCircle className="w-10 h-10 text-[#43474c] mx-auto mb-3 opacity-50" />
          <p className="text-sm text-[#43474c]">No hay asignación seleccionada.</p>
        </div>
      )}

      {isLoading && !sinContexto && (
        <div className="rounded-xl border border-[#c4c6cd] bg-[#f5f3f4] p-8 text-center">
          <p className="text-sm text-[#43474c]">Cargando configuración...</p>
        </div>
      )}

      {umbral && (
        <div className="grid grid-cols-12 gap-6">
          {/* Main config card */}
          <div className="col-span-12 lg:col-span-7 bg-white border border-[#c4c6cd] rounded-xl overflow-hidden shadow-sm">
            <div className="px-6 py-4 border-b border-[#c4c6cd] flex items-center gap-3 bg-white">
              <div className="p-2 bg-[#cce2fc] rounded-lg">
                <SlidersHorizontal className="w-4 h-4 text-primary" />
              </div>
              <h3 className="font-medium text-sm text-primary">Porcentaje de aprobación</h3>
            </div>

            <div className="p-6 space-y-6">
              <p className="text-sm text-[#43474c]">
                Porcentaje mínimo de aprobación
                {umbral.es_default ? (
                  <span className="ml-1 text-xs font-medium text-[#50657b] bg-[#cce2fc] px-2 py-0.5 rounded-full">
                    valor por defecto
                  </span>
                ) : (
                  <span className="ml-1 text-xs font-medium text-green-700 bg-green-100 px-2 py-0.5 rounded-full">
                    configurado
                  </span>
                )}
              </p>

              {/* Slider visual */}
              <div className="space-y-3">
                <div className="flex justify-between items-center">
                  <label
                    className="text-xs font-bold tracking-[0.05em] text-[#43474c] uppercase"
                    htmlFor="porcentaje"
                  >
                    Umbral (%)
                  </label>
                  <span className="font-mono text-2xl font-bold text-primary">{porcentaje}%</span>
                </div>

                <input
                  id="porcentaje"
                  type="range"
                  min={1}
                  max={100}
                  value={porcentaje}
                  onChange={(e) => {
                    setPorcentaje(Number(e.target.value))
                    setError(null)
                    setExito(null)
                  }}
                  className="w-full h-2 bg-[#efedef] rounded-full appearance-none cursor-pointer accent-primary"
                />

                <div className="flex justify-between text-xs text-[#43474c]">
                  <span>1%</span>
                  <span>50%</span>
                  <span>100%</span>
                </div>
              </div>

              {/* Input numérico */}
              <div className="space-y-1">
                <label
                  className="text-xs font-bold tracking-[0.05em] text-[#43474c] uppercase"
                  htmlFor="porcentaje-num"
                >
                  Valor exacto
                </label>
                <input
                  id="porcentaje-num"
                  type="number"
                  min={1}
                  max={100}
                  value={porcentaje}
                  onChange={(e) => {
                    setPorcentaje(Number(e.target.value))
                    setError(null)
                    setExito(null)
                  }}
                  className="w-32 rounded-lg border border-[#c4c6cd] px-3 py-2 text-sm text-primary focus:outline-none focus:ring-2 focus:ring-primary"
                />
              </div>

              {/* Valores aprobatorios */}
              {umbral.valores_aprobatorios.length > 0 && (
                <div className="rounded-lg bg-[#f5f3f4] p-4 border border-[#c4c6cd]">
                  <p className="text-xs font-bold tracking-[0.05em] text-[#43474c] uppercase mb-2">
                    Valores aprobatorios
                  </p>
                  <div className="flex flex-wrap gap-2">
                    {umbral.valores_aprobatorios.map((v) => (
                      <span
                        key={v}
                        className="px-2 py-1 bg-white border border-[#c4c6cd] rounded text-xs font-mono text-primary"
                      >
                        {v}
                      </span>
                    ))}
                  </div>
                </div>
              )}

              {/* Feedback */}
              {error && (
                <div
                  role="alert"
                  className="flex items-center gap-2 rounded-lg border border-[#ffdad6] bg-[#ffdad6]/40 px-4 py-3 text-sm text-[#93000a]"
                >
                  <AlertCircle className="w-4 h-4 shrink-0" />
                  <span>{error}</span>
                </div>
              )}
              {exito && (
                <div
                  role="status"
                  className="flex items-center gap-2 rounded-lg border border-green-200 bg-green-50 px-4 py-3 text-sm text-green-800"
                >
                  <CheckCircle2 className="w-4 h-4 shrink-0" />
                  <span>{exito}</span>
                </div>
              )}

              <button
                type="button"
                onClick={handleGuardar}
                disabled={actualizar.isPending}
                className="flex items-center gap-2 rounded-lg bg-primary px-5 py-2.5 text-sm font-medium text-white hover:opacity-90 disabled:opacity-50 transition-opacity"
              >
                <SlidersHorizontal className="w-4 h-4" />
                {actualizar.isPending ? 'Guardando...' : 'Guardar umbral'}
              </button>
            </div>
          </div>

          {/* Info panel */}
          <div className="col-span-12 lg:col-span-5 space-y-4">
            <div className="bg-primary text-white rounded-xl p-6 relative overflow-hidden">
              <div className="absolute -right-8 -top-8 opacity-10 pointer-events-none">
                <SlidersHorizontal className="w-40 h-40" />
              </div>
              <h3 className="font-medium text-sm mb-1 relative z-10">Asignación activa</h3>
              <p className="text-xs text-[#96a9be] mb-4 relative z-10">
                El umbral aplica a todos los alumnos de esta asignación.
              </p>
              <div className="space-y-3 relative z-10">
                <div className="bg-white/10 backdrop-blur-sm p-3 rounded-lg border border-white/20">
                  <p className="font-mono text-xs text-white/70">Asignación ID</p>
                  <p className="font-medium text-sm mt-0.5">{asignacionId.slice(0, 12)}</p>
                </div>
                <div className="bg-white/10 backdrop-blur-sm p-3 rounded-lg border border-white/20">
                  <p className="font-mono text-xs text-white/70">Materia ID</p>
                  <p className="font-medium text-sm mt-0.5">{materiaId.slice(0, 12)}</p>
                </div>
              </div>
            </div>

            <div className="bg-white border border-[#c4c6cd] rounded-xl p-6">
              <div className="flex items-center gap-2 mb-4">
                <Info className="w-4 h-4 text-[#4b6076]" />
                <h4 className="font-medium text-sm text-primary">Resumen rápido</h4>
              </div>
              <ul className="space-y-3">
                <li className="flex justify-between items-center text-sm">
                  <span className="text-[#43474c]">Umbral actual</span>
                  <span className="font-medium font-mono text-primary">{porcentaje}%</span>
                </li>
                <li className="flex justify-between items-center text-sm">
                  <span className="text-[#43474c]">Tipo</span>
                  <span className="font-medium text-primary">
                    {umbral.es_default ? 'Por defecto' : 'Personalizado'}
                  </span>
                </li>
                <li className="flex justify-between items-center text-sm">
                  <span className="text-[#43474c]">Valores aprobatorios</span>
                  <span className="font-medium text-primary">
                    {umbral.valores_aprobatorios.length > 0
                      ? umbral.valores_aprobatorios.length
                      : '—'}
                  </span>
                </li>
              </ul>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
