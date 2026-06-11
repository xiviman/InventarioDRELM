# main.py
from hardware import obtener_datos
from session import (
    obtener_institutos,
    obtener_instituto_en_progreso,
    crear_instituto,
    pausar_instituto,
    reanudar_instituto,
    finalizar_instituto,
    agregar_ambiente,
    completar_ambiente,
    obtener_resumen
)
import customtkinter as ctk
import csv
import os
from datetime import datetime
from tkinter import messagebox


import sys

# ── RUTAS RELATIVAS AL USB ──────────────────────────
# Funciona sin importar en qué letra quede el USB (D:, E:, F:...)
if getattr(sys, 'frozen', False):
    # Ejecutando como .exe (PyInstaller)
    BASE_DIR = os.path.dirname(sys.executable)
else:
    # Ejecutando como .py
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

CSV_PATH      = os.path.join(BASE_DIR, "inventario.csv")
SESSION_PATH  = os.path.join(BASE_DIR, "institutos.json")
REPORTES_DIR  = os.path.join(BASE_DIR, "reportes")

# Crear carpeta reportes si no existe
os.makedirs(REPORTES_DIR, exist_ok=True)



ctk.set_appearance_mode("light")
app = ctk.CTk()
app.title("Inventario DRELM")
app.geometry("1200x750")

# ─────────────────────────────────────────
# VARIABLES GLOBALES
# ─────────────────────────────────────────
equipo_actual        = 1
total_equipos_sesion = 0
instituto_id_actual  = None
datos_detectados     = None
lbl_equipo           = None
lbl_total            = None

CSV_PATH    = "inventario.csv"
CSV_COLUMNAS = [
    "FECHA", "INSTITUTO", "DIRECCION", "PABELLON", "PISO",
    "TIPO_AMBIENTE", "AMBIENTE", "EQUIPO_N",
    "CBI", "AÑO_COMPRA", "OFFICE", "ANTIVIRUS", "ESTADO",
    "MARCA", "MODELO", "SERIE", "NOMBRE_EQUIPO", "IP",
    "CPU", "CORE", "GENERACION", "GHZ",
    "RAM", "SSD", "HDD", "SO"
]

# ─────────────────────────────────────────
# CSV
# ─────────────────────────────────────────
def inicializar_csv():
    if not os.path.exists(CSV_PATH):
        with open(CSV_PATH, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=CSV_COLUMNAS)
            writer.writeheader()

