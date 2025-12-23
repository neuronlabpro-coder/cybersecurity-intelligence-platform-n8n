#!/bin/bash
# Arrancar CVEFind en puerto 5001
cd /app/cvefind.com && python app.py &

# Arrancar DGSSI en puerto 5002
cd /app/dgssi && python app.py &

# Arrancar OpenCVE en puerto 5000
cd /app/opencve.io && python app.py &

# Mantener el contenedor vivo
wait
