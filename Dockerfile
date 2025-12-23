# Usamos una imagen ligera de Python
FROM python:3.9-slim

# Directorio de trabajo
WORKDIR /app

# Copiamos todo el código del repo al contenedor
COPY . .

# Instalamos las dependencias de los 3 servicios
RUN pip install --no-cache-dir -r cvefind.com/requirements.txt
RUN pip install --no-cache-dir -r dgssi/requirements.txt
RUN pip install --no-cache-dir -r opencve.io/requirements.txt

# Exponemos los puertos que usan los scripts
EXPOSE 5000 5001 5002

# Script para arrancar los 3 servicios a la vez en segundo plano
COPY start.sh /start.sh
RUN chmod +x /start.sh

CMD ["/start.sh"]
