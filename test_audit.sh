#!/bin/bash

# Colores para output
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${GREEN}=== Iniciando Prueba de Auditoría Financiera ===${NC}\n"

# 1. Verificar que estamos en el directorio correcto
if [ ! -f "requirements.txt" ]; then
    echo -e "${RED}❌ Error: No se encuentra requirements.txt${NC}"
    echo "Por favor, ejecuta este script desde el directorio raíz del proyecto"
    exit 1
fi

# 2. Crear y activar entorno virtual si no existe
if [ ! -d ".venv" ]; then
    echo "Creando entorno virtual..."
    python3 -m venv .venv
fi

echo "Activando entorno virtual..."
source .venv/bin/activate

# 3. Instalar dependencias
echo -e "\nInstalando dependencias..."
pip install -r requirements.txt

# 4. Ejecutar prueba de auditoría
echo -e "\nEjecutando prueba de auditoría..."
python -m auditor.tests.test_audit_flow

# 5. Verificar resultado
if [ $? -eq 0 ]; then
    echo -e "\n${GREEN}✅ Prueba completada exitosamente${NC}"
else
    echo -e "\n${RED}❌ La prueba falló${NC}"
    exit 1
fi 