def guardar_en_csv(fila: dict):
    with open(CSV_PATH, "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_COLUMNAS)
        writer.writerow(fila)

# ─────────────────────────────────────────
# UTILIDADES UI
# ─────────────────────────────────────────
def limpiar_ventana():
    for widget in app.winfo_children():
        widget.destroy()

# ─────────────────────────────────────────
# PANTALLA 0 — DASHBOARD
# ─────────────────────────────────────────
def mostrar_dashboard():
    limpiar_ventana()

    # —— HEADER ——
    header = ctk.CTkFrame(app, fg_color="#112b44", corner_radius=0)
    header.pack(fill="x")

    ctk.CTkLabel(
        header,
        text="📋 SISTEMA DE INVENTARIO DRELM",
        font=("Arial", 22, "bold"),
        text_color="white"
    ).pack(side="left", padx=20, pady=12)

    ctk.CTkLabel(
        header,
        text=f"🗓 {datetime.now().strftime('%d/%m/%Y')}",
        font=("Arial", 13),
        text_color="#aac8e4"
    ).pack(side="right", padx=20)

    # —— CUERPO ——
    cuerpo = ctk.CTkFrame(app)
    cuerpo.pack(fill="both", expand=True, padx=20, pady=20)

    # Título + botón nuevo
    fila_titulo = ctk.CTkFrame(cuerpo, fg_color="transparent")
    fila_titulo.pack(fill="x", pady=(0, 10))

    ctk.CTkLabel(
        fila_titulo,
        text="Institutos",
        font=("Arial", 18, "bold")
    ).pack(side="left")

    ctk.CTkButton(
        fila_titulo,
        text="+ Nuevo Instituto",
        width=160,
        fg_color="#1a7a3a",
        hover_color="#145c2b",
        command=mostrar_nuevo_instituto
    ).pack(side="right")

    # —— TABLA DE INSTITUTOS ——
    institutos = obtener_institutos()

    # Cabecera de tabla
    tabla_header = ctk.CTkFrame(cuerpo, fg_color="#d0d8e4", corner_radius=6)
    tabla_header.pack(fill="x", pady=(0, 2))

    for texto, peso in [
        ("#", 0.04),
        ("Instituto", 0.30),
        ("Dirección", 0.22),
        ("Ambientes", 0.12),
        ("Equipos", 0.10),
        ("Inicio", 0.12),
        ("Estado", 0.10)
    ]:
        ctk.CTkLabel(
            tabla_header,
            text=texto,
            font=("Arial", 12, "bold"),
            anchor="w"
        ).pack(side="left", padx=8, pady=6,
               expand=True if peso > 0.1 else False)

    # Scroll para las filas
    scroll = ctk.CTkScrollableFrame(cuerpo, height=380)
    scroll.pack(fill="both", expand=True)

    if not institutos:
        ctk.CTkLabel(
            scroll,
            text="No hay institutos registrados.\nPresiona '+ Nuevo Instituto' para comenzar.",
            font=("Arial", 14),
            text_color="gray"
        ).pack(pady=40)
    else:
        for i, inst in enumerate(institutos):
            _fila_instituto(scroll, i + 1, inst)

    # —— BOTÓN CONTINUAR si hay uno en progreso ——
    en_progreso = obtener_instituto_en_progreso()
    if en_progreso:
        banner = ctk.CTkFrame(app, fg_color="#1a4fa0", corner_radius=0)
        banner.pack(fill="x", side="bottom")

        ctk.CTkLabel(
            banner,
            text=f"▶  Tienes un inventario en progreso: {en_progreso['nombre']}",
            font=("Arial", 13, "bold"),
            text_color="white"
        ).pack(side="left", padx=20, pady=10)

        ctk.CTkButton(
            banner,
            text="Continuar →",
            fg_color="white",
            text_color="#1a4fa0",
            hover_color="#dde8ff",
            command=lambda: continuar_instituto(en_progreso)
        ).pack(side="right", padx=20, pady=8)

def _fila_instituto(parent, numero: int, inst: dict):
    """Dibuja una fila de la tabla de institutos."""

    # Color según estado
    colores = {
        "completado":  ("#e6f4ea", "#1a7a3a"),   # verde
        "en_progreso": ("#fff8e1", "#b8860b"),    # amarillo
        "pausado":     ("#e8f0fe", "#1a4fa0"),    # azul
    }
    bg, fg = colores.get(inst["estado"], ("#f5f5f5", "#333"))

    fila = ctk.CTkFrame(parent, fg_color=bg, corner_radius=6)
    fila.pack(fill="x", pady=2, padx=2)

    ambientes_completados = sum(
        1 for a in inst.get("ambientes", []) if a["completado"]
    )
    total_ambientes = len(inst.get("ambientes", []))

    estado_texto = {
        "completado":  "✅ Completado",
        "en_progreso": "🔄 En progreso",
        "pausado":     "⏸ Pausado",
    }.get(inst["estado"], inst["estado"])

    datos_fila = [
        str(numero),
        inst["nombre"],
        inst["direccion"],
        f"{ambientes_completados}/{total_ambientes}",
        str(inst["total_equipos"]),
        inst["fecha_inicio"][:10],
        estado_texto
    ]

    for texto in datos_fila:
        ctk.CTkLabel(
            fila,
            text=texto,
            font=("Arial", 12),
            text_color=fg,
            anchor="w"
        ).pack(side="left", padx=8, pady=6, expand=True)

    # Botones acción según estado
    frame_botones = ctk.CTkFrame(fila, fg_color="transparent")
    frame_botones.pack(side="right", padx=6)

    if inst["estado"] == "pausado":
        ctk.CTkButton(
            frame_botones,
            text="▶ Reanudar",
            width=100,
            height=28,
            fg_color="#1a4fa0",
            hover_color="#143a7a",
            command=lambda i=inst: _reanudar(i)
        ).pack(side="left", padx=3)

    elif inst["estado"] == "en_progreso":
        ctk.CTkButton(
            frame_botones,
            text="⏸ Pausar",
            width=90,
            height=28,
            fg_color="#b8860b",
            hover_color="#8b6508",
            command=lambda i=inst: _pausar(i)
        ).pack(side="left", padx=3)

    if inst["estado"] == "completado":
        ctk.CTkButton(
            frame_botones,
            text="📊 Resumen",
            width=100,
            height=28,
            fg_color="#555",
            hover_color="#333",
            command=lambda i=inst: mostrar_resumen_instituto(i["id"])
        ).pack(side="left", padx=3)

def _pausar(inst: dict):
    pausar_instituto(inst["id"])
    messagebox.showinfo(
        "⏸ Turno guardado",
        f"El instituto '{inst['nombre']}' quedó pausado.\n"
        f"Mañana puedes reanudarlo desde el Dashboard.\n"
        f"Todos los datos están guardados."
    )
    mostrar_dashboard()

def _reanudar(inst: dict):
    reanudar_instituto(inst["id"])
    continuar_instituto(inst)

def continuar_instituto(inst: dict):
    """Retoma un instituto pausado o en progreso."""
    global instituto_id_actual, instituto_actual
    global direccion_actual, total_equipos_sesion

    instituto_id_actual  = inst["id"]
    instituto_actual     = inst["nombre"]
    direccion_actual     = inst["direccion"]
    total_equipos_sesion = inst["total_equipos"]

    mostrar_configurar_ambiente()

# ─────────────────────────────────────────
# PANTALLA 1 — NUEVO INSTITUTO
# ─────────────────────────────────────────
def mostrar_nuevo_instituto():
    limpiar_ventana()

    frame = ctk.CTkFrame(app)
    frame.pack(fill="both", expand=True, padx=60, pady=60)

    ctk.CTkLabel(
        frame,
        text="🏫 NUEVO INSTITUTO",
        font=("Arial", 24, "bold")
    ).pack(pady=20)

    ctk.CTkLabel(frame, text="Nombre del Instituto").pack()
    entry_nombre = ctk.CTkEntry(frame, width=450, height=38)
    entry_nombre.pack(pady=8)
    entry_nombre.focus()

    ctk.CTkLabel(frame, text="Dirección").pack()
    entry_dir = ctk.CTkEntry(frame, width=450, height=38)
    entry_dir.pack(pady=8)

    def confirmar():
        nombre = entry_nombre.get().strip()
        direccion = entry_dir.get().strip()

        if not nombre:
            messagebox.showwarning("Atención", "El nombre del instituto es obligatorio.")
            return

        # Verificar si ya existe uno en progreso
        en_progreso = obtener_instituto_en_progreso()
        if en_progreso:
            messagebox.showwarning(
                "Instituto en progreso",
                f"Ya tienes un instituto en progreso:\n'{en_progreso['nombre']}'\n\n"
                f"Debes pausarlo o finalizarlo antes de crear uno nuevo."
            )
            return

        global instituto_id_actual, instituto_actual
        global direccion_actual, total_equipos_sesion

        inst = crear_instituto(nombre, direccion)
        instituto_id_actual  = inst["id"]
        instituto_actual     = inst["nombre"]
        direccion_actual     = inst["direccion"]
        total_equipos_sesion = 0

        mostrar_configurar_ambiente()

    ctk.CTkButton(
        frame,
        text="Continuar →",
        width=200,
        height=40,
        command=confirmar
    ).pack(pady=20)

    ctk.CTkButton(
        frame,
        text="← Volver",
        width=120,
        fg_color="transparent",
        border_width=1,
        text_color="#333",
        command=mostrar_dashboard
    ).pack()

# ─────────────────────────────────────────
# INICIO
# ─────────────────────────────────────────

# ─────────────────────────────────────────
# PANTALLA 2 — CONFIGURAR AMBIENTE
# ─────────────────────────────────────────
def mostrar_configurar_ambiente():
    global entry_pabellon, entry_piso, combo_tipo, entry_ambiente
    global equipo_actual

    equipo_actual = 1
    limpiar_ventana()

    # —— HEADER ——
    header = ctk.CTkFrame(app, fg_color="#112b44", corner_radius=0)
    header.pack(fill="x")

    ctk.CTkLabel(
        header,
        text=f"🏫 {instituto_actual}",
        font=("Arial", 16, "bold"),
        text_color="white"
    ).pack(side="left", padx=20, pady=10)

    ctk.CTkLabel(
        header,
        text=f"📦 Total equipos: {total_equipos_sesion}",
        font=("Arial", 13),
        text_color="#aac8e4"
    ).pack(side="right", padx=20)

    # —— CUERPO ——
    frame = ctk.CTkFrame(app)
    frame.pack(fill="both", expand=True, padx=80, pady=30)

    ctk.CTkLabel(
        frame,
        text="📍 CONFIGURAR AMBIENTE",
        font=("Arial", 22, "bold")
    ).pack(pady=(10, 20))

    # Resumen de ambientes ya completados
    resumen = obtener_resumen(instituto_id_actual)
    if resumen and resumen["ambientes"]:
        completados = [a for a in resumen["ambientes"] if a["completado"]]
        if completados:
            info = ctk.CTkFrame(frame, fg_color="#e6f4ea", corner_radius=8)
            info.pack(fill="x", pady=(0, 15))

            ctk.CTkLabel(
                info,
                text="✅ Ambientes completados en este instituto:",
                font=("Arial", 12, "bold"),
                text_color="#1a7a3a"
            ).pack(anchor="w", padx=12, pady=(8, 2))

            for amb in completados:
                ctk.CTkLabel(
                    info,
                    text=f"   • {amb['nombre']}  —  {amb['equipos']} equipos",
                    font=("Arial", 12),
                    text_color="#1a7a3a"
                ).pack(anchor="w", padx=12)

            ctk.CTkLabel(info, text="").pack(pady=4)

    # —— CAMPOS ——
    campos = ctk.CTkFrame(frame, fg_color="transparent")
    campos.pack()

    def campo(parent, label):
        ctk.CTkLabel(parent, text=label, anchor="w").pack(fill="x")
        entry = ctk.CTkEntry(parent, width=420, height=36)
        entry.pack(pady=(2, 10))
        return entry

    entry_pabellon = campo(campos, "Pabellón")
    entry_piso     = campo(campos, "Piso")

    ctk.CTkLabel(campos, text="Tipo de Ambiente", anchor="w").pack(fill="x")
    combo_tipo = ctk.CTkComboBox(
        campos,
        width=420,
        height=36,
        values=["Laboratorio", "Aula", "Oficina", "Dirección", "Biblioteca", "Otro"]
    )
    combo_tipo.pack(pady=(2, 10))

    entry_ambiente = campo(campos, "Nombre del Ambiente")

    # —— BOTONES ——
    fila_botones = ctk.CTkFrame(frame, fg_color="transparent")
    fila_botones.pack(pady=20)

    ctk.CTkButton(
        fila_botones,
        text="🚀 Iniciar Inventario",
        width=200,
        height=42,
        command=_iniciar_desde_ambiente
    ).pack(side="left", padx=10)

    ctk.CTkButton(
        fila_botones,
        text="🏁 Finalizar Instituto",
        width=180,
        height=42,
        fg_color="#8b0000",
        hover_color="#5c0000",
        command=_confirmar_finalizar_instituto
    ).pack(side="left", padx=10)

    ctk.CTkButton(
        fila_botones,
        text="⏸ Pausar Turno",
        width=150,
        height=42,
        fg_color="#b8860b",
        hover_color="#8b6508",
        command=_confirmar_pausar_turno
    ).pack(side="left", padx=10)

def _iniciar_desde_ambiente():
    global pabellon_actual, piso_actual, tipo_actual, ambiente_actual
    global datos_detectados

    pabellon_actual  = entry_pabellon.get().strip()
    piso_actual      = entry_piso.get().strip()
    tipo_actual      = combo_tipo.get()
    ambiente_actual  = entry_ambiente.get().strip()
    datos_detectados = None

    if not ambiente_actual:
        messagebox.showwarning("Atención", "El nombre del ambiente es obligatorio.")
        return

    agregar_ambiente(
        instituto_id_actual,
        ambiente_actual,
        pabellon_actual,
        piso_actual,
        tipo_actual
    )

    mostrar_inventario()

def _confirmar_pausar_turno():
    respuesta = messagebox.askyesno(
        "⏸ Pausar turno",
        f"¿Deseas pausar el inventario de '{instituto_actual}'?\n\n"
        f"Todos los datos están guardados.\n"
        f"Mañana puedes continuar desde el Dashboard."
    )
    if respuesta:
        pausar_instituto(instituto_id_actual)
        messagebox.showinfo(
            "Turno guardado",
            f"Hasta mañana 👋\n"
            f"Total equipos registrados hoy: {total_equipos_sesion}"
        )
        mostrar_dashboard()

def _confirmar_finalizar_instituto():
    resumen = obtener_resumen(instituto_id_actual)
    ambientes_count = len(resumen["ambientes"]) if resumen else 0

    respuesta = messagebox.askyesno(
        "🏁 Finalizar Instituto",
        f"¿Estás seguro de finalizar '{instituto_actual}'?\n\n"
        f"Ambientes registrados: {ambientes_count}\n"
        f"Total equipos: {total_equipos_sesion}\n\n"
        f"Se mostrará el resumen final."
    )
    if respuesta:
        finalizar_instituto(instituto_id_actual)
        mostrar_resumen_instituto(instituto_id_actual)

# ─────────────────────────────────────────
# PANTALLA 3 — INVENTARIO
# ─────────────────────────────────────────
def mostrar_inventario():
    global combo_estado, panel_resumen
    global entry_cbi, entry_anio, entry_office, entry_antivirus
    global lbl_equipo, lbl_total

    limpiar_ventana()

    # —— CABECERA ——
    cabecera = ctk.CTkFrame(app, fg_color="#112b44", corner_radius=0)
    cabecera.pack(fill="x")

    col_info = ctk.CTkFrame(cabecera, fg_color="transparent")
    col_info.pack(side="left", padx=15, pady=8)

    ctk.CTkLabel(
        col_info,
        text=f"🏫 {instituto_actual}",
        font=("Arial", 16, "bold"),
        text_color="white"
    ).pack(anchor="w")

    ctk.CTkLabel(
        col_info,
        text=f"🏢 {ambiente_actual}  |  📍 Piso {piso_actual}  |  🏗 Pabellón {pabellon_actual}",
        font=("Arial", 12),
        text_color="#aac8e4"
    ).pack(anchor="w")

    lbl_equipo = ctk.CTkLabel(
        col_info,
        text=f"🖥 Equipo #{equipo_actual}",
        font=("Arial", 13, "bold"),
        text_color="#7ec8f7"
    )
    lbl_equipo.pack(anchor="w")

    col_acciones = ctk.CTkFrame(cabecera, fg_color="transparent")
    col_acciones.pack(side="right", padx=15, pady=8)

    lbl_total = ctk.CTkLabel(
        col_acciones,
        text=f"📦 Total sesión: {total_equipos_sesion}",
        font=("Arial", 14, "bold"),
        text_color="#7ec8f7"
    )
    lbl_total.pack(anchor="e", pady=(0, 6))

    ctk.CTkButton(
        col_acciones,
        text="🏁 Finalizar Ambiente",
        fg_color="#8b0000",
        hover_color="#5c0000",
        width=170,
        command=_finalizar_ambiente
    ).pack(anchor="e")

    # —— CUERPO ——
    cuerpo = ctk.CTkFrame(app)
    cuerpo.pack(fill="both", expand=True, padx=10, pady=10)

    izquierda = ctk.CTkFrame(cuerpo)
    izquierda.pack(side="left", fill="both", expand=True, padx=10)

    derecha = ctk.CTkFrame(cuerpo)
    derecha.pack(side="right", fill="both", expand=True, padx=10)

    # —— IZQUIERDA ——
    ctk.CTkLabel(
        izquierda,
        text="📝 DATOS MANUALES",
        font=("Arial", 16, "bold")
    ).pack(pady=10)

    ctk.CTkLabel(izquierda, text="CBI").pack()
    entry_cbi = ctk.CTkEntry(izquierda, width=250)
    entry_cbi.pack(pady=5)
    entry_cbi.focus()

    ctk.CTkLabel(izquierda, text="Año Compra").pack()
    entry_anio = ctk.CTkEntry(izquierda, width=250)
    entry_anio.pack(pady=5)

    ctk.CTkLabel(izquierda, text="Office").pack()
    entry_office = ctk.CTkEntry(izquierda, width=250)
    entry_office.pack(pady=5)

    ctk.CTkLabel(izquierda, text="Antivirus").pack()
    entry_antivirus = ctk.CTkEntry(izquierda, width=250)
    entry_antivirus.pack(pady=5)

    ctk.CTkLabel(izquierda, text="Estado").pack()
    combo_estado = ctk.CTkComboBox(
        izquierda,
        width=250,
        values=["Bueno", "Regular", "Lento", "Malogrado", "No enciende"]
    )
    combo_estado.pack(pady=5)

    ctk.CTkButton(
        izquierda,
        text="🔍 Visualizar Equipo",
        width=200,
        command=visualizar_equipo
    ).pack(pady=(20, 5))

    ctk.CTkButton(
        izquierda,
        text="📤 Enviar",
        width=200,
        fg_color="#1a7a3a",
        hover_color="#145c2b",
        command=confirmar_envio
    ).pack(pady=5)

    # —— DERECHA ——
    ctk.CTkLabel(
        derecha,
        text="💻 DATOS DETECTADOS",
        font=("Arial", 16, "bold")
    ).pack(pady=10)

    panel_resumen = ctk.CTkTextbox(derecha, width=500, height=500)
    panel_resumen.pack(padx=10, pady=10, fill="both", expand=True)

def actualizar_cabecera():
    lbl_equipo.configure(text=f"🖥 Equipo #{equipo_actual}")
    lbl_total.configure(text=f"📦 Total sesión: {total_equipos_sesion}")

def visualizar_equipo():
    global datos_detectados

    datos_detectados = obtener_datos()

    resumen = f"""
INSTITUTO: {instituto_actual}
AMBIENTE:  {ambiente_actual}
PISO:      {piso_actual}
================================
CBI:       {entry_cbi.get()}
AÑO:       {entry_anio.get()}
OFFICE:    {entry_office.get()}
ANTIVIRUS: {entry_antivirus.get()}
ESTADO:    {combo_estado.get()}
================================
MARCA:      {datos_detectados['marca']}
MODELO:     {datos_detectados['modelo']}
SERIE:      {datos_detectados['serie']}
CPU:        {datos_detectados['cpu']}
CORE:       {datos_detectados['core']}
GENERACION: {datos_detectados['generacion']}
GHZ:        {datos_detectados['ghz']}
RAM:        {datos_detectados['ram']} GB
SSD:        {datos_detectados['ssd']} GB
HDD:        {datos_detectados['hdd']} GB
SO:         {datos_detectados['so']}
"""
    panel_resumen.delete("1.0", "end")
    panel_resumen.insert("1.0", resumen)

def confirmar_envio():
    if datos_detectados is None:
        messagebox.showwarning(
            "Atención",
            "Primero presiona '🔍 Visualizar Equipo' antes de enviar."
        )
        return

    respuesta = messagebox.askyesno(
        "Confirmar envío",
        f"¿Está seguro de enviar el Equipo #{equipo_actual}?\n\n"
        f"Instituto: {instituto_actual}\n"
        f"Ambiente:  {ambiente_actual}\n"
        f"CBI:       {entry_cbi.get()}"
    )
    if respuesta:
        enviar_a_csv()

def enviar_a_csv():
    global equipo_actual, total_equipos_sesion

    fila = {
        "FECHA":         datetime.now().strftime("%d/%m/%Y %H:%M"),
        "INSTITUTO":     instituto_actual,
        "DIRECCION":     direccion_actual,
        "PABELLON":      pabellon_actual,
        "PISO":          piso_actual,
        "TIPO_AMBIENTE": tipo_actual,
        "AMBIENTE":      ambiente_actual,
        "EQUIPO_N":      equipo_actual,
        "CBI":           entry_cbi.get(),
        "AÑO_COMPRA":    entry_anio.get(),
        "OFFICE":        entry_office.get(),
        "ANTIVIRUS":     entry_antivirus.get(),
        "ESTADO":        combo_estado.get(),
        "MARCA":         datos_detectados["marca"],
        "MODELO":        datos_detectados["modelo"],
        "SERIE":         datos_detectados["serie"],
        "NOMBRE_EQUIPO": datos_detectados["nombre_equipo"],
        "IP":            datos_detectados["ip"],
        "CPU":           datos_detectados["cpu"],
        "CORE":          datos_detectados["core"],
        "GENERACION":    datos_detectados["generacion"],
        "GHZ":           datos_detectados["ghz"],
        "RAM":           datos_detectados["ram"],
        "SSD":           datos_detectados["ssd"],
        "HDD":           datos_detectados["hdd"],
        "SO":            datos_detectados["so"],
    }

    inicializar_csv()
    guardar_en_csv(fila)

    equipo_actual        += 1
    total_equipos_sesion += 1

    actualizar_cabecera()

    messagebox.showinfo(
        "✅ Enviado",
        f"Equipo guardado correctamente.\n"
        f"Total sesión: {total_equipos_sesion}\n\n"
        f"Listo para el siguiente equipo."
    )

    entry_cbi.delete(0, "end")
    entry_anio.delete(0, "end")
    entry_office.delete(0, "end")
    entry_antivirus.delete(0, "end")
    combo_estado.set("Bueno")
    panel_resumen.delete("1.0", "end")

def _finalizar_ambiente():
    equipos_este_ambiente = equipo_actual - 1

    respuesta = messagebox.askyesno(
        "Finalizar Ambiente",
        f"¿Finalizar el ambiente '{ambiente_actual}'?\n\n"
        f"Equipos registrados: {equipos_este_ambiente}\n"
        f"Total sesión: {total_equipos_sesion}"
    )
    if respuesta:
        completar_ambiente(
            instituto_id_actual,
            ambiente_actual,
            equipos_este_ambiente
        )
        messagebox.showinfo(
            "✅ Ambiente completado",
            f"'{ambiente_actual}' finalizado con {equipos_este_ambiente} equipos.\n\n"
            f"Puedes configurar el siguiente ambiente."
        )
        mostrar_configurar_ambiente()

# ─────────────────────────────────────────
# PANTALLA 4 — RESUMEN FINAL INSTITUTO
# ─────────────────────────────────────────
def mostrar_resumen_instituto(instituto_id: str):
    limpiar_ventana()

    resumen = obtener_resumen(instituto_id)
    if not resumen:
        messagebox.showerror("Error", "No se encontró el instituto.")
        mostrar_dashboard()
        return

    # —— HEADER ——
    header = ctk.CTkFrame(app, fg_color="#112b44", corner_radius=0)
    header.pack(fill="x")

    ctk.CTkLabel(
        header,
        text=f"📊 RESUMEN FINAL — {resumen['nombre']}",
        font=("Arial", 18, "bold"),
        text_color="white"
    ).pack(side="left", padx=20, pady=12)

    # —— CUERPO ——
    cuerpo = ctk.CTkFrame(app)
    cuerpo.pack(fill="both", expand=True, padx=25, pady=20)

    # Info general
    info = ctk.CTkFrame(cuerpo, fg_color="#e8f0fe", corner_radius=8)
    info.pack(fill="x", pady=(0, 15))

    ctk.CTkLabel(
        info,
        text=f"🏫 {resumen['nombre']}",
        font=("Arial", 16, "bold"),
        text_color="#1a4fa0"
    ).pack(anchor="w", padx=15, pady=(10, 2))

    ctk.CTkLabel(
        info,
        text=f"📍 {resumen['direccion']}   |   🗓 Inicio: {resumen['fecha_inicio']}   |   🏁 Fin: {resumen['fecha_fin'] or 'En progreso'}",
        font=("Arial", 12),
        text_color="#333"
    ).pack(anchor="w", padx=15, pady=(0, 10))

    # Totales destacados
    totales = ctk.CTkFrame(cuerpo, fg_color="transparent")
    totales.pack(fill="x", pady=(0, 15))

    def tarjeta(parent, titulo, valor, color):
        t = ctk.CTkFrame(parent, fg_color=color, corner_radius=10)
        t.pack(side="left", expand=True, fill="both", padx=6)
        ctk.CTkLabel(
            t,
            text=str(valor),
            font=("Arial", 32, "bold"),
            text_color="white"
        ).pack(pady=(14, 2))
        ctk.CTkLabel(
            t,
            text=titulo,
            font=("Arial", 12),
            text_color="white"
        ).pack(pady=(0, 14))

    tarjeta(totales, "Total Equipos",   resumen["total_equipos"],           "#1a7a3a")
    tarjeta(totales, "Ambientes",       len(resumen["ambientes"]),          "#1a4fa0")
    tarjeta(totales, "Completados",
            sum(1 for a in resumen["ambientes"] if a["completado"]),        "#555")

    # Tabla por ambiente
    ctk.CTkLabel(
        cuerpo,
        text="Detalle por ambiente:",
        font=("Arial", 14, "bold")
    ).pack(anchor="w", pady=(0, 6))

    tabla_h = ctk.CTkFrame(cuerpo, fg_color="#d0d8e4", corner_radius=6)
    tabla_h.pack(fill="x")

    for col in ["Ambiente", "Pabellón", "Piso", "Tipo", "Equipos", "Estado"]:
        ctk.CTkLabel(
            tabla_h,
            text=col,
            font=("Arial", 12, "bold"),
            anchor="w"
        ).pack(side="left", padx=10, pady=6, expand=True)

    scroll = ctk.CTkScrollableFrame(cuerpo, height=180)
    scroll.pack(fill="both", expand=True, pady=2)

    for amb in resumen["ambientes"]:
        bg = "#e6f4ea" if amb["completado"] else "#fff8e1"
        fila = ctk.CTkFrame(scroll, fg_color=bg, corner_radius=4)
        fila.pack(fill="x", pady=1)

        for texto in [
            amb["nombre"],
            amb.get("pabellon", "—"),
            amb.get("piso", "—"),
            amb.get("tipo", "—"),
            str(amb["equipos"]),
            "✅ Listo" if amb["completado"] else "🔄 Pendiente"
        ]:
            ctk.CTkLabel(
                fila,
                text=texto,
                font=("Arial", 12),
                anchor="w"
            ).pack(side="left", padx=10, pady=5, expand=True)

    # —— BOTONES ——
    fila_botones = ctk.CTkFrame(cuerpo, fg_color="transparent")
    fila_botones.pack(pady=15)

    ctk.CTkButton(
        fila_botones,
        text="📥 Exportar Excel",
        width=180,
        height=40,
        fg_color="#1a4fa0",
        hover_color="#143a7a",
        command=lambda: exportar_excel(instituto_id)
    ).pack(side="left", padx=10)

    ctk.CTkButton(
        fila_botones,
        text="← Volver al Dashboard",
        width=180,
        height=40,
        fg_color="transparent",
        border_width=1,
        text_color="#333",
        command=mostrar_dashboard
    ).pack(side="left", padx=10)

def exportar_excel(instituto_id: str):
    """Placeholder — se implementa en PASO 4."""
    messagebox.showinfo(
        "Próximamente",
        "La exportación a Excel se implementa en el siguiente paso."
    )


mostrar_dashboard()
app.mainloop()