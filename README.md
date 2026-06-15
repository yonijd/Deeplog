# DEEPLOG - Escáner Jerárquico de Directorios

## Descripción

Herramienta que genera reportes recursivos con **jerarquía visual** de carpetas, mostrando estadísticas por directorio y estructura completa del árbol. Ideal para entender la organización de proyectos complejos.

## Características

- **Jerarquía visual**: Muestra la estructura completa del árbol de directorios
- **Estadísticas por carpeta**: Archivos, tamaño total y extensiones dominantes por cada subcarpeta
- **Detalle interno**: Listado completo de archivos dentro de cada carpeta
- **Sin dependencias**: Solo usa bibliotecas estándar de Python
- **Auto-copia al portapapeles**: Reporte listo para pegar en cualquier chat de IA
- **Guardado automático**: Logs en `%USERPROFILE%\.ialogpack\logs\`

## Instalación

```cmd
python instalador.py
```

## Uso

### Línea de comandos
```cmd
deeplog.py "C:\ruta\carpeta"
```

### Menú contextual (Windows)
1. Click derecho en cualquier carpeta
2. Ir a `IALogPack`
3. Seleccionar `3_deeplog`

## Ejemplo de salida

```
====================================================================================================
   REPORTE PROFUNDO PARA IA - DEEPLOG v1.0.0
====================================================================================================
  Carpeta raiz : C:\Proyectos\mi_app
  Fecha/Hora   : 2026-06-14 04:28:57
  Total global : 40 arch | 7 carpetas | 310.67 KB
  Tipos dom.   : .py(22) .bat(14) .xml(2) .md(1) .rar(1)
  Tiempo scan  : 0.016 seg
====================================================================================================

  [ESTRUCTURA]
  CARPETA/ARCHIVO                                 ARCH      TAMANO  TIPOS DOMINANTES
  --------------------------------------------------------------------------------------------------
  src/                                             12       45.23 KB  .py(8) .json(3) .md(1)
  tests/                                           5        12.10 KB  .py(5)
  README.md                                                 2.15 KB   .md
  --------------------------------------------------------------------------------------------------

====================================================================================================
  [DETALLE POR CARPETA]
====================================================================================================

  --- src ---  (12 arch | 3 subcarpetas | 45.23 KB)
  NOMBRE                               TIPO      TAMANO     MODIFICADO     
  -------------------------------------------------------------------------
  main.py                              .py       8.45 KB    2026-06-14 11:00
  utils.py                             .py       3.21 KB    2026-06-13 15:30
  config.json                          .json     1.02 KB    2026-06-12 09:00
  ...
  -------------------------------------------------------------------------
```

## Formato de salida

### Sección ESTATURA
| Columna | Descripción |
|---------|-------------|
| CARPETA/ARCHIVO | Nombre (sufijo `/` indica carpeta) |
| ARCH | Cantidad de archivos dentro de la carpeta |
| TAMANO | Tamaño total formateado (B/KB/MB/GB) |
| TIPOS DOMINANTES | Extensiones más comunes con su cantidad |

### Sección DETALLE POR CARPETA
| Columna | Descripción |
|---------|-------------|
| NOMBRE | Nombre del archivo |
| TIPO | Extensión del archivo |
| TAMANO | Tamaño formateado (B/KB/MB/GB) |
| MODIFICADO | Fecha y hora de última modificación |

## Limitaciones

- ❌ No analiza contenido de archivos
- ❌ No calcula hashes MD5/SHA256
- ❌ No detecta tipos MIME reales (solo extensión)
- ❌ No permite excluir carpetas (ej: `.git`, `node_modules`)
- ❌ Sin barra de progreso en escaneos grandes
- ❌ Carga todo el árbol en memoria (puede ser pesado en carpetas masivas)

## Dependencias

**Ninguna** - Solo bibliotecas estándar de Python.

## Archivos generados

Los reportes se guardan automáticamente en:
```
%USERPROFILE%\.ialogpack\logs\deeplog_nombre_carpeta_YYYY-MM-DD_HH-MM-SS.log
```

## Desinstalación

Ejecutar `desinstalador.py` desde esta carpeta.

## Licencia

MIT

## Versión

1.0.0

---

*Esta herramienta forma parte del paquete IALogPack.*
