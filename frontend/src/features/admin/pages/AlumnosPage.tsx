import { Link } from 'react-router-dom'
import { RequirePermission } from '@/shared/components/RequirePermission'

function AlumnosContent() {
  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold">Alumnos</h1>

      <div className="rounded-lg border border-blue-200 bg-blue-50 p-5">
        <h2 className="mb-2 font-semibold text-blue-800">¿Cómo se gestionan los alumnos?</h2>
        <p className="text-sm text-blue-700">
          Los alumnos en activia-trace se organizan por <strong>materia × cohorte</strong> a través
          del padrón. Cada materia tiene su propio padrón versionado: podés importarlo desde un
          archivo xlsx/csv o sincronizarlo directamente desde Moodle.
        </p>
      </div>

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
        <Link
          to="/profesor/importar"
          className="flex flex-col gap-2 rounded-lg border border-border p-5 transition-colors hover:bg-surface-subtle"
        >
          <span className="text-lg font-semibold">Importar padrón</span>
          <span className="text-sm text-gray-500">
            Cargá o actualizá el padrón de alumnos para una materia desde un archivo o desde Moodle.
          </span>
          <span className="mt-auto text-sm font-medium text-blue-600">Ir a Importar →</span>
        </Link>

        <Link
          to="/profesor/atrasados"
          className="flex flex-col gap-2 rounded-lg border border-border p-5 transition-colors hover:bg-surface-subtle"
        >
          <span className="text-lg font-semibold">Ver alumnos atrasados</span>
          <span className="text-sm text-gray-500">
            Visualizá qué alumnos tienen entregas pendientes o calificaciones por debajo del umbral.
          </span>
          <span className="mt-auto text-sm font-medium text-blue-600">Ir a Atrasados →</span>
        </Link>

        <Link
          to="/coloquios"
          className="flex flex-col gap-2 rounded-lg border border-border p-5 transition-colors hover:bg-surface-subtle"
        >
          <span className="text-lg font-semibold">Coloquios</span>
          <span className="text-sm text-gray-500">
            Gestioná las convocatorias de coloquio y las reservas de alumnos.
          </span>
          <span className="mt-auto text-sm font-medium text-blue-600">Ir a Coloquios →</span>
        </Link>

        <Link
          to="/profesor/comunicaciones"
          className="flex flex-col gap-2 rounded-lg border border-border p-5 transition-colors hover:bg-surface-subtle"
        >
          <span className="text-lg font-semibold">Comunicaciones</span>
          <span className="text-sm text-gray-500">
            Enviá comunicaciones masivas a los alumnos atrasados de tu comisión.
          </span>
          <span className="mt-auto text-sm font-medium text-blue-600">Ir a Comunicaciones →</span>
        </Link>
      </div>
    </div>
  )
}

export function AlumnosPage() {
  return (
    <RequirePermission permission="padron:importar">
      <div className="p-6">
        <AlumnosContent />
      </div>
    </RequirePermission>
  )
}
