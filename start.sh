#!/bin/bash

# 1. Arrancar CVEFind en puerto 5001 (Nombre real: cvefind_server.py)
echo "Iniciando CVEFind..."
cd /app/cvefind.com && python cvefind_server.py &

# 2. Arrancar DGSSI en puerto 5002 (Nombre real: dgssi_scraper.py)
echo "Iniciando DGSSI..."
cd /app/dgssi && python dgssi_scraper.py &

# 3. Arrancar OpenCVE en puerto 5000 (Nombre real: simple_cve_server.py)
echo "Iniciando OpenCVE..."
cd /app/opencve.io && python simple_cve_server.py &

# Esperar a que los procesos arranquen y mantener el contenedor vivo
wait
