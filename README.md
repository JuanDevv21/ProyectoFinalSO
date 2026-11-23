# Monitoreo de una infraestructura Docker

Nginx distribuye solicitudes entre tres réplicas Flask. Prometheus consulta las réplicas, el exportador de Nginx y cAdvisor. Grafana carga automáticamente el tablero Infraestructura Docker.

## Requisitos y arranque

Usa Docker Desktop iniciado en modo de contenedores Linux, o Docker Engine Linux con Compose v2. Para la prueba de carga instala k6 en el host, por ejemplo con `winget install k6 --source winget` en Windows. Abre una terminal nueva después de instalarlo.

Desde la raíz del proyecto:

```powershell
docker version
docker compose version
docker compose config --quiet
docker compose up -d --build
docker compose ps
```

Si PowerShell no encuentra Docker, en una instalación por usuario agrega a la sesión la carpeta con el ejecutable:

```powershell
$env:Path += ";$env:LOCALAPPDATA\Programs\DockerDesktop\resources\bin"
```

| Servicio | Acceso desde el host |
| --- | --- |
| Nginx | http://127.0.0.1:8080/ |
| Prometheus | http://127.0.0.1:9090/targets |
| Grafana | http://127.0.0.1:3000/d/infraestructura |

En el primer inicio Grafana usa `admin` como usuario y contraseña, salvo que definas `GRAFANA_ADMIN_PASSWORD` en un archivo `.env` antes de crear el volumen.

## Verificación

Abre Nginx en el navegador. Luego verifica la distribución con 30 solicitudes en PowerShell:

```powershell
1..30 | ForEach-Object {
  (Invoke-RestMethod http://127.0.0.1:8080/).instancia
} | Group-Object | Select-Object Name, Count
```

Comprueba que Prometheus muestre cinco objetivos activos. En su página de consultas verifica `up` y `nginx_up`. En Grafana selecciona los últimos cinco minutos. Bajo carga deben aparecer las tres series de solicitudes y latencia. Los paneles de cAdvisor muestran CPU, memoria, red, espacio ocupado y actividad de lectura y escritura según las métricas que exponga el motor Linux.

## Prueba de carga

```powershell
New-Item -ItemType Directory resultados -Force | Out-Null
k6 run --summary-export resultados/k6.json pruebas/carga.js
```

La prueba programa 40 solicitudes por segundo durante 60 segundos. Requiere menos de 1 % de errores HTTP, p95 inferior a 250 ms, más del 99 % de comprobaciones correctas, cero iteraciones descartadas y tráfico en cada réplica. Usa el p95 de k6 para medir la latencia desde el host y el de Grafana para observar el tiempo de procesamiento del backend.


### Alternativas de ejecución

La prueba incluida en Python 3 usa solo la biblioteca estándar y mide desde el host. Ejecuta python pruebas/carga_host.py. Produce resultados/host.json.

También puedes ejecutar k6 en la red interna de Compose. Esta variante mide desde un contenedor y usa el puerto interno de Nginx.

```powershell
New-Item -ItemType Directory resultados -Force | Out-Null
docker run --rm --network proyecto-monitoreo_monitoreo -e TEST_URL=http://nginx/ --mount "type=bind,source=$PWD/pruebas,target=/pruebas,readonly" --mount "type=bind,source=$PWD/resultados,target=/resultados" grafana/k6:2.4.0 run --summary-export /resultados/k6.json /pruebas/carga.js
```
Consulta `docker compose logs --tail 100` si un objetivo no responde. En Windows, comprueba que Docker Desktop use contenedores Linux. cAdvisor necesita acceso al cgroup, al socket Docker y al almacenamiento del motor. Si faltan métricas de disco según el controlador de almacenamiento, revisa el registro de cAdvisor y consulta `container_fs_usage_bytes` en Prometheus. El panel Actividad de disco muestra lecturas y escrituras cuando Linux registra actividad de bloque por contenedor. Los puertos publicados se limitan a loopback.

```powershell
docker compose down
```

Los volúmenes nombrados conservan el historial de Prometheus y la configuración de Grafana.

## Referencias

- [Docker Compose](https://docs.docker.com/compose/)
- [NGINX Prometheus Exporter](https://github.com/nginx/nginx-prometheus-exporter)
- [cAdvisor en Docker](https://github.com/google/cadvisor/blob/master/docs/running.md)
- [Instalación de k6](https://grafana.com/docs/k6/latest/set-up/install-k6/)
