"""Parser de archivos LMS para importación de calificaciones (C-10).

Detecta el formato por extensión (xlsx/csv).
Identifica columnas de actividad:
  - Header termina en ' (Real)' → nota_numerica (RN-01)
  - Otras no-metadato → nota_textual
Metadatos ignorados: Nombre, Apellido(s), Dirección de correo, Número de ID, etc.
Retorna lista de dicts: {email, nombre, apellidos, actividad, nota_numerica, nota_textual}
"""

import csv
import io
from decimal import Decimal, InvalidOperation

_METADATO_PREFIJOS = {
    "nombre",
    "apellido",
    "dirección de correo",
    "direccion de correo",
    "email",
    "número de id",
    "numero de id",
    "id",
    "grupo",
    "departamento",
    "departament",
    "inicio",
    "fin",
    "última descarga",
}

_COL_EMAIL = {"dirección de correo", "direccion de correo", "email", "e-mail"}
_COL_NOMBRE = {"nombre", "first name", "firstname"}
_COL_APELLIDOS = {"apellido(s)", "apellidos", "last name", "lastname"}


class CalificacionParseError(Exception):
    """Error de parsing de archivo de calificaciones del LMS."""


def _es_metadato(header_lower: str) -> bool:
    return any(header_lower.startswith(p) for p in _METADATO_PREFIJOS)


def _parse_nota_numerica(valor: str | None) -> Decimal | None:
    if not valor or str(valor).strip() in ("-", "", "N/A", "n/a"):
        return None
    try:
        return Decimal(str(valor).strip().replace(",", "."))
    except InvalidOperation:
        return None


def _clasificar_columnas(headers: list[str]) -> tuple[str | None, str | None, str | None, list[tuple[str, str]]]:
    """Retorna (col_email, col_nombre, col_apellidos, [(col_orig, tipo)])."""
    col_email = None
    col_nombre = None
    col_apellidos = None
    actividades: list[tuple[str, str]] = []

    for h in headers:
        hl = h.strip().lower()
        if hl in _COL_EMAIL:
            col_email = h
        elif hl in _COL_NOMBRE:
            col_nombre = h
        elif hl in _COL_APELLIDOS:
            col_apellidos = h
        elif h.strip().endswith("(Real)"):
            actividades.append((h, "numerica"))
        elif not _es_metadato(hl) and hl:
            actividades.append((h, "textual"))

    return col_email, col_nombre, col_apellidos, actividades


def _procesar_filas(
    rows: list[dict],
    col_email: str | None,
    col_nombre: str | None,
    col_apellidos: str | None,
    actividades: list[tuple[str, str]],
) -> list[dict]:
    resultado = []
    for row in rows:
        email = str(row.get(col_email, "") or "").strip() if col_email else ""
        nombre = str(row.get(col_nombre, "") or "").strip() if col_nombre else ""
        apellidos = str(row.get(col_apellidos, "") or "").strip() if col_apellidos else ""

        if not email and not nombre:
            continue

        for col_orig, tipo in actividades:
            raw = row.get(col_orig, "")
            valor = str(raw).strip() if raw is not None else ""

            # Nombre limpio de actividad: quitar el sufijo " (Real)" si aplica
            nombre_actividad = col_orig.strip()
            if nombre_actividad.endswith(" (Real)"):
                nombre_actividad = nombre_actividad[: -len(" (Real)")].strip()

            if tipo == "numerica":
                nota_num = _parse_nota_numerica(valor)
                nota_txt = None
            else:
                nota_num = None
                nota_txt = valor if valor else None

            resultado.append({
                "email": email,
                "nombre": nombre,
                "apellidos": apellidos,
                "actividad": nombre_actividad,
                "nota_numerica": nota_num,
                "nota_textual": nota_txt,
            })

    return resultado


def _parse_xlsx(contents: bytes) -> list[dict]:
    import openpyxl

    try:
        wb = openpyxl.load_workbook(io.BytesIO(contents), read_only=True, data_only=True)
    except Exception as e:
        raise CalificacionParseError(f"No se pudo leer el archivo xlsx: {e}") from e

    ws = wb.active
    rows = list(ws.iter_rows(values_only=True))
    if not rows:
        raise CalificacionParseError("Archivo xlsx vacío")

    headers = [str(c).strip() if c is not None else "" for c in rows[0]]
    col_email, col_nombre, col_apellidos, actividades = _clasificar_columnas(headers)

    if not col_email and not col_nombre:
        raise CalificacionParseError(
            "No se encontró columna de alumno (Nombre o Dirección de correo)"
        )

    data_rows = []
    for raw_row in rows[1:]:
        data_rows.append({headers[j]: raw_row[j] for j in range(len(headers))})

    return _procesar_filas(data_rows, col_email, col_nombre, col_apellidos, actividades)


def _parse_csv(contents: bytes) -> list[dict]:
    for encoding in ("utf-8-sig", "utf-8", "latin-1"):
        try:
            text = contents.decode(encoding)
            break
        except UnicodeDecodeError:
            continue
    else:
        raise CalificacionParseError("No se pudo decodificar el CSV")

    reader = csv.DictReader(io.StringIO(text))
    if reader.fieldnames is None:
        raise CalificacionParseError("CSV vacío o sin headers")

    headers = list(reader.fieldnames)
    col_email, col_nombre, col_apellidos, actividades = _clasificar_columnas(headers)

    if not col_email and not col_nombre:
        raise CalificacionParseError(
            "No se encontró columna de alumno (Nombre o Dirección de correo)"
        )

    return _procesar_filas(list(reader), col_email, col_nombre, col_apellidos, actividades)


def parse_calificaciones_file(contents: bytes, filename: str) -> list[dict]:
    """Parsea un archivo de calificaciones del LMS (xlsx o csv).

    Returns:
        Lista de dicts con keys: email, nombre, apellidos, actividad,
        nota_numerica (Decimal | None), nota_textual (str | None).

    Raises:
        CalificacionParseError: si el formato es inválido o faltan columnas de alumno.
    """
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""

    if ext == "xlsx":
        return _parse_xlsx(contents)
    elif ext == "csv":
        return _parse_csv(contents)
    else:
        raise CalificacionParseError(
            f"Formato de archivo no soportado: '{ext}'. Use .xlsx o .csv"
        )
