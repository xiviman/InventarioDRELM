import wmi
import psutil
import socket
import cpuinfo
import re

def obtener_datos():

    c = wmi.WMI()

    datos = {}

    # Marca y modelo
    for pc in c.Win32_ComputerSystem():
        datos["marca"] = pc.Manufacturer
        datos["modelo"] = pc.Model

    # Serie
    for bios in c.Win32_BIOS():
        datos["serie"] = bios.SerialNumber

    # Nombre equipo
    datos["nombre_equipo"] = socket.gethostname()

    # IP
    try:
        datos["ip"] = socket.gethostbyname(socket.gethostname())
    except:
        datos["ip"] = "No disponible"

    # RAM
    datos["ram"] = round(
        psutil.virtual_memory().total / (1024**3)
    )

    # CPU
    cpu = cpuinfo.get_cpu_info()
    cpu_name = cpu["brand_raw"]

    datos["cpu"] = cpu_name

    # Core
    core_match = re.search(
        r'(i3|i5|i7|i9)',
        cpu_name,
        re.IGNORECASE
    )

    if core_match:
        datos["core"] = core_match.group(1).upper()
    else:
        datos["core"] = "No detectado"

    # Generación
    gen_match = re.search(
        r'i[3579]-(\d{4,5})',
        cpu_name
    )

    if gen_match:

        numero = gen_match.group(1)

        if numero.startswith(
            ("10","11","12","13","14","15")
        ):
            datos["generacion"] = numero[:2]
        else:
            datos["generacion"] = numero[0]

    else:
        datos["generacion"] = "No detectada"

    # GHz
    ghz_match = re.search(
        r'@\s([\d\.]+)GHz',
        cpu_name
    )

    if ghz_match:
        datos["ghz"] = ghz_match.group(1)
    else:
        datos["ghz"] = "No detectado"

    # Sistema Operativo
    for os in c.Win32_OperatingSystem():
        datos["so"] = (
            f"{os.Caption} {os.OSArchitecture}"
        )

    # Discos
    ssd_total = 0
    hdd_total = 0

    for disk in c.Win32_DiskDrive():

        nombre = disk.Model.lower()

        capacidad = round(
            int(disk.Size) / (1024**3)
        )

        if "ssd" in nombre or "nvme" in nombre:
            ssd_total += capacidad
        else:
            hdd_total += capacidad

    datos["ssd"] = ssd_total
    datos["hdd"] = hdd_total

    return datos