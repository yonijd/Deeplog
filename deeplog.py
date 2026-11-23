import os
import re
import sys
import ctypes
import time
import unicodedata
from pathlib import Path
from datetime import datetime
from collections import Counter

__version__ = "1.1.1"

MAX_KB = 150
MAX_BYTES = MAX_KB * 1024
MARGEN_BYTES = 1024
MAX_LISTA = 100
LIMITE_RUTA = 260
NOISE_DIRS = {".git", "node_modules", "__pycache__"}
SEP = os.sep


def setup_console():
    if os.name != "nt":
        return
    try:
        kernel32 = ctypes.windll.kernel32
        kernel32.SetConsoleOutputCP(65001)
        kernel32.SetConsoleCP(65001)
    except Exception:
        pass


def ext_path(path):
    s = str(path)
    if os.name != "nt" or s.startswith("\\\\?\\"):
        return s
    s = os.path.abspath(s)
    if s.startswith("\\\\"):
        return "\\\\?\\UNC\\" + s[2:]
    return "\\\\?\\" + s


def clean_text(text):
    text = text.encode("utf-8", errors="replace").decode("utf-8")
    return "".join("?" if unicodedata.category(c) == "Cc" else c for c in text)


def norm_key(text):
    base = unicodedata.normalize("NFD", text.lower())
    return "".join(c for c in base if not unicodedata.combining(c))


def path_key(rel):
    if rel == ".":
        return ()
    return tuple(norm_key(p) for p in rel.split(SEP))


def text_bytes(lines):
    return sum(len(line.encode("utf-8")) + 1 for line in lines)


def format_size(bytes_size):
    if bytes_size < 1024:
        return f"{bytes_size} B"
    elif bytes_size < 1024 * 1024:
        return f"{bytes_size / 1024:.2f} KB"
    elif bytes_size < 1024 * 1024 * 1024:
        return f"{bytes_size / (1024 * 1024):.2f} MB"
    else:
        return f"{bytes_size / (1024 * 1024 * 1024):.2f} GB"


def ext_of(name):
    suffix = Path(name).suffix.lower()
    return suffix if suffix else "(sin ext)"


def top_extensions(counter, top):
    return " ".join(f"{e}({n})" for e, n in counter.most_common(top))


def error_reason(e):
    if getattr(e, "winerror", None) in (3, 206):
        return "ruta no encontrada o demasiado larga"
    if isinstance(e, PermissionError):
        return "sin permiso de acceso"
    if isinstance(e, FileNotFoundError):
        return "no encontrado (pudo borrarse durante el escaneo)"
    return clean_text(f"error del sistema: {getattr(e, 'strerror', None) or e}")


def entry_kind(entry):
    if entry.is_symlink():
        return "link"
    try:
        attrs = getattr(entry.stat(follow_symlinks=False), "st_file_attributes", 0)
    except OSError:
        attrs = 0
    if attrs & 0x400:
        return "link"
    if entry.is_dir(follow_symlinks=False):
        return "dir"
    return "file"


def new_node(name, rel, path, mtime):
    return {
        "name": name, "rel": rel, "path": path, "mtime": mtime,
        "files": [], "dirs": [], "links": [], "error": None,
        "omitted": False, "in_omitted": False,
        "expanded": False, "hidden": 0, "limit": None,
        "tot_files": 0, "tot_dirs": 0, "tot_links": 0, "tot_size": 0,
        "exts": Counter(),
    }


