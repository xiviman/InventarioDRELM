# session.py
# Maneja el archivo institutos.json
# Guarda el estado de cada instituto, ambientes y totales

import json
import os
from datetime import datetime
# session.py
import json
import os
import sys
from datetime import datetime

# ── RUTA RELATIVA ──
if getattr(sys, 'frozen', False):
    BASE_DIR = os.path.dirname(sys.executable)
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

SESSION_PATH = os.path.join(BASE_DIR, "institutos.json")

SESSION_PATH = "institutos.json"

# ─────────────────────────────────────────
# ESTRUCTURA BASE
# ─────────────────────────────────────────

def _estructura_vacia():
    return {"institutos": []}

def _cargar():
    if not os.path.exists(SESSION_PATH):
        _guardar(_estructura_vacia())
    
    # ← NUEVO: si existe pero está vacío o corrupto, lo reinicia
    try:
        with open(SESSION_PATH, "r", encoding="utf-8") as f:
            contenido = f.read().strip()
            if not contenido:
                _guardar(_estructura_vacia())
                return _estructura_vacia()
            return json.loads(contenido)
    except json.JSONDecodeError:
        _guardar(_estructura_vacia())
        return _estructura_vacia()

def _guardar(data: dict):
    with open(SESSION_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

# ─────────────────────────────────────────
# INSTITUTOS
# ─────────────────────────────────────────

def obtener_institutos() -> list:
    """Devuelve la lista completa de institutos."""
    return _cargar()["institutos"]

def obtener_instituto_en_progreso() -> dict | None:
    """Devuelve el instituto con estado 'en_progreso', o None."""
    for inst in obtener_institutos():
        if inst["estado"] == "en_progreso":
            return inst
    return None

def crear_instituto(nombre: str, direccion: str) -> dict:
    """Crea un nuevo instituto y lo guarda."""
    data = _cargar()
    nuevo = {
        "id":            _generar_id(),
        "nombre":        nombre,
        "direccion":     direccion,
        "fecha_inicio":  datetime.now().strftime("%d/%m/%Y %H:%M"),
        "fecha_fin":     None,
        "estado":        "en_progreso",
        "ambientes":     [],
        "total_equipos": 0
    }
    data["institutos"].append(nuevo)
    _guardar(data)
    return nuevo

def finalizar_instituto(instituto_id: str):
    """Marca un instituto como completado."""
    data = _cargar()
    for inst in data["institutos"]:
        if inst["id"] == instituto_id:
            inst["estado"]    = "completado"
            inst["fecha_fin"] = datetime.now().strftime("%d/%m/%Y %H:%M")
            break
    _guardar(data)

def pausar_instituto(instituto_id: str):
    """
    Pausa un instituto (fin de turno).
    Los datos se conservan, solo cambia el estado.
    """
    data = _cargar()
    for inst in data["institutos"]:
        if inst["id"] == instituto_id:
            inst["estado"] = "pausado"
            break
    _guardar(data)

def reanudar_instituto(instituto_id: str):
    """Reactiva un instituto pausado."""
    data = _cargar()
    for inst in data["institutos"]:
        if inst["id"] == instituto_id:
            inst["estado"] = "en_progreso"
            break
    _guardar(data)

# ─────────────────────────────────────────
# AMBIENTES
# ─────────────────────────────────────────

def agregar_ambiente(instituto_id: str, nombre: str, pabellon: str,
                     piso: str, tipo: str) -> dict:
    """Agrega un ambiente nuevo a un instituto."""
    data = _cargar()
    nuevo_ambiente = {
        "nombre":     nombre,
        "pabellon":   pabellon,
        "piso":       piso,
        "tipo":       tipo,
        "fecha":      datetime.now().strftime("%d/%m/%Y"),
        "equipos":    0,
        "completado": False
    }
    for inst in data["institutos"]:
        if inst["id"] == instituto_id:
            inst["ambientes"].append(nuevo_ambiente)
            break
    _guardar(data)
    return nuevo_ambiente

def completar_ambiente(instituto_id: str, nombre_ambiente: str, total_equipos: int):
    """
    Marca un ambiente como completado y actualiza
    el total de equipos del instituto.
    """
    data = _cargar()
    for inst in data["institutos"]:
        if inst["id"] == instituto_id:
            for amb in inst["ambientes"]:
                if amb["nombre"] == nombre_ambiente:
                    amb["equipos"]    = total_equipos
                    amb["completado"] = True
                    break
            inst["total_equipos"] = sum(
                a["equipos"] for a in inst["ambientes"]
            )
            break
    _guardar(data)

# ─────────────────────────────────────────
# RESUMEN
# ─────────────────────────────────────────

def obtener_resumen(instituto_id: str) -> dict | None:
    """
    Devuelve un resumen del instituto:
    nombre, ambientes completados, total equipos.
    """
    for inst in obtener_institutos():
        if inst["id"] == instituto_id:
            return {
                "nombre":        inst["nombre"],
                "direccion":     inst["direccion"],
                "fecha_inicio":  inst["fecha_inicio"],
                "fecha_fin":     inst["fecha_fin"],
                "estado":        inst["estado"],
                "total_equipos": inst["total_equipos"],
                "ambientes":     inst["ambientes"]
            }
    return None

# ─────────────────────────────────────────
# UTILIDADES
# ─────────────────────────────────────────

def _generar_id() -> str:
    """ID único basado en timestamp."""
    return datetime.now().strftime("%Y%m%d%H%M%S%f")