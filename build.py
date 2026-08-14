#!/usr/bin/env python3
"""Genera el sitio legal de PlanGasto a partir de los Markdown de la app.

La fuente única de verdad son los cuatro documentos de `legal/` en el
repositorio de la aplicación. Este script NO los edita: solo los convierte a
HTML. Si un documento cambia allí, se vuelve a ejecutar esto y se publica.

    python3 build.py [ruta/al/repo/de/la/app]

Sin argumento asume ../gestor_gastos_app_mig
"""

from __future__ import annotations

import html
import re
import shutil
import sys
from pathlib import Path

# md de origen -> (idioma, slug de la URL, título del navegador)
PAGES = {
    "privacidad.md": ("es", "privacidad", "Política de Privacidad — PlanGasto"),
    "terminos.md": ("es", "terminos", "Términos de Uso — PlanGasto"),
    "privacy.md": ("en", "privacy", "Privacy Policy — PlanGasto"),
    "terms.md": ("en", "terms", "Terms of Use — PlanGasto"),
}

# El documento equivalente en el otro idioma, para el conmutador de cabecera.
COUNTERPART = {
    "privacidad.md": ("privacy.md", "English"),
    "terminos.md": ("terms.md", "English"),
    "privacy.md": ("privacidad.md", "Español"),
    "terms.md": ("terminos.md", "Español"),
}

# Nota editorial interna que no debe publicarse: la sustituye el conmutador.
INTERNAL_NOTE = re.compile(r"^>\s*(Versión en inglés|Spanish version)")

CSS = """
:root {
  color-scheme: light dark;
  --bg: #ffffff;
  --fg: #1a1a1a;
  --muted: #5c5c5c;
  --rule: #e3e3e3;
  --accent: #1f6feb;
  --code-bg: #f2f2f2;
  --table-head: #f7f7f7;
}
@media (prefers-color-scheme: dark) {
  :root {
    --bg: #14161a;
    --fg: #e6e6e6;
    --muted: #a0a0a0;
    --rule: #2c2f36;
    --accent: #6ea8ff;
    --code-bg: #22262d;
    --table-head: #1c1f25;
  }
}
* { box-sizing: border-box; }
body {
  margin: 0;
  background: var(--bg);
  color: var(--fg);
  font: 16px/1.65 -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto,
        "Helvetica Neue", Arial, sans-serif;
  -webkit-text-size-adjust: 100%;
}
.wrap { max-width: 46rem; margin: 0 auto; padding: 2rem 1.25rem 5rem; }
header.bar {
  display: flex; flex-wrap: wrap; gap: .75rem;
  align-items: center; justify-content: space-between;
  padding-bottom: 1rem; margin-bottom: 2rem;
  border-bottom: 1px solid var(--rule);
}
header.bar .app { font-weight: 700; letter-spacing: -.01em; }
header.bar a { color: var(--accent); text-decoration: none; font-size: .9rem; }
header.bar a:hover { text-decoration: underline; }
h1 { font-size: 1.75rem; line-height: 1.25; letter-spacing: -.02em; margin: 0 0 1.5rem; }
h2 { font-size: 1.2rem; margin: 2.5rem 0 .75rem; letter-spacing: -.01em; }
h3 { font-size: 1rem; margin: 1.75rem 0 .5rem; }
p, li { overflow-wrap: break-word; }
a { color: var(--accent); }
hr { border: 0; border-top: 1px solid var(--rule); margin: 2rem 0; }
code {
  background: var(--code-bg); padding: .15em .4em;
  border-radius: 4px; font-size: .875em;
  font-family: ui-monospace, SFMono-Regular, Menlo, monospace;
}
blockquote {
  margin: 1.5rem 0; padding: .25rem 0 .25rem 1rem;
  border-left: 3px solid var(--rule); color: var(--muted);
}
.tablewrap { overflow-x: auto; margin: 1.5rem 0; }
table { border-collapse: collapse; width: 100%; font-size: .9rem; }
th, td { border: 1px solid var(--rule); padding: .55rem .7rem; text-align: left; vertical-align: top; }
th { background: var(--table-head); font-weight: 600; }
footer { margin-top: 4rem; padding-top: 1.25rem; border-top: 1px solid var(--rule);
         color: var(--muted); font-size: .85rem; }
ul { padding-left: 1.25rem; }
li { margin: .3rem 0; }
"""