def scan_tree(root_path):
    root_display = str(root_path.absolute())
    root_display = root_display.rstrip("\\/") or root_display
    root = new_node(".", ".", ext_path(root_path), None)
    nodes = []
    failures = []
    failed = set()
    long_paths = []
    stack = [root]

    def fail(rel, reason):
        if rel not in failed:
            failed.add(rel)
            failures.append((rel, reason))

    while stack:
        node = stack.pop()
        nodes.append(node)
        try:
            it = os.scandir(node["path"])
        except OSError as e:
            node["error"] = error_reason(e)
            fail(node["rel"], node["error"])
            continue
        with it:
            while True:
                try:
                    entry = next(it)
                except StopIteration:
                    break
                except OSError as e:
                    fail(node["rel"], "lectura interrumpida: " + error_reason(e))
                    break

                name = clean_text(entry.name)
                rel = name if node["rel"] == "." else node["rel"] + SEP + name
                full_len = len(root_display) + 1 + len(rel)
                if full_len > LIMITE_RUTA:
                    long_paths.append((rel, full_len))

                try:
                    kind = entry_kind(entry)
                except OSError as e:
                    kind = "file"
                    fail(rel, error_reason(e))

                size = None
                mtime = None
                try:
                    stat_info = entry.stat(follow_symlinks=False)
                    size = stat_info.st_size
                    mtime = datetime.fromtimestamp(stat_info.st_mtime).strftime("%Y-%m-%d %H:%M")
                except (OSError, ValueError, OverflowError):
                    fail(rel, "no se pudieron leer los atributos")

                if kind == "dir":
                    child = new_node(name, rel, entry.path, mtime)
                    child["omitted"] = name.lower() in NOISE_DIRS and not (node["omitted"] or node["in_omitted"])
                    child["in_omitted"] = node["omitted"] or node["in_omitted"]
                    node["dirs"].append(child)
                    stack.append(child)
                elif kind == "link":
                    node["links"].append({"name": name, "mtime": mtime})
                else:
                    node["files"].append({"name": name, "size": size, "mtime": mtime})

    for node in reversed(nodes):
        node["tot_files"] = len(node["files"])
        node["tot_dirs"] = len(node["dirs"])
        node["tot_links"] = len(node["links"])
        node["tot_size"] = sum(f["size"] or 0 for f in node["files"])
        for f in node["files"]:
            node["exts"][ext_of(f["name"])] += 1
        for child in node["dirs"]:
            node["tot_files"] += child["tot_files"]
            node["tot_dirs"] += child["tot_dirs"]
            node["tot_links"] += child["tot_links"]
            node["tot_size"] += child["tot_size"]
            node["exts"].update(child["exts"])

    return root, nodes, failures, long_paths, root_display


def is_empty(node):
    return node["tot_files"] == 0 and node["tot_dirs"] == 0 and node["tot_links"] == 0


def sorted_entries(node):
    items = []
    for child in node["dirs"]:
        items.append((0, norm_key(child["name"]), "dir", child))
    for link in node["links"]:
        items.append((1, norm_key(link["name"]), "link", link))
    for f in node["files"]:
        items.append((2, norm_key(f["name"]), "file", f))
    items.sort(key=lambda x: (x[0], x[1]))
    return items


def row_text(kind, obj):
    mtime = obj["mtime"] if obj["mtime"] else "?"
    if kind == "file":
        size = "?" if obj["size"] is None else str(obj["size"])
        return f"ARCHIVO | {obj['name']} | {size} | - | {mtime} | -"
    if kind == "link":
        return f"ENLACE | {obj['name']} | - | - | {mtime} | enlace o junction; no se recorre"
    if obj["error"]:
        return f"CARPETA | {obj['name']} | ? | ? | {mtime} | ERROR: {obj['error']}"
    types = top_extensions(obj["exts"], 4)
    suffix = f"; tipos: {types}" if types else ""
    if obj["omitted"]:
        note = "OMITIDA (carpeta de herramientas)" + suffix
    elif obj["expanded"]:
        note = f'ver bloque "{obj["rel"]}"'
    elif is_empty(obj):
        note = "VACIA"
    else:
        note = "NO EXPANDIDA" + suffix
    content = f"arbol: {obj['tot_files']} archivos, {obj['tot_dirs']} carpetas"
    return f"CARPETA | {obj['name']} | {obj['tot_size']} | {content} | {mtime} | {note}"


def block_lines(node, limit=None):
    title = ". (raiz)" if node["rel"] == "." else node["rel"]
    direct = f"directo: {len(node['files'])} archivos, {len(node['dirs'])} carpetas"
    if node["links"]:
        direct += f", {len(node['links'])} enlaces"
    lines = ["", f"=== CARPETA: {title} | {direct} ==="]
    items = sorted_entries(node)
    if not items:
        lines.append("(carpeta vacia)")
        return lines
    used = text_bytes(lines)
    shown = 0
    for _, _, kind, obj in items:
        row = row_text(kind, obj)
        cost = len(row.encode("utf-8")) + 1
        if limit is not None and used + cost > limit:
            break
        lines.append(row)
        used += cost
        shown += 1
    if limit is not None:
        node["hidden"] = len(items) - shown
    if limit is not None and node["hidden"]:
        lines.append(f"(se omitieron {node['hidden']} elementos de esta carpeta por el tope de tamano; estan incluidos en los totales)")
    return lines


def reset_expansion(nodes):
    for node in nodes:
        node["expanded"] = False
        node["hidden"] = 0
        node["limit"] = None


