import wmi
import psutil
import socket
import cpuinfo
import re

c = wmi.WMI()

print("=" * 60)

# MARCA Y MODELO
for pc in c.Win32_ComputerSystem():
    print("Marca:", pc.Manufacturer)
    print("Modelo:", pc.Model)

# SERIE
for bios in c.Win32_BIOS():
    print("Serie:", bios.SerialNumber)

# NOMBRE EQUIPO
print("Nombre Equipo:", socket.gethostname())

# IP
try:
    ip = socket.gethostbyname(socket.gethostname())
except:
    ip = "No disponible"

print("IP:", ip)

# RAM
ram = round(psutil.virtual_memory().total / (1024**3))
print("RAM:", ram, "GB")

# CPU
cpu = cpuinfo.get_cpu_info()
cpu_name = cpu["brand_raw"]

print("CPU Completo:", cpu_name)

# Core
core_match = re.search(r'(i3|i5|i7|i9)', cpu_name, re.IGNORECASE)

if core_match:
    core = core_match.group(1).upper()
else:
    core = "No detectado"

print("Core:", core)

# Generación Intel
gen_match = re.search(r'i[3579]-(\d{4,5})', cpu_name)

if gen_match:
    numero = gen_match.group(1)

    if numero.startswith(("10", "11", "12", "13", "14", "15")):
        generacion = numero[:2]
    else:
        generacion = numero[0]
else:
    generacion = "No detectada"

print("Generación:", generacion)

# GHz nominal
ghz_match = re.search(r'@\s([\d\.]+)GHz', cpu_name)

if ghz_match:
    ghz = ghz_match.group(1)
else:
    ghz = "No detectado"

print("Velocidad:", ghz, "GHz")

# SISTEMA OPERATIVO
for os in c.Win32_OperatingSystem():
    print("Sistema Operativo:",
          f"{os.Caption} {os.OSArchitecture}")
    
ssd_total = 0
hdd_total = 0

for disk in c.Win32_DiskDrive():

    nombre = disk.Model.lower()
    capacidad = round(int(disk.Size) / (1024**3))

    if "ssd" in nombre or "nvme" in nombre:
        ssd_total += capacidad
    else:
        hdd_total += capacidad

print("SSD:", ssd_total, "GB")
print("HDD:", hdd_total, "GB")

print("=" * 60)