# DEEPLOG - Reporte de estructura de proyectos para IA

## Descripción

Escanea un árbol de carpetas completo y genera un reporte de texto pensado para pegarlo en un chat de IA. El reporte se organiza en **bloques, uno por carpeta**, cada uno con su contenido directo y rutas relativas a la raíz, de modo que la IA sepa siempre qué está dentro de qué. Tiene un tope de tamaño configurable: lo que no cabe se resume y se marca de forma explícita, nunca se oculta en silencio.

## Características

- **Un bloque por carpeta**: cada bloque lista solo el contenido directo de esa carpeta
- **Rutas relativas a la raíz**: el título del bloque indica dónde está cada archivo
- **Nombres completos y bytes exactos**: sin truncar ni redondear
- **Resumen por carpeta**: tamaño del árbol, cantidad de archivos y carpetas, y tipos dominantes
- **Tope de tamaño** (150 KB por defecto): se expande por niveles, de la carpeta más pequeña a la más grande; lo que no cabe queda como `NO EXPANDIDA` con su resumen
- **Carpetas de herramientas omitidas**: `.git`, `node_modules` y `__pycache__` se marcan `OMITIDA`, con su conteo; sus archivos sí cuentan en los totales
- **Nada se omite en silencio**: los fallos de lectura y las rutas de más de 260 caracteres se listan al final
- **Estado de cobertura**: el encabezado indica si el reporte quedó `completa` o `parcial`
- **Rutas largas**: se leen con el prefijo `\\?\`; los enlaces y junctions no se recorren
- **Sin dependencias**: solo usa bibliotecas estándar de Python
- **Auto-copia al portapapeles**: Unicode directo, sin BOM, listo para pegar en cualquier chat de IA
- **Guardado automático**: logs en `%USERPROFILE%\.ialogpack\logs\`

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

También funciona sobre la raíz de una unidad (por ejemplo `D:\`).

## Ejemplo de salida

Ejemplo ilustrativo con un proyecto pequeño:

```
REPORTE PROFUNDO PARA IA - DEEPLOG v1.1.1
Raiz: C:\Proyectos\mi_app
Fecha/Hora: 2026-11-23 18:29:51
Lectura: rutas relativas a la raiz ("." es la raiz). Cada bloque CARPETA lista SOLO el contenido directo de esa carpeta; lo que esta fuera del bloque no pertenece a ella.
Instruccion para la IA: una CARPETA marcada NO EXPANDIDA existe pero su contenido no esta listado aqui; no supongas sus archivos, pide el detalle de esa carpeta (ejecutar deeplog sobre ella).
Campos: TIPO | NOMBRE | BYTES | CONTENIDO | MODIFICADO | NOTA
Notas: BYTES de una CARPETA es el tamano de todo su arbol; CONTENIDO de una CARPETA cuenta todo su arbol; ? = no se pudo leer; - = no aplica
Totales (arbol completo): 13 archivos | 7 carpetas | 0 enlaces | 29570 B (28.88 KB)
Tipos dominantes: .py(5) (sin ext)(4) .md(1) .txt(1) .json(1) .sample(1)
Cobertura: completa (todas las carpetas con su detalle)
Presupuesto: tope 150 KB; bloques 1.2 KB; carpetas sin expandir: 0; carpetas omitidas por ser de herramientas: 1 (sus archivos si cuentan en los totales)
Fallos de lectura: 0 | Rutas de mas de 260 caracteres: 0

=== CARPETA: . (raiz) | directo: 2 archivos, 3 carpetas ===
CARPETA | .git | 9000 | arbol: 5 archivos, 3 carpetas | 2026-11-21 20:42 | OMITIDA (carpeta de herramientas); tipos: (sin ext)(4) .sample(1)
CARPETA | src | 14480 | arbol: 4 archivos, 1 carpetas | 2026-11-20 10:12 | ver bloque "src"
CARPETA | tests | 3900 | arbol: 2 archivos, 0 carpetas | 2026-11-19 09:30 | ver bloque "tests"
ARCHIVO | README.md | 2150 | - | 2026-11-20 10:30 | -
ARCHIVO | requirements.txt | 40 | - | 2026-11-12 09:00 | -

=== CARPETA: src | directo: 3 archivos, 1 carpetas ===
CARPETA | models | 1800 | arbol: 1 archivos, 0 carpetas | 2026-11-20 10:05 | ver bloque "src\models"
ARCHIVO | config.json | 1020 | - | 2026-11-12 09:00 | -
ARCHIVO | main.py | 8450 | - | 2026-11-14 11:00 | -
ARCHIVO | utils.py | 3210 | - | 2026-11-13 15:30 | -

=== CARPETA: src\models | directo: 1 archivos, 0 carpetas ===
ARCHIVO | user.py | 1800 | - | 2026-11-20 10:05 | -

=== CARPETA: tests | directo: 2 archivos, 0 carpetas ===
ARCHIVO | test_main.py | 2400 | - | 2026-11-14 11:20 | -
ARCHIVO | test_utils.py | 1500 | - | 2026-11-13 15:45 | -