def plan_expansion(root, budget):
    root["expanded"] = True
    root["limit"] = budget
    remaining = budget - text_bytes(block_lines(root, budget))
    expanded = [root]
    level = [root]

    while level and remaining > 0:
        costed = []
        for node in level:
            for child in node["dirs"]:
                if child["omitted"] or child["in_omitted"] or child["error"] or is_empty(child):
                    continue
                costed.append((text_bytes(block_lines(child)), path_key(child["rel"]), child))
        costed.sort(key=lambda x: (x[0], x[1]))
        next_level = []
        for cost, _, child in costed:
            if cost > remaining:
                break
            child["expanded"] = True
            remaining -= cost
            expanded.append(child)
            next_level.append(child)
        level = next_level

    return expanded


def capped_list(title, rows):
    lines = ["", f"=== {title} ({len(rows)}) ==="]
    lines.extend(rows[:MAX_LISTA])
    if len(rows) > MAX_LISTA:
        lines.append(f"(... y {len(rows) - MAX_LISTA} mas)")
    return lines


def build_report(root, root_display, nodes, expanded, failures, long_paths, now):
    unexpanded = 0
    for node in expanded:
        for child in node["dirs"]:
            if not (child["expanded"] or child["omitted"] or child["in_omitted"] or child["error"] or is_empty(child)):
                unexpanded += 1
    omitted = sum(1 for n in nodes if n["omitted"])

    body = []
    used = 0
    for node in sorted(expanded, key=lambda n: path_key(n["rel"])):
        bl = block_lines(node, node["limit"])
        used += text_bytes(bl)
        body.extend(bl)

    complete = bool(expanded) and unexpanded == 0 and not root["hidden"]
    coverage = "completa (todas las carpetas con su detalle)" if complete else "parcial (ver carpetas NO EXPANDIDAS)"

    lines = [
        f"REPORTE PROFUNDO PARA IA - DEEPLOG v{__version__}",
        f"Raiz: {clean_text(root_display)}",
        f"Fecha/Hora: {now.strftime('%Y-%m-%d %H:%M:%S')}",
        'Lectura: rutas relativas a la raiz ("." es la raiz). Cada bloque CARPETA lista SOLO el contenido directo de esa carpeta; lo que esta fuera del bloque no pertenece a ella.',
        "Instruccion para la IA: una CARPETA marcada NO EXPANDIDA existe pero su contenido no esta listado aqui; no supongas sus archivos, pide el detalle de esa carpeta (ejecutar deeplog sobre ella).",
        "Campos: TIPO | NOMBRE | BYTES | CONTENIDO | MODIFICADO | NOTA",
        "Notas: BYTES de una CARPETA es el tamano de todo su arbol; CONTENIDO de una CARPETA cuenta todo su arbol; ? = no se pudo leer; - = no aplica",
        f"Totales (arbol completo): {root['tot_files']} archivos | {root['tot_dirs']} carpetas | "
        f"{root['tot_links']} enlaces | {root['tot_size']} B ({format_size(root['tot_size'])})",
        f"Tipos dominantes: {top_extensions(root['exts'], 6) or '-'}",
        f"Cobertura: {coverage}",
        f"Presupuesto: tope {MAX_KB} KB; bloques {used / 1024:.1f} KB; carpetas sin expandir: {unexpanded}; "
        f"carpetas omitidas por ser de herramientas: {omitted} (sus archivos si cuentan en los totales)",
        f"Fallos de lectura: {len(failures)} | Rutas de mas de {LIMITE_RUTA} caracteres: {len(long_paths)}",
    ]
    if failures:
        lines.append("ATENCION: hubo fallos de lectura; los totales pueden estar incompletos (ver FALLOS al final)")

    lines.extend(body)

    if failures:
        rows = [f"{rel} | {reason}" for rel, reason in sorted(failures, key=lambda x: path_key(x[0]))]
        lines.extend(capped_list("FALLOS", rows))
    if long_paths:
        rows = [f"{rel} | {length} caracteres" for rel, length in sorted(long_paths, key=lambda x: path_key(x[0]))]
        lines.extend(capped_list(f"RUTAS LARGAS (mas de {LIMITE_RUTA} caracteres)", rows))

    lines.append("")
    lines.append(f"=== FIN DEL REPORTE - {root['tot_files']} archivos en {root['tot_dirs']} carpetas - {format_size(root['tot_size'])} ===")
    return "\n".join(lines) + "\n"


