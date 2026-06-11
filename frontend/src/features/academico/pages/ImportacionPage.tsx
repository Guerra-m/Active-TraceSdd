import { useRef, useState } from 'react'
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
      <h1 className="text-2xl font-bold text-text">Importar calificaciones</h1>

      {sinContexto && (
        <p className="text-text-muted">No hay asignación seleccionada.</p>
      )}

      {!sinContexto && (
        <div className="max-w-md space-y-4">
          <p className="text-sm text-text-muted">
            Subí el archivo de calificaciones exportado desde Moodle (xlsx o csv).
          </p>

          <div className="flex flex-col gap-1">
            <label htmlFor="archivo" className="text-sm font-medium text-text">
              Archivo de calificaciones
            </label>
            <input
              id="archivo"
              ref={fileRef}
              type="file"
              accept=".xlsx,.csv"
              onChange={handleFileChange}
              className="text-sm text-text"
            />
          </div>

          {errorMsg && (
            <p className="text-sm text-red-600" role="alert">{errorMsg}</p>
          )}

          <button
            type="button"
            onClick={handleImportar}
            disabled={importar.isPending}
            className="rounded-lg bg-brand-600 px-4 py-2 text-sm font-medium text-white hover:bg-brand-700 disabled:opacity-50"
          >
            {importar.isPending ? 'Importando...' : 'Importar'}
          </button>

          {resultado && (
            <div className="rounded-lg border border-green-200 bg-green-50 p-4 space-y-1">
              <p className="text-sm font-medium text-green-800">
                Importación exitosa: {resultado.filas} filas procesadas
              </p>
              {resultado.actividades.length > 0 && (
                <p className="text-xs text-green-700">
                  Actividades detectadas: {resultado.actividades.join(', ')}
                </p>
              )}
            </div>
          )}
        </div>
      )}
    </div>
  )
}
