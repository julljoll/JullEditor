#!/usr/bin/env bash
# =============================================================================
# Script de Aprovisionamiento Automatizado — Oracle Cloud (Always Free VM)
# Arquitectura: Ubuntu 22.04 / 24.04 LTS (x86_64 o ARM Ampere A1)
# =============================================================================

set -euo pipefail

echo "========================================================================="
echo "   INSTALACIÓN AUTOMATIZADA: GRANITE BLOG WRITER v3.0 (ORACLE CLOUD)"
echo "========================================================================="
echo ""

# 1. Actualizar repositorios del sistema
echo "[1/7] Actualizando paquetes del sistema..."
sudo apt-get update && sudo apt-get upgrade -y

# 2. Instalar Docker si no está presente
if ! command -v docker &> /dev/null; then
    echo "[2/7] Instalando Docker Engine oficial..."
    curl -fsSL https://get.docker.com | sh
    sudo usermod -aG docker "$USER"
    echo "✅ Docker instalado exitosamente."
else
    echo "[2/7] Docker ya se encuentra instalado."
fi

# 3. Instalar Docker Compose Plugin
if ! docker compose version &> /dev/null; then
    echo "[3/7] Instalando Docker Compose Plugin..."
    sudo apt-get install -y docker-compose-plugin
    echo "✅ Docker Compose Plugin instalado."
else
    echo "[3/7] Docker Compose Plugin verificado."
fi

# 4. Configurar cortafuegos iptables de Oracle Cloud (Puertos 80, 443, 8000)
echo "[4/7] Configurando reglas de iptables para tráfico web..."
sudo iptables -I INPUT -p tcp --dport 80 -j ACCEPT || true
sudo iptables -I INPUT -p tcp --dport 443 -j ACCEPT || true
sudo iptables -I INPUT -p tcp --dport 8000 -j ACCEPT || true

if command -v netfilter-persistent &> /dev/null; then
    sudo netfilter-persistent save || true
fi

# 5. Directorios de persistencia
REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
echo "[5/7] Configurando directorios de persistencia en: $REPO_DIR"
cd "$REPO_DIR"

mkdir -p RAG/inputs RAG/articulos logs docker/nginx

# 6. Levantar contenedores con Docker Compose
echo "[6/7] Levantando infraestructura con Docker Compose..."
cd docker
docker compose up -d --build

# 7. Descargar el modelo IBM Granite dentro del contenedor de Ollama
echo "[7/7] Esperando a que el contenedor de Ollama esté listo..."
sleep 8
echo "Descargando modelo IBM Granite (granite3.3:8b) en Ollama..."
docker exec -it granite-ollama ollama pull granite3.3:8b

# Verificación de salud
echo ""
echo "Verificando salud de la aplicación..."
sleep 5
curl -s http://localhost:8000/api/health || true

PUBLIC_IP=$(curl -s -4 ifconfig.me || echo "IP_PUBLICA")
echo ""
echo "========================================================================="
echo "   ✅ DESPLIEGUE FINALIZADO EXITOSAMENTE"
echo "   🌐 Acceso Directo Nginx: http://${PUBLIC_IP}"
echo "   🌐 Acceso Directo App:   http://${PUBLIC_IP}:8000"
echo "========================================================================="