def make_report(root, root_display, nodes, failures, long_paths, now):
    reset_expansion(nodes)
    fixed = len(build_report(root, root_display, nodes, [], failures, long_paths, now).encode("utf-8"))
    budget = MAX_BYTES - fixed - MARGEN_BYTES
    report = ""
    for _ in range(8):
        reset_expansion(nodes)
        expanded = plan_expansion(root, max(budget, 0))
        report = build_report(root, root_display, nodes, expanded, failures, long_paths, now)
        size = len(report.encode("utf-8"))
        if size <= MAX_BYTES:
            break
        budget -= (size - MAX_BYTES) + 512
    return report


def write_log(target_path, report, now):
    try:
        folder_name = target_path.name if target_path.name else "raiz"
        folder_clean = "".join([c if c.isalnum() else "_" for c in folder_name])[:40]
        base = os.environ.get("USERPROFILE") or str(Path.home())
        log_dir = Path(base) / ".ialogpack" / "logs"
        log_dir.mkdir(parents=True, exist_ok=True)
        log_filename = f"deeplog_{folder_clean}_{now.strftime('%Y-%m-%d_%H-%M-%S')}.log"
        log_filepath = log_dir / log_filename
        with open(log_filepath, "w", encoding="utf-8", errors="replace") as f:
            f.write(report)
        print("\n[+] Log guardado en:")
        print(f"    {log_filepath}")
    except Exception as e:
        print(f"\nAdvertencia: No se pudo guardar el log: {e}")


def copy_to_clipboard(text):
    try:
        data = text.replace("\r\n", "\n").replace("\n", "\r\n").encode("utf-16le", errors="replace") + b"\x00\x00"
        kernel32 = ctypes.windll.kernel32
        user32 = ctypes.windll.user32
        kernel32.GlobalAlloc.restype = ctypes.c_void_p
        kernel32.GlobalAlloc.argtypes = [ctypes.c_uint, ctypes.c_size_t]
        kernel32.GlobalLock.restype = ctypes.c_void_p
        kernel32.GlobalLock.argtypes = [ctypes.c_void_p]
        kernel32.GlobalUnlock.argtypes = [ctypes.c_void_p]
        kernel32.GlobalFree.argtypes = [ctypes.c_void_p]
        user32.OpenClipboard.argtypes = [ctypes.c_void_p]
        user32.SetClipboardData.argtypes = [ctypes.c_uint, ctypes.c_void_p]
        user32.SetClipboardData.restype = ctypes.c_void_p
        handle = kernel32.GlobalAlloc(0x0002, len(data))
        if not handle:
            return False
        ptr = kernel32.GlobalLock(handle)
        if not ptr:
            kernel32.GlobalFree(handle)
            return False
        ctypes.memmove(ptr, data, len(data))
        kernel32.GlobalUnlock(handle)
        if not user32.OpenClipboard(None):
            kernel32.GlobalFree(handle)
            return False
        try:
            user32.EmptyClipboard()
            if not user32.SetClipboardData(13, handle):
                kernel32.GlobalFree(handle)
                return False
        finally:
            user32.CloseClipboard()
        return True
    except Exception:
        return False


def parse_args(argv):
    raw = " ".join(argv[1:])
    raw = raw.replace('"', "").strip()
    raw = re.sub(r"[\\/]\.$", "", raw)
    if not raw:
        raise ValueError(f"Falta la ruta. Uso: {Path(__file__).name} <ruta>")
    if len(raw) == 2 and raw[1] == ":":
        raw += "\\"
    return Path(raw)


def main():
    setup_console()
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    target_path = parse_args(sys.argv)

    if not os.path.isdir(ext_path(target_path)):
        raise ValueError(f"'{clean_text(str(target_path))}' no es una carpeta valida.")

    print(f"Escaneando: {clean_text(str(target_path.absolute()))}")
    print("Por favor espere...\n")

    start = time.time()
    root, nodes, failures, long_paths, root_display = scan_tree(target_path)
    elapsed = time.time() - start

    if root["error"]:
        raise ValueError(f"No se pudo leer la carpeta: {root['error']}")

    now = datetime.now()
    report = make_report(root, root_display, nodes, failures, long_paths, now)

    print(report)
    print(f"Escaneo completado en {elapsed:.2f} seg | reporte de {len(report.encode('utf-8')) / 1024:.1f} KB")
    write_log(target_path, report, now)

    if copy_to_clipboard(report):
        print("\n[+] Reporte copiado al portapapeles.")
    else:
        print("\n[!] No se pudo copiar al portapapeles.")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"Error: {e}")
    finally:
        input("\nPresione Enter para salir...")