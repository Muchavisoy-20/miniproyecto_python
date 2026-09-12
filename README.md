# Miniproyecto Python - Diplomado Módulo 1

Este repositorio contiene la estructura modular para el miniproyecto en Python, incluyendo pruebas unitarias, análisis de código con Ruff y soporte para contenerización con Docker.

## 📁 Estructura del Proyecto

```text
miniproyecto_python/
├── src/
│   ├── main.py              # Código principal y menú interactivo
│   ├── requirements.txt     # Dependencias del proyecto (pytest, ruff)
│   └── tests.py             # Pruebas unitarias
├── .gitignore               # Configuración de exclusiones de Git
├── Dockerfile               # Configuración de contenedor Docker
└── README.md                # Documentación del proyecto
```

## 🚀 Instalación y Uso

### 1. Crear y activar el entorno virtual

```bash
python -m venv venv
```

- En Windows (PowerShell):
  ```powershell
  .\venv\Scripts\Activate.ps1
  ```
- En Linux / macOS / Git Bash:
  ```bash
  source venv/bin/activate
  ```

### 2. Instalar dependencias

```bash
pip install -r src/requirements.txt
```

### 3. Ejecutar la aplicación

```bash
python src/main.py
```

### 4. Ejecutar pruebas unitarias

```bash
pytest src/tests.py
```

### 5. Análisis de código con Ruff

```bash
ruff check src/
```

## 🐳 Ejecución con Docker

```bash
docker build -t miniproyecto_python .
docker run -it miniproyecto_python
```
