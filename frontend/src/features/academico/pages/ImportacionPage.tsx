import { useRef, useState } from 'react'
import {
  Upload,
  FileSpreadsheet,
  CheckCircle2,
  AlertCircle,
  TrendingUp,
  Filter,
  Download,
  ChevronRight,
  MoreVertical,
  CheckCircle,
  XCircle,
  Timer,
} from 'lucide-react'
import { useImportarCalificaciones } from '../hooks/useImportacion'

interface ImportacionPageProps {
  asignacionId: string
  materiaId: string
}

export function ImportacionPage({ asignacionId, materiaId }: ImportacionPageProps) {
  const fileRef = useRef<HTMLInputElement>(null)
  const [archivo, setArchivo] = useState<File | null>(null)
  const [resultado, setResultado] = useState<{ filas: number; actividades: string[] } | null>(null)
  const [errorMsg, setErrorMsg] = useState<string | null>(null)
  const [filtroLog, setFiltroLog] = useState<'todos' | 'pendiente' | 'completado'>('todos')

  const importar = useImportarCalificaciones()

  const sinContexto = !asignacionId || !materiaId

  function handleFileChange(e: React.ChangeEvent<HTMLInputElement>) {
    setResultado(null)
    setErrorMsg(null)
    setArchivo(e.target.files?.[0] ?? null)
  }

  function handleImportar() {
    if (!archivo) {
      setErrorMsg('Seleccioná un archivo xlsx o csv')
      return
    }
    setErrorMsg(null)
    setResultado(null)
    importar.mutate(
      { asignacionId, materiaId, archivo },
      {
        onSuccess: (res) => {
          setResultado({ filas: res.filas_importadas, actividades: res.actividades_detectadas })
          setArchivo(null)
          if (fileRef.current) fileRef.current.value = ''
        },
        onError: () => setErrorMsg('Error al importar. Verificá el formato del archivo.'),
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
            <span className="text-primary font-medium">Registro de Guardias</span>
          </nav>
          <h1 className="text-[30px] font-semibold leading-tight tracking-tight text-primary">
            Importar Calificaciones
          </h1>
          <p className="text-sm text-[#4b6076] mt-0.5">
            Importación de notas desde Moodle para la asignación activa.
          </p>
        </div>
        <div className="flex gap-3">
          <button
            type="button"
            onClick={() => setFiltroLog(filtroLog === 'todos' ? 'completado' : 'todos')}
            className="flex items-center gap-2 border border-[#c4c6cd] px-4 py-2 rounded-lg bg-white hover:bg-[#efedef] transition-colors text-sm font-medium text-[#1b1c1d]"
          >
            <Filter className="w-4 h-4" />
            <span>Filtros</span>
          </button>
          <button
            type="button"
            onClick={() => {
              if (!resultado) return
              const rows = [
                'Archivo,Filas,Actividades,Asignación,Estado',
                `"${archivo?.name ?? 'calificaciones.xlsx'}","${resultado.filas}","${resultado.actividades.join('; ')}","${asignacionId}","Validado"`,
              ].join('\n')
              const blob = new Blob([rows], { type: 'text/csv;charset=utf-8;' })
              const url = URL.createObjectURL(blob)
              const a = document.createElement('a')
              a.href = url
              a.download = `importacion_${new Date().toISOString().slice(0, 10)}.csv`
              a.click()
              URL.revokeObjectURL(url)
            }}
            disabled={!resultado}
            className="flex items-center gap-2 border border-[#c4c6cd] px-4 py-2 rounded-lg bg-white hover:bg-[#efedef] transition-colors text-sm font-medium text-[#1b1c1d] disabled:opacity-50"
          >
            <Download className="w-4 h-4" />
            <span>Exportar CSV</span>
          </button>
        </div>
      </div>

      {sinContexto ? (
        <div className="rounded-xl border border-[#c4c6cd] bg-[#f5f3f4] p-8 text-center">
          <AlertCircle className="w-10 h-10 text-[#43474c] mx-auto mb-3 opacity-50" />
          <p className="text-sm text-[#43474c]">No hay asignación seleccionada.</p>
        </div>
      ) : (
        <>
          {/* Bento Stats */}
          <div className="grid grid-cols-4 gap-6">
            <div className="bg-white border border-[#c4c6cd] rounded-xl p-4 flex flex-col gap-2">
              <span className="text-[11px] font-bold tracking-[0.05em] text-[#4b6076] uppercase">
                Guardias Activas
              </span>
              <span className="text-[30px] font-semibold text-primary leading-none">
                {resultado ? resultado.filas : '—'}
              </span>
              <div className="flex items-center gap-1 text-green-600 text-xs">
                <TrendingUp className="w-3 h-3" />
                <span>Filas importadas</span>
              </div>
            </div>
            <div className="bg-white border border-[#c4c6cd] rounded-xl p-4 flex flex-col gap-2">
              <span className="text-[11px] font-bold tracking-[0.05em] text-[#4b6076] uppercase">
                Tasa de Conformidad
              </span>
              <span className="text-[30px] font-semibold text-primary leading-none">98.2%</span>
              <div className="w-full bg-[#efedef] rounded-full h-1.5 mt-1">
                <div className="bg-primary h-full rounded-full w-[98%]" />
              </div>
            </div>
            <div className="bg-white border border-[#c4c6cd] rounded-xl p-4 flex flex-col gap-2">
              <span className="text-[11px] font-bold tracking-[0.05em] text-[#4b6076] uppercase">
                Actividades Detectadas
              </span>
              <span className="text-[30px] font-semibold text-primary leading-none">
                {resultado ? resultado.actividades.length : '—'}
              </span>
              <span className="text-xs text-[#74777d]">
                {resultado?.actividades.length
                  ? resultado.actividades.slice(0, 2).join(', ')
                  : 'Sin datos aún'}
              </span>
            </div>
            <div className="bg-white border border-[#c4c6cd] rounded-xl p-4 flex flex-col gap-2">
              <span className="text-[11px] font-bold tracking-[0.05em] text-[#4b6076] uppercase">
                Turno Actual
              </span>
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-full bg-[#cce2fc] flex items-center justify-center text-[#50657b]">
                  <Timer className="w-5 h-5" />
                </div>
                <div>
                  <p className="font-medium text-sm text-primary">
                    {asignacionId.slice(0, 6) || 'Bloque D4'}
                  </p>
                  <p className="text-xs text-[#74777d]">Asignación activa</p>
                </div>
              </div>
            </div>
          </div>

          {/* Upload card */}
          <div className="bg-white border border-[#c4c6cd] rounded-xl overflow-hidden shadow-sm">
            <div className="flex items-center justify-between px-6 py-4 border-b border-[#c4c6cd] bg-white">
              <h3 className="font-medium text-sm text-primary">Importar archivo Moodle</h3>
            </div>

            <div className="p-6">
              <p className="text-sm text-[#43474c] mb-6">
                Subí el archivo de calificaciones exportado desde Moodle (xlsx o csv). Las
                actividades se detectan automáticamente.
              </p>

              {/* Drop zone */}
              <label
                htmlFor="archivo"
                className="flex flex-col items-center justify-center gap-3 rounded-xl border-2 border-dashed border-[#c4c6cd] p-10 cursor-pointer hover:border-primary hover:bg-[#f5f3f4] transition-all group"
              >
                <div className="w-12 h-12 rounded-full bg-[#cce2fc] flex items-center justify-center group-hover:bg-primary/10 transition-colors">
                  <FileSpreadsheet className="w-6 h-6 text-primary" />
                </div>
                <div className="text-center">
                  <p className="font-medium text-sm text-primary">
                    {archivo ? archivo.name : 'Seleccioná un archivo'}
                  </p>
                  <p className="text-xs text-[#43474c] mt-1">xlsx o csv — exportado desde Moodle</p>
                </div>
                <input
                  id="archivo"
                  ref={fileRef}
                  type="file"
                  accept=".xlsx,.csv"
                  onChange={handleFileChange}
                  className="sr-only"
                />
              </label>

              {errorMsg && (
                <div
                  role="alert"
                  className="mt-4 flex items-center gap-2 rounded-lg border border-[#ffdad6] bg-[#ffdad6]/40 px-4 py-3 text-sm text-[#93000a]"
                >
                  <AlertCircle className="w-4 h-4 shrink-0" />
                  <span>{errorMsg}</span>
                </div>
              )}

              {resultado && (
                <div className="mt-4 rounded-lg border border-green-200 bg-green-50 p-4 space-y-1">
                  <div className="flex items-center gap-2">
                    <CheckCircle2 className="w-4 h-4 text-green-700 shrink-0" />
                    <p className="text-sm font-medium text-green-800">
                      Importación exitosa: {resultado.filas} filas procesadas
                    </p>
                  </div>
                  {resultado.actividades.length > 0 && (
                    <p className="text-xs text-green-700 ml-6">
                      Actividades: {resultado.actividades.join(', ')}
                    </p>
                  )}
                </div>
              )}

              <button
                type="button"
                onClick={handleImportar}
                disabled={importar.isPending || !archivo}
                className="mt-6 flex items-center gap-2 rounded-lg bg-primary px-5 py-2.5 text-sm font-medium text-white hover:opacity-90 disabled:opacity-50 transition-opacity"
              >
                <Upload className="w-4 h-4" />
                {importar.isPending ? 'Importando...' : 'Importar'}
              </button>
            </div>
          </div>

          {/* Tabla logs (estructura visual del diseño de guardias) */}
          <div className="bg-white border border-[#c4c6cd] rounded-xl overflow-hidden shadow-sm">
            <div className="flex items-center justify-between px-6 py-4 border-b border-[#c4c6cd] bg-white">
              <div className="flex items-center gap-4">
                <h3 className="font-medium text-sm text-primary">Registros de importación</h3>
                <div className="flex rounded-lg border border-[#c4c6cd] overflow-hidden text-xs">
                  {(['todos', 'pendiente', 'completado'] as const).map((f) => (
                    <button
                      key={f}
                      type="button"
                      onClick={() => setFiltroLog(f)}
                      className={`px-4 py-1 capitalize border-l border-[#c4c6cd] first:border-l-0 hover:bg-[#efedef] ${
                        filtroLog === f ? 'bg-[#efedef] text-primary font-medium' : 'bg-white text-[#4b6076]'
                      }`}
                    >
                      {f.charAt(0).toUpperCase() + f.slice(1)}
                    </button>
                  ))}
                </div>
              </div>
              <div className="flex items-center gap-2">
                <span className="text-xs text-[#74777d]">Página 1 de 1</span>
                <div className="flex gap-1">
                  <button type="button" disabled className="w-8 h-8 flex items-center justify-center border border-[#c4c6cd] rounded hover:bg-[#efedef] disabled:opacity-50 disabled:cursor-not-allowed">
                    <ChevronRight className="w-3 h-3 rotate-180 text-[#43474c]" />
                  </button>
                  <button type="button" disabled className="w-8 h-8 flex items-center justify-center border border-[#c4c6cd] rounded hover:bg-[#efedef] disabled:opacity-50 disabled:cursor-not-allowed">
                    <ChevronRight className="w-3 h-3 text-[#43474c]" />
                  </button>
                </div>
              </div>
            </div>

            <div className="overflow-x-auto">
              <table className="w-full text-left border-collapse">
                <thead>
                  <tr className="bg-[#f5f3f4] border-b border-[#c4c6cd]">
                    <th className="px-6 py-4 text-[11px] font-bold tracking-[0.05em] text-[#4b6076] uppercase">
                      Archivo
                    </th>
                    <th className="px-6 py-4 text-[11px] font-bold tracking-[0.05em] text-[#4b6076] uppercase">
                      Filas
                    </th>
                    <th className="px-6 py-4 text-[11px] font-bold tracking-[0.05em] text-[#4b6076] uppercase">
                      Actividades
                    </th>
                    <th className="px-6 py-4 text-[11px] font-bold tracking-[0.05em] text-[#4b6076] uppercase">
                      Asignación
                    </th>
                    <th className="px-6 py-4 text-[11px] font-bold tracking-[0.05em] text-[#4b6076] uppercase">
                      Asistencia
                    </th>
                    <th className="px-6 py-4 text-[11px] font-bold tracking-[0.05em] text-[#4b6076] uppercase">
                      Estado
                    </th>
                    <th className="px-6 py-4 text-[11px] font-bold tracking-[0.05em] text-[#4b6076] uppercase">
                      Acciones
                    </th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-[#c4c6cd]">
                  {resultado ? (
                    <tr className="hover:bg-[#f5f3f4] transition-colors group">
                      <td className="px-6 py-4">
                        <div className="flex items-center gap-3">
                          <div className="w-8 h-8 rounded-full bg-[#d1e4fb] text-primary flex items-center justify-center font-bold text-xs">
                            MO
                          </div>
                          <div>
                            <div className="font-medium text-sm text-primary">
                              {archivo?.name ?? 'calificaciones.xlsx'}
                            </div>
                            <div className="text-xs text-[#74777d]">Moodle Export</div>
                          </div>
                        </div>
                      </td>
                      <td className="px-6 py-4">
                        <div className="flex flex-col">
                          <span className="font-mono text-xs text-primary">{resultado.filas}</span>
                          <span className="text-xs text-[#74777d]">filas</span>
                        </div>
                      </td>
                      <td className="px-6 py-4">
                        <span className="bg-[#cce2fc] text-[#50657b] px-2 py-1 rounded text-xs font-medium">
                          {resultado.actividades.length} detectadas
                        </span>
                      </td>
                      <td className="px-6 py-4 text-sm text-primary">
                        {asignacionId.slice(0, 8)}
                      </td>
                      <td className="px-6 py-4">
                        <div className="flex items-center gap-1 text-green-700 text-sm">
                          <CheckCircle className="w-4 h-4" />
                          Procesado
                        </div>
                      </td>
                      <td className="px-6 py-4">
                        <span className="bg-green-100 text-green-800 px-3 py-1 rounded-full text-xs font-bold uppercase tracking-tight">
                          Validado
                        </span>
                      </td>
                      <td className="px-6 py-4">
                        <button
                          type="button"
                          onClick={() => setResultado(null)}
                          title="Eliminar registro"
                          className="text-[#4b6076] hover:text-primary"
                        >
                          <MoreVertical className="w-4 h-4" />
                        </button>
                      </td>
                    </tr>
                  ) : (
                    <tr>
                      <td
                        colSpan={7}
                        className="px-6 py-10 text-center text-sm text-[#43474c]"
                      >
                        No hay importaciones registradas. Subí un archivo para comenzar.
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>

            <div className="bg-[#f5f3f4] px-6 py-4 flex items-center justify-between border-t border-[#c4c6cd]">
              <div className="flex items-center gap-4">
                <div className="flex items-center gap-2">
                  <span className="text-xs text-[#74777d]">Filas por página:</span>
                  <select className="bg-white border border-[#c4c6cd] rounded px-2 py-0.5 text-xs focus:ring-primary focus:border-primary">
                    <option>10</option>
                    <option>20</option>
                    <option>50</option>
                  </select>
                </div>
              </div>
              <div className="flex gap-4 items-center">
                <span className="text-xs text-[#74777d]">
                  {resultado ? `1 de 1 registros` : '0 registros'}
                </span>
                <div className="flex items-center gap-2">
                  <button type="button" disabled className="p-1 hover:bg-[#efedef] rounded disabled:opacity-50 disabled:cursor-not-allowed">
                    <ChevronRight className="w-4 h-4 rotate-180 text-[#43474c]" />
                  </button>
                  <button type="button" disabled className="p-1 hover:bg-[#efedef] rounded disabled:opacity-50 disabled:cursor-not-allowed">
                    <ChevronRight className="w-4 h-4 text-[#43474c]" />
                  </button>
                </div>
              </div>
            </div>
          </div>

          {/* Conflictos / Advertencias */}
          {errorMsg && (
            <div className="bg-white border border-[#c4c6cd] rounded-xl overflow-hidden shadow-sm">
              <div className="p-6 border-b border-[#c4c6cd] flex justify-between items-center bg-white">
                <div>
                  <h4 className="font-medium text-sm text-primary">Conflictos detectados</h4>
                  <p className="text-xs text-[#74777d]">
                    Inconsistencias identificadas durante la importación.
                  </p>
                </div>
              </div>
              <div className="p-6 space-y-4">
                <div className="flex items-start gap-4 p-4 rounded-lg border border-[#ffdad6] bg-[#ffdad6]/10">
                  <XCircle className="w-5 h-5 text-[#ba1a1a] mt-0.5 shrink-0" />
                  <div className="flex-1">
                    <p className="font-medium text-sm text-[#93000a]">Error de formato</p>
                    <p className="text-xs text-[#50657b] mt-0.5">{errorMsg}</p>
                  </div>
                  <div className="flex gap-2">
                    <button
                      type="button"
                      onClick={() => setErrorMsg(null)}
                      className="px-4 py-1 border border-[#74777d] text-xs rounded hover:bg-white transition-colors"
                    >
                      Descartar
                    </button>
                    <button
                      type="button"
                      onClick={handleImportar}
                      disabled={importar.isPending}
                      className="px-4 py-1 bg-primary text-white text-xs rounded hover:opacity-90 disabled:opacity-50"
                    >
                      Reintentar
                    </button>
                  </div>
                </div>
              </div>
            </div>
          )}
        </>
      )}
    </div>
  )
}
