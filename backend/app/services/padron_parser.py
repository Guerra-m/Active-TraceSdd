"""Parser de archivos xlsx/csv para importación de padrón (C-09).

Detecta el formato por extensión del filename.
Normaliza nombres de columna a lowercase/strip.
Valida columnas mínimas requeridas: nombre, apellidos, email.
Columnas opcionales: comision, regional.

Raises:
    PadronParseError: si el archivo tiene formato inválido, columnas faltantes,
                      o no se puede decodificar.
"""

import csv
import io
from typing import Any


class PadronParseError(Exception):
    """Error de parsing de archivo de padrón."""


_REQUIRED_COLS = {"nombre", "apellidos", "email"}
_OPTIONAL_COLS = {"comision", "regional"}
_ALL_COLS = _REQUIRED_COLS | _OPTIONAL_COLS


def _normalize_cols(headers: list[str]) -> dict[str, str]:
    """Mapea nombre normalizado → nombre original en el header."""
    return {h.strip().lower(): h for h in headers}


def _validate_headers(normalized: dict[str, str]) -> None:
    missing = _REQUIRED_COLS - set(normalized.keys())
    if missing:
        raise PadronParseError(
            f"Columnas requeridas faltantes: {', '.join(sorted(missing))}. "
            f"Columnas requeridas: nombre, apellidos, email."
        )


def _row_to_dict(row: dict[str, Any], col_map: dict[str, str]) -> dict[str, str | None]:
    """Extrae los campos del padrón de una fila normalizada."""
    def get(key: str) -> str | None:
        orig = col_map.get(key)
        if orig is None:
            return None
        val = row.get(orig, "")
        return str(val).strip() if val else None

    nombre = get("nombre")
    apellidos = get("apellidos")
    email = get("email")

    if not nombre:
        raise PadronParseError("Columna 'nombre' vacía en una fila")
    if not apellidos:
        raise PadronParseError("Columna 'apellidos' vacía en una fila")
    if not email:
        raise PadronParseError("Columna 'email' vacía en una fila")

    return {
        "nombre": nombre,
        "apellidos": apellidos,
        "email": email,
        "comision": get("comision"),
        "regional": get("regional"),
    }


def _parse_xlsx(contents: bytes) -> list[dict]:
    import openpyxl

    try:
        wb = openpyxl.load_workbook(io.BytesIO(contents), read_only=True, data_only=True)
    except Exception as e:
        raise PadronParseError(f"No se pudo leer el archivo xlsx: {e}") from e

    ws = wb.active
    rows = list(ws.iter_rows(values_only=True))
    if not rows:
        raise PadronParseError("Archivo xlsx vacío")

    headers = [str(c).strip() if c is not None else "" for c in rows[0]]
    col_map = _normalize_cols(headers)
    _validate_headers(col_map)

    result = []
    for i, raw_row in enumerate(rows[1:], start=2):
        row_dict = {headers[j]: raw_row[j] for j in range(len(headers))}
        try:
            result.append(_row_to_dict(row_dict, col_map))
        except PadronParseError as e:
            raise PadronParseError(f"Fila {i}: {e}") from e

    return result


def _parse_csv(contents: bytes) -> list[dict]:
    # Intenta utf-8, fallback a latin-1
    for encoding in ("utf-8-sig", "utf-8", "latin-1"):
        try:
            text = contents.decode(encoding)
            break
        except UnicodeDecodeError:
            continue
    else:
        raise PadronParseError("No se pudo decodificar el CSV (intentado utf-8 y latin-1)")

    reader = csv.DictReader(io.StringIO(text))
    if reader.fieldnames is None:
        raise PadronParseError("CSV vacío o sin headers")

    col_map = _normalize_cols(list(reader.fieldnames))
    _validate_headers(col_map)

    result = []
    for i, row in enumerate(reader, start=2):
        try:
            result.append(_row_to_dict(dict(row), col_map))
        except PadronParseError as e:
            raise PadronParseError(f"Fila {i}: {e}") from e

    return result


def parse_padron_file(contents: bytes, filename: str) -> list[dict]:
    """Parsea un archivo de padrón (xlsx o csv) y retorna lista de dicts.

    Args:
        contents: Contenido del archivo en bytes.
        filename: Nombre del archivo (usado para detectar formato por extensión).

    Returns:
        Lista de dicts con claves: nombre, apellidos, email, comision, regional.

    Raises:
        PadronParseError: si el formato es inválido, columnas requeridas faltan,
                          o una fila tiene datos inválidos.
    """
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""

    if ext == "xlsx":
        return _parse_xlsx(contents)
    elif ext == "csv":
        return _parse_csv(contents)
    else:
        raise PadronParseError(
            f"Formato de archivo no soportado: '{ext}'. Use .xlsx o .csv"
        )