=== FIN DEL REPORTE - 13 archivos en 7 carpetas - 28.88 KB ===
```

Como referencia, un proyecto real de unos 500 archivos y 200 carpetas ocupa cerca de 70 KB, es decir, entra completo con más del doble de margen.

## Cómo leer el reporte

### Encabezado

| Línea | Descripción |
|-------|-------------|
| `Raiz` | Ruta completa de la carpeta escaneada |
| `Totales (arbol completo)` | Archivos, carpetas, enlaces y bytes de todo el árbol, incluidas las carpetas omitidas |
| `Tipos dominantes` | Extensiones más comunes de todo el árbol |
| `Cobertura` | `completa` si todas las carpetas tienen su detalle; `parcial` si alguna quedó `NO EXPANDIDA` |
| `Presupuesto` | Tope en KB, KB usados por los bloques, carpetas sin expandir y carpetas omitidas |
| `Fallos de lectura` | Cantidad de elementos que no se pudieron leer |

### Filas

Cada fila tiene seis campos separados por ` | `. El separador `|` no puede aparecer en nombres de archivo de Windows.

| Campo | Descripción |
|-------|-------------|
| TIPO | `ARCHIVO`, `CARPETA` o `ENLACE` |
| NOMBRE | Nombre completo, sin truncar |
| BYTES | Tamaño exacto; en una carpeta, el de todo su árbol |
| CONTENIDO | Solo en carpetas: archivos y carpetas de todo su árbol |
| MODIFICADO | Fecha y hora de última modificación |
| NOTA | Estado de la fila (ver tabla siguiente) |

En cualquier campo, `?` significa que no se pudo leer y `-` que no aplica.

### Notas de una carpeta

| Nota | Significado |
|------|-------------|
| `ver bloque "ruta"` | La carpeta tiene su propio bloque más abajo |
| `NO EXPANDIDA; tipos: ...` | Existe, pero su detalle no cupo en el tope; se resume con su tamaño, conteo y tipos |
| `OMITIDA (carpeta de herramientas)` | Es `.git`, `node_modules` o `__pycache__`; sus archivos cuentan en los totales |
| `VACIA` | La carpeta no contiene nada |
| `ERROR: motivo` | No se pudo leer (por ejemplo, sin permiso de acceso) |

Los enlaces y junctions aparecen como `ENLACE` y no se recorren.

### Secciones finales

Aparecen solo si hay algo que informar:

- `FALLOS`: ruta de cada carpeta o archivo que no se pudo leer y el motivo. Cuando existen, el encabezado avisa de que los totales pueden estar incompletos.
- `RUTAS LARGAS`: elementos cuya ruta completa supera los 260 caracteres, con su longitud.

Cada lista muestra un máximo de 100 líneas y avisa cuántas más hay.

## Cómo funciona el tope

1. Se escanea **todo** el árbol, así que los totales siempre están completos.
2. El tope solo limita cuánto se **muestra**. Primero se muestra la raíz; si queda espacio, el nivel siguiente, y así hasta agotarlo.
3. Dentro de cada nivel se expanden primero las carpetas de menor tamaño de bloque, de modo que la estructura entra antes que las listas largas de archivos.
4. Una carpeta se muestra completa o no se muestra: si no cabe, queda como `NO EXPANDIDA` con su resumen.
5. La raíz siempre se muestra; si por sí sola supera el tope, el reporte indica cuántos elementos se omitieron.

### Ajustes

Las constantes están al inicio de `deeplog.py`:

| Constante | Valor por defecto | Descripción |
|-----------|-------------------|-------------|
| `MAX_KB` | `150` | Tamaño máximo del reporte en KB |
| `NOISE_DIRS` | `.git`, `node_modules`, `__pycache__` | Carpetas que se marcan como `OMITIDA` |
| `LIMITE_RUTA` | `260` | Longitud de ruta a partir de la cual se informa en `RUTAS LARGAS` |
| `MAX_LISTA` | `100` | Líneas máximas de las secciones `FALLOS` y `RUTAS LARGAS` |

## Limitaciones

- ❌ No analiza contenido de archivos
- ❌ No calcula hashes MD5/SHA256
- ❌ No detecta tipos MIME reales (solo extensión)
- ❌ Las carpetas omitidas y el tope se cambian editando el archivo; no hay opciones de línea de comandos
- ❌ Sin barra de progreso en escaneos grandes
- ❌ Carga todo el árbol en memoria (puede ser pesado en carpetas masivas)
- ❌ No recorre enlaces ni junctions

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

1.1.1

### Cambios respecto a 1.0.0

- Un bloque por carpeta con rutas relativas (antes los archivos salían solo con su nombre)
- Nombres completos, sin truncar
- Tope de tamaño de 150 KB; lo que no cabe queda como `NO EXPANDIDA` con su resumen
- Carpetas `.git`, `node_modules` y `__pycache__` marcadas como `OMITIDA`
- Fallos de lectura y rutas largas listados al final, en vez de omitirse
- Corrige el total de carpetas, que solo contaba el primer nivel
- Portapapeles en Unicode sin BOM
- Se elimina el redimensionado de ventana

---

*Esta herramienta forma parte del paquete IALogPack.*