def inline(text: str, links: dict[str, str]) -> str:
    """Formato en línea: escapado, código, negrita y enlaces."""
    out = html.escape(text, quote=False)
    out = re.sub(r"`([^`]+)`", r"<code>\1</code>", out)
    out = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", out)

    def link(match: re.Match[str]) -> str:
        label, target = match.group(1), match.group(2)
        # Los enlaces entre documentos apuntan a .md; se reescriben a las URLs
        # publicadas. Un .md sin reescribir sería un enlace roto en producción.
        href = links.get(target, target)
        return f'<a href="{html.escape(href, quote=True)}">{label}</a>'

    return re.sub(r"\[([^\]]+)\]\(([^)]+)\)", link, out)


def render_paragraph(lines: list[str], links: dict[str, str]) -> str:
    """Un bloque de texto. Los campos `**Etiqueta:** valor` conservan su salto.

    Las líneas se unen ANTES de aplicar el formato en línea: en el original la
    negrita y los enlaces cruzan los saltos del ajuste a 78 columnas, y
    formatear línea a línea dejaría los `**` crudos en el documento publicado.
    """
    is_field_block = all(re.match(r"^\*\*[^*]+:\*\*", ln) for ln in lines)
    body = inline("\n".join(lines), links)
    if is_field_block:
        body = body.replace("\n", "<br>\n")
    return f"<p>{body}</p>"


def render_table(rows: list[str], links: dict[str, str]) -> str:
    def cells(row: str) -> list[str]:
        return [c.strip() for c in row.strip().strip("|").split("|")]

    head = cells(rows[0])
    body = [cells(r) for r in rows[2:]]  # rows[1] es el separador |---|---|
    out = ['<div class="tablewrap"><table>', "<thead><tr>"]
    out += [f"<th>{inline(c, links)}</th>" for c in head]
    out.append("</tr></thead><tbody>")
    for row in body:
        out.append("<tr>" + "".join(f"<td>{inline(c, links)}</td>" for c in row) + "</tr>")
    out.append("</tbody></table></div>")
    return "".join(out)


def to_html(markdown: str, links: dict[str, str]) -> str:
    blocks: list[str] = []
    buffer: list[str] = []
    mode = "p"  # p | ul | table

    def flush() -> None:
        nonlocal buffer, mode
        if not buffer:
            return
        if mode == "ul":
            items = "".join(f"<li>{inline(i, links)}</li>" for i in buffer)
            blocks.append(f"<ul>{items}</ul>")
        elif mode == "table":
            blocks.append(render_table(buffer, links))
        else:
            blocks.append(render_paragraph(buffer, links))
        buffer, mode = [], "p"

    for raw in markdown.splitlines():
        line = raw.rstrip()

        if not line.strip():
            flush()
            continue
        if INTERNAL_NOTE.match(line):  # nota interna: no se publica
            flush()
            continue
        if line.startswith("---"):
            flush()
            blocks.append("<hr>")
            continue

        heading = re.match(r"^(#{1,4})\s+(.*)$", line)
        if heading:
            flush()
            level = len(heading.group(1))
            blocks.append(f"<h{level}>{inline(heading.group(2), links)}</h{level}>")
            continue

        if line.startswith("|"):
            if mode != "table":
                flush()
                mode = "table"
            buffer.append(line)
            continue

        bullet = re.match(r"^[-*]\s+(.*)$", line)
        if bullet:
            if mode != "ul":
                flush()
                mode = "ul"
            buffer.append(bullet.group(1))
            continue

        # Continuación sangrada de un elemento de lista: pertenece al elemento
        # anterior, no a un párrafo nuevo. Sin esto, una negrita que cruce el
        # salto queda partida entre dos bloques.
        if mode == "ul" and buffer and line.startswith(" "):
            buffer[-1] += "\n" + line.strip()
            continue

        quote = re.match(r"^>\s?(.*)$", line)
        if quote:
            flush()
            blocks.append(f"<blockquote>{inline(quote.group(1), links)}</blockquote>")
            continue

        if mode != "p":
            flush()
        buffer.append(line)

    flush()
    return "\n".join(blocks)


def link_map(from_md: str) -> dict[str, str]:
    """Reescribe cada enlace a .md hacia su URL publicada, relativa a esta página."""
    lang = PAGES[from_md][0]
    mapping = {}
    for md, (other_lang, slug, _) in PAGES.items():
        mapping[md] = f"../{slug}/" if other_lang == lang else f"../../{other_lang}/{slug}/"
    return mapping


def page(title: str, lang: str, body: str, switch_href: str, switch_label: str) -> str:
    home = "../../"
    return f"""<!DOCTYPE html>
<html lang="{lang}">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{html.escape(title)}</title>
<style>{CSS}</style>
</head>
<body>
<div class="wrap">
<header class="bar">
  <span class="app"><a href="{home}">PlanGasto</a></span>
  <a href="{switch_href}">{switch_label}</a>
</header>
{body}
<footer>PlanGasto · Kevin Eduardo Olivo Revelo · eduardindev@gmail.com</footer>
</div>
</body>
</html>
"""


INDEX = """<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>PlanGasto — Documentos legales</title>
<style>__CSS__</style>
</head>
<body>
<div class="wrap">
<header class="bar"><span class="app">PlanGasto</span></header>
<h1>Documentos legales</h1>
<h2>Español</h2>
<ul>
  <li><a href="es/privacidad/">Política de Privacidad</a></li>
  <li><a href="es/terminos/">Términos de Uso</a></li>
</ul>
<h2>English</h2>
<ul>
  <li><a href="en/privacy/">Privacy Policy</a></li>
  <li><a href="en/terms/">Terms of Use</a></li>
</ul>
<footer>PlanGasto · Kevin Eduardo Olivo Revelo · eduardindev@gmail.com</footer>
</div>
</body>
</html>
"""


def main() -> int:
    here = Path(__file__).resolve().parent
    app_repo = Path(sys.argv[1]) if len(sys.argv) > 1 else here.parent / "gestor_gastos_app_mig"
    source = (app_repo / "legal").resolve()

    if not source.is_dir():
        print(f"ERROR: no encuentro {source}", file=sys.stderr)
        print("Uso: python3 build.py [ruta/al/repo/de/la/app]", file=sys.stderr)
        return 1

    for lang in ("es", "en"):
        shutil.rmtree(here / lang, ignore_errors=True)

    for md, (lang, slug, title) in PAGES.items():
        src = source / md
        if not src.is_file():
            print(f"ERROR: falta {src}", file=sys.stderr)
            return 1

        body = to_html(src.read_text(encoding="utf-8"), link_map(md))
        other_md, label = COUNTERPART[md]
        other_lang, other_slug, _ = PAGES[other_md]
        switch = f"../../{other_lang}/{other_slug}/"

        out = here / lang / slug / "index.html"
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(page(title, lang, body, switch, label), encoding="utf-8")
        print(f"  {md}  ->  {lang}/{slug}/index.html")

    (here / "index.html").write_text(INDEX.replace("__CSS__", CSS), encoding="utf-8")
    (here / ".nojekyll").write_text("", encoding="utf-8")
    print("  index.html")
    print("\nListo. Fuente:", source)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
