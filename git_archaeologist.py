#!/usr/bin/env python3
"""
🏺 Git Archaeologist
Descubre zombis, hotspots y relaciones ocultas en tu historial de Git.

Uso:
    python git_archaeologist.py                    # Analiza repo actual
    python git_archaeologist.py /ruta/al/repo      # Analiza repo externo
    python git_archaeologist.py --output reporte.html

Autor: Tu Nombre
Repo: https://github.com/tuusuario/git-archaeologist
"""

import argparse
import json
import os
import subprocess
import sys
from collections import Counter, defaultdict
from datetime import datetime, timedelta
from pathlib import Path


class GitArchaeologist:
    """Motor de análisis forense de repositorios Git."""

    def __init__(self, repo_path: str = ".", zombie_days: int = 180, hotspot_days: int = 90):
        self.repo_path = Path(repo_path).resolve()
        self.zombie_threshold = timedelta(days=zombie_days)
        self.hotspot_window = timedelta(days=hotspot_days)
        self.commits = []
        self.file_stats = {}
        self.co_occurrence = Counter()

    def _run_git(self, args: list) -> str:
        """Ejecuta un comando git en el repo objetivo."""
        result = subprocess.run(
            ["git", "-C", str(self.repo_path)] + args,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
        if result.returncode != 0:
            raise RuntimeError(f"Git error: {result.stderr.strip()}")
        return result.stdout

    def validate_repo(self) -> bool:
        """Verifica que la ruta sea un repositorio Git válido."""
        try:
            self._run_git(["rev-parse", "--git-dir"])
            return True
        except RuntimeError:
            return False

    def extract_history(self) -> list:
        """Extrae la historia completa de commits con archivos modificados."""
        fmt = "%H|%ai|%an|%s"
        raw = self._run_git(["log", f"--pretty=format:{fmt}", "--name-only", "--reverse"])

        commits = []
        current = None

        for line in raw.strip().split("\n"):
            line = line.strip()
            if not line:
                continue

            if "|" in line and not line.startswith(" "):
                parts = line.split("|", 3)
                if len(parts) >= 4:
                    current = {
                        "hash": parts[0],
                        "date": datetime.strptime(
                            parts[1].split("+")[0].strip(), "%Y-%m-%d %H:%M:%S"
                        ),
                        "author": parts[2],
                        "message": parts[3],
                        "files": [],
                    }
                    commits.append(current)
            elif current is not None and line:
                current["files"].append(line)

        self.commits = commits
        return commits

    def analyze(self):
        """Calcula todas las métricas: zombis, hotspots, co-ocurrencia, timeline."""
        if not self.commits:
            self.extract_history()

        now = self.commits[-1]["date"] if self.commits else datetime.now()
        zombie_cutoff = now - self.zombie_threshold
        hotspot_cutoff = now - self.hotspot_window

        file_last_touch = {}
        file_commit_count = Counter()
        file_recent_count = Counter()
        file_all_dates = defaultdict(list)
        co_occurrence = Counter()
        monthly_activity = defaultdict(lambda: defaultdict(int))

        for commit in self.commits:
            files = list(set(commit["files"]))
            date = commit["date"]
            month_key = date.strftime("%Y-%m")

            for f in files:
                file_last_touch[f] = max(file_last_touch.get(f, datetime.min), date)
                file_commit_count[f] += 1
                file_all_dates[f].append(date)
                if date >= hotspot_cutoff:
                    file_recent_count[f] += 1
                monthly_activity[month_key][f] += 1

            # Co-ocurrencia (pares no ordenados)
            for i in range(len(files)):
                for j in range(i + 1, len(files)):
                    pair = tuple(sorted([files[i], files[j]]))
                    co_occurrence[pair] += 1

        # Zombis
        zombies = [
            {
                "file": f,
                "last_touch": d.strftime("%Y-%m-%d"),
                "days_dead": (now - d).days,
                "total_commits": file_commit_count[f],
            }
            for f, d in file_last_touch.items()
            if d < zombie_cutoff
        ]
        zombies.sort(key=lambda x: x["days_dead"], reverse=True)

        # Hotspots
        hotspots = [
            {
                "file": f,
                "recent_commits": c,
                "total_commits": file_commit_count[f],
                "last_touch": file_last_touch[f].strftime("%Y-%m-%d"),
            }
            for f, c in file_recent_count.most_common()
            if c > 0
        ]

        # Líneas de código actuales
        file_lines = {}
        for root, dirs, files in os.walk(self.repo_path):
            dirs[:] = [d for d in dirs if d != ".git"]
            for f in files:
                if f.endswith(
                    (".py", ".js", ".ts", ".jsx", ".tsx", ".java", ".go", ".rs", ".c", ".cpp", ".h", ".md", ".txt", ".json", ".yaml", ".yml", ".html", ".css", ".sql")
                ):
                    filepath = Path(root) / f
                    try:
                        with open(filepath, "r", encoding="utf-8", errors="ignore") as file:
                            file_lines[str(filepath.relative_to(self.repo_path))] = len(file.readlines())
                    except Exception:
                        pass

        # Datos del grafo
        all_files = sorted(file_last_touch.keys())
        graph_nodes = [
            {"id": f, "commits": file_commit_count[f], "lines": file_lines.get(f, 0)}
            for f in all_files
            if file_commit_count[f] > 0
        ]
        node_idx = {n["id"]: i for i, n in enumerate(graph_nodes)}
        graph_links = [
            {"source": node_idx[f1], "target": node_idx[f2], "value": v}
            for (f1, f2), v in co_occurrence.most_common(50)
            if f1 in node_idx and f2 in node_idx and v > 1
        ]

        # Timeline
        months = sorted(monthly_activity.keys())
        timeline_data = [
            {"month": m, "file": f, "count": c}
            for m in months
            for f, c in monthly_activity[m].items()
            if c > 0
        ]

        self.file_stats = {
            "commits": self.commits,
            "total_commits": len(self.commits),
            "total_files": len(all_files),
            "zombies": zombies,
            "hotspots": hotspots,
            "co_occurrence": [
                {"file1": f1, "file2": f2, "count": v}
                for (f1, f2), v in co_occurrence.most_common(20)
                if v > 1
            ],
            "graph_nodes": graph_nodes,
            "graph_links": graph_links,
            "timeline": timeline_data,
            "months": months,
            "all_files": all_files,
            "repo_path": str(self.repo_path),
            "generated_at": datetime.now().isoformat(),
        }

        return self.file_stats

    def generate_html(self, template_path: str = None) -> str:
        """Genera el reporte HTML a partir de una plantilla o inline."""
        if not self.file_stats:
            self.analyze()

        stats = self.file_stats

        # Intentar cargar plantilla externa
        if template_path and Path(template_path).exists():
            with open(template_path, "r", encoding="utf-8") as f:
                template = f.read()
            # Reemplazar marcador de datos
            data_json = json.dumps(stats, default=str)
            return template.replace("{{DATA}}", data_json)

        # Plantilla inline por defecto
        return self._default_template(stats)

    def _default_template(self, stats: dict) -> str:
        """Plantilla HTML autocontenida por defecto."""
        data_json = json.dumps(stats, default=str)

        return f"""<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>🏺 Git Archaeologist — {stats["repo_path"]}</title>
    <style>
        :root {{
            --bg: #0d1117; --bg2: #161b22; --bg3: #21262d;
            --text: #c9d1d9; --text2: #8b949e;
            --accent: #58a6ff; --zombie: #f85149; --hotspot: #ffa657; --ok: #3fb950;
            --border: #30363d;
        }}
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ font-family: system-ui, -apple-system, sans-serif; background: var(--bg); color: var(--text); line-height: 1.6; }}
        .container {{ max-width: 1400px; margin: 0 auto; padding: 2rem; }}
        header {{ text-align: center; padding: 3rem 0; border-bottom: 1px solid var(--border); margin-bottom: 2rem; }}
        h1 {{ font-size: 3rem; background: linear-gradient(135deg, var(--accent), #a371f7); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }}
        .subtitle {{ color: var(--text2); }}
        .metrics {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 1rem; margin-bottom: 2rem; }}
        .metric {{ background: var(--bg2); border: 1px solid var(--border); border-radius: 12px; padding: 1.5rem; text-align: center; transition: transform 0.2s; }}
        .metric:hover {{ transform: translateY(-2px); }}
        .metric b {{ display: block; font-size: 2.5rem; margin-bottom: 0.25rem; }}
        .metric-commits {{ color: var(--accent); }} .metric-zombies {{ color: var(--zombie); }}
        .metric-hotspots {{ color: var(--hotspot); }} .metric-files {{ color: var(--ok); }}
        .metric-label {{ color: var(--text2); font-size: 0.8rem; text-transform: uppercase; letter-spacing: 0.05em; }}
        .section {{ background: var(--bg2); border: 1px solid var(--border); border-radius: 12px; margin-bottom: 2rem; overflow: hidden; }}
        .section-header {{ padding: 1.25rem 1.5rem; border-bottom: 1px solid var(--border); display: flex; align-items: center; gap: 0.75rem; }}
        .section-header h2 {{ font-size: 1.2rem; }}
        .section-body {{ padding: 1.5rem; }}
        table {{ width: 100%; border-collapse: collapse; }}
        th, td {{ padding: 0.875rem 1rem; border-bottom: 1px solid var(--border); text-align: left; }}
        th {{ color: var(--text2); font-size: 0.8rem; text-transform: uppercase; letter-spacing: 0.05em; font-weight: 500; }}
        tr:hover td {{ background: var(--bg3); }}
        .filename {{ font-family: SF Mono, Monaco, monospace; font-size: 0.9rem; color: var(--accent); }}
        .bar {{ width: 100%; height: 8px; background: var(--bg3); border-radius: 4px; overflow: hidden; }}
        .bar-fill {{ height: 100%; border-radius: 4px; transition: width 1s ease; }}
        .graph-wrap {{ width: 100%; height: 500px; position: relative; background: var(--bg); border-radius: 8px; }}
        canvas {{ display: block; }}
        .tooltip {{ position: fixed; background: var(--bg3); border: 1px solid var(--border); padding: 0.5rem 0.75rem; border-radius: 6px; font-size: 0.8rem; pointer-events: none; z-index: 1000; display: none; box-shadow: 0 4px 12px rgba(0,0,0,0.3); }}
        .timeline-wrap {{ overflow-x: auto; padding-bottom: 1rem; }}
        .insight {{ background: linear-gradient(135deg, rgba(88,166,255,0.1), rgba(163,113,247,0.1)); border-left: 3px solid var(--accent); padding: 1rem 1.5rem; border-radius: 0 8px 8px 0; margin-bottom: 2rem; font-size: 0.95rem; }}
        .insight strong {{ color: var(--accent); }}
        code {{ background: var(--bg3); padding: 0.15rem 0.4rem; border-radius: 4px; font-family: monospace; font-size: 0.9em; }}
        @media (max-width: 768px) {{ .container {{ padding: 1rem; }} h1 {{ font-size: 2rem; }} .metrics {{ grid-template-columns: repeat(2, 1fr); }} }}
    </style>
</head>
<body>
    <div class="tooltip" id="tooltip"></div>
    <div class="container">
        <header>
            <h1>🏺 Git Archaeologist</h1>
            <p class="subtitle">{stats["repo_path"]} — {stats["total_commits"]} commits analizados</p>
        </header>

        <div class="metrics">
            <div class="metric"><b class="metric-commits">{stats["total_commits"]}</b><span class="metric-label">Commits</span></div>
            <div class="metric"><b class="metric-files">{stats["total_files"]}</b><span class="metric-label">Archivos</span></div>
            <div class="metric"><b class="metric-zombies">{len(stats["zombies"])}</b><span class="metric-label">Zombies 🧟</span></div>
            <div class="metric"><b class="metric-hotspots">{len([h for h in stats["hotspots"] if h["recent_commits"] >= 2])}</b><span class="metric-label">Hotspots 🔥</span></div>
        </div>

        <div class="insight">
            <strong>💡 Insight:</strong> {len(stats["zombies"])} archivos llevan más de {self.zombie_threshold.days} días sin tocarse.
            {f'El par más frecuente es <code>{stats["co_occurrence"][0]["file1"]}</code> ↔ <code>{stats["co_occurrence"][0]["file2"]}</code> ({stats["co_occurrence"][0]["count"]} commits juntos).' if stats["co_occurrence"] else ''}
        </div>

        <div class="section">
            <div class="section-header"><span>🧟</span><h2>Archivos Zombies</h2></div>
            <div class="section-body">
                <table>
                    <thead><tr><th>Archivo</th><th>Último commit</th><th>Días muerto</th><th>Total commits</th><th>Riesgo</th></tr></thead>
                    <tbody>
                        {self._render_zombies(stats["zombies"])}
                    </tbody>
                </table>
            </div>
        </div>

        <div class="section">
            <div class="section-header"><span>🔥</span><h2>Hotspots</h2></div>
            <div class="section-body">
                <table>
                    <thead><tr><th>Archivo</th><th>Commits recientes</th><th>Total</th><th>Último</th><th>Intensidad</th></tr></thead>
                    <tbody>
                        {self._render_hotspots(stats["hotspots"])}
                    </tbody>
                </table>
            </div>
        </div>

        <div class="section">
            <div class="section-header"><span>🔗</span><h2>Grafo de Co-ocurrencia (arrastra los nodos)</h2></div>
            <div class="section-body">
                <div class="graph-wrap" id="graphWrap">
                    <canvas id="graphCanvas"></canvas>
                </div>
            </div>
        </div>

        <div class="section">
            <div class="section-header"><span>📅</span><h2>Timeline de Actividad</h2></div>
            <div class="section-body">
                <div class="timeline-wrap" id="timelineWrap"></div>
            </div>
        </div>
    </div>

    <script>
        const DATA = {data_json};
        {self._render_js()}
    </script>
</body>
</html>"""

    def _render_zombies(self, zombies: list) -> str:
        if not zombies:
            return '<tr><td colspan="5" style="text-align:center;color:var(--text2)">¡No hay zombis! Todo el código está vivo.</td></tr>'
        max_d = max(z["days_dead"] for z in zombies)
        rows = ""
        for z in zombies:
            w = (z["days_dead"] / max_d) * 100
            rows += f"""<tr>
                <td><span class="filename">{z["file"]}</span></td>
                <td>{z["last_touch"]}</td>
                <td>{z["days_dead"]} días</td>
                <td>{z["total_commits"]}</td>
                <td><div class="bar"><div class="bar-fill" style="width:{w}%;background:var(--zombie)"></div></div></td>
            </tr>"""
        return rows

    def _render_hotspots(self, hotspots: list) -> str:
        if not hotspots:
            return '<tr><td colspan="5" style="text-align:center;color:var(--text2)">Sin hotspots recientes.</td></tr>'
        max_r = max(h["recent_commits"] for h in hotspots)
        rows = ""
        for h in hotspots:
            w = (h["recent_commits"] / max_r) * 100
            rows += f"""<tr>
                <td><span class="filename">{h["file"]}</span></td>
                <td>{h["recent_commits"]}</td>
                <td>{h["total_commits"]}</td>
                <td>{h["last_touch"]}</td>
                <td><div class="bar"><div class="bar-fill" style="width:{w}%;background:var(--hotspot)"></div></div></td>
            </tr>"""
        return rows

    def _render_js(self) -> str:
        return """
        // Grafo de fuerzas
        const canvas = document.getElementById('graphCanvas');
        const ctx = canvas.getContext('2d');
        const wrap = document.getElementById('graphWrap');
        const tooltip = document.getElementById('tooltip');

        function resize() {
            canvas.width = wrap.clientWidth;
            canvas.height = wrap.clientHeight;
        }
        resize();
        window.addEventListener('resize', resize);

        const nodes = DATA.graph_nodes.map(n => ({
            ...n,
            x: canvas.width/2 + (Math.random()-0.5)*200,
            y: canvas.height/2 + (Math.random()-0.5)*200,
            vx: 0, vy: 0,
            r: Math.max(12, Math.min(45, 8 + n.commits * 2.5))
        }));
        const links = DATA.graph_links.map(l => ({
            ...l, source: nodes[l.source], target: nodes[l.target]
        }));

        let dragged = null, hover = null;
        canvas.addEventListener('mousedown', e => {
            const r = canvas.getBoundingClientRect();
            const mx = e.clientX - r.left, my = e.clientY - r.top;
            dragged = nodes.find(n => { const dx=mx-n.x, dy=my-n.y; return dx*dx+dy*dy < n.r*n.r; });
        });
        canvas.addEventListener('mousemove', e => {
            const r = canvas.getBoundingClientRect();
            const mx = e.clientX - r.left, my = e.clientY - r.top;
            if (dragged) { dragged.x = mx; dragged.y = my; dragged.vx = dragged.vy = 0; }
            hover = nodes.find(n => { const dx=mx-n.x, dy=my-n.y; return dx*dx+dy*dy < n.r*n.r; });
            if (hover) {
                tooltip.style.display = 'block';
                tooltip.style.left = (e.clientX + 15) + 'px';
                tooltip.style.top = (e.clientY + 15) + 'px';
                tooltip.innerHTML = `<strong>${hover.id}</strong><br>Commits: ${hover.commits}<br>Líneas: ${hover.lines}`;
                canvas.style.cursor = 'pointer';
            } else { tooltip.style.display = 'none'; canvas.style.cursor = 'default'; }
        });
        canvas.addEventListener('mouseup', () => dragged = null);
        canvas.addEventListener('mouseleave', () => { dragged = null; tooltip.style.display = 'none'; });

        function loop() {
            ctx.clearRect(0, 0, canvas.width, canvas.height);
            // Física
            nodes.forEach((a, i) => nodes.forEach((b, j) => {
                if (i >= j) return;
                const dx = b.x - a.x, dy = b.y - a.y, d = Math.sqrt(dx*dx + dy*dy) || 1;
                const f = 5000 / (d * d);
                const fx = (dx/d) * f, fy = (dy/d) * f;
                a.vx -= fx; a.vy -= fy; b.vx += fx; b.vy += fy;
            }));
            links.forEach(l => {
                const dx = l.target.x - l.source.x, dy = l.target.y - l.source.y;
                const d = Math.sqrt(dx*dx + dy*dy) || 1;
                const f = (d - 100) * 0.04;
                const fx = (dx/d) * f, fy = (dy/d) * f;
                l.source.vx += fx; l.source.vy += fy; l.target.vx -= fx; l.target.vy -= fy;
            });
            nodes.forEach(n => {
                if (n === dragged) return;
                n.vx += (canvas.width/2 - n.x) * 0.008;
                n.vy += (canvas.height/2 - n.y) * 0.008;
                n.vx *= 0.88; n.vy *= 0.88;
                n.x += n.vx; n.y += n.vy;
                n.x = Math.max(n.r, Math.min(canvas.width - n.r, n.x));
                n.y = Math.max(n.r, Math.min(canvas.height - n.r, n.y));
            });
            // Dibujo
            links.forEach(l => {
                ctx.beginPath(); ctx.moveTo(l.source.x, l.source.y); ctx.lineTo(l.target.x, l.target.y);
                ctx.strokeStyle = `rgba(139,148,158,${Math.min(0.6, l.value/5)})`;
                ctx.lineWidth = Math.max(1, l.value * 0.8); ctx.stroke();
            });
            nodes.forEach(n => {
                const grad = ctx.createRadialGradient(n.x, n.y, 0, n.x, n.y, n.r + 8);
                grad.addColorStop(0, 'rgba(88,166,255,0.25)'); grad.addColorStop(1, 'rgba(88,166,255,0)');
                ctx.fillStyle = grad; ctx.beginPath(); ctx.arc(n.x, n.y, n.r + 8, 0, Math.PI*2); ctx.fill();
                ctx.beginPath(); ctx.arc(n.x, n.y, n.r, 0, Math.PI*2);
                ctx.fillStyle = n === hover ? '#79c0ff' : '#58a6ff'; ctx.fill();
                ctx.fillStyle = '#fff'; ctx.font = 'bold 10px monospace'; ctx.textAlign = 'center'; ctx.textBaseline = 'middle';
                const label = n.id.length > 14 ? n.id.substring(0, 11) + '...' : n.id;
                ctx.fillText(label, n.x, n.y);
            });
            requestAnimationFrame(loop);
        }
        loop();

        // Timeline SVG
        const tw = document.getElementById('timelineWrap');
        const cell = 16, gap = 2, labelW = 150, headH = 30;
        const months = DATA.months;
        const files = DATA.all_files;
        const maxC = Math.max(...DATA.timeline.map(d => d.count), 1);
        const w = labelW + months.length * (cell + gap) + 20;
        const h = headH + files.length * (cell + gap) + 20;

        let svg = `<svg width="${w}" height="${h}" style="background:#0d1117;border-radius:8px;min-width:${w}px">`;
        months.forEach((m, i) => {
            const x = labelW + i * (cell + gap) + cell/2;
            svg += `<text x="${x}" y="18" fill="#8b949e" font-size="9" text-anchor="middle" transform="rotate(-50,${x},18)">${m}</text>`;
        });
        files.forEach((f, fi) => {
            const y = headH + fi * (cell + gap);
            svg += `<text x="${labelW - 8}" y="${y + cell/2 + 3}" fill="#c9d1d9" font-size="10" text-anchor="end" font-family="monospace">${f}</text>`;
            months.forEach((m, mi) => {
                const d = DATA.timeline.find(t => t.file === f && t.month === m);
                const c = d ? d.count : 0;
                const int = c / maxC;
                const color = int === 0 ? '#21262d' : int < 0.25 ? '#0e4429' : int < 0.5 ? '#006d32' : int < 0.75 ? '#26a641' : '#39d353';
                svg += `<rect x="${labelW + mi * (cell + gap)}" y="${y}" width="${cell}" height="${cell}" fill="${color}" rx="2" data-f="${f}" data-m="${m}" data-c="${c}"/>`;
            });
        });
        svg += '</svg>';
        tw.innerHTML = svg;

        tw.addEventListener('mousemove', e => {
            if (e.target.tagName === 'rect' && e.target.dataset.c) {
                tooltip.style.display = 'block';
                tooltip.style.left = (e.clientX + 15) + 'px';
                tooltip.style.top = (e.clientY + 15) + 'px';
                tooltip.innerHTML = `<strong>${e.target.dataset.f}</strong><br>${e.target.dataset.m}<br>Commits: ${e.target.dataset.c}`;
            }
        });
        tw.addEventListener('mouseleave', () => tooltip.style.display = 'none');
        """


def main():
    parser = argparse.ArgumentParser(
        description="🏺 Git Archaeologist — Análisis forense de repositorios Git",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Ejemplos:
    python git_archaeologist.py                          # Analiza repo actual
    python git_archaeologist.py ../mi-proyecto           # Analiza repo externo
    python git_archaeologist.py --output reporte.html    # Guarda en archivo
    python git_archaeologist.py --zombie-days 90         # Zombis = 90 días
        """,
    )
    parser.add_argument("path", nargs="?", default=".", help="Ruta al repositorio Git (default: .)")
    parser.add_argument("-o", "--output", default="git_report.html", help="Archivo de salida (default: git_report.html)")
    parser.add_argument("--zombie-days", type=int, default=180, help="Días para considerar un archivo zombi (default: 180)")
    parser.add_argument("--hotspot-days", type=int, default=90, help="Días de ventana para hotspots (default: 90)")
    parser.add_argument("--template", help="Ruta a plantilla HTML personalizada")
    parser.add_argument("--open", action="store_true", help="Abre el reporte en el navegador tras generarlo")

    args = parser.parse_args()

    print("🏺 Git Archaeologist")
    print(f"   Repo: {args.path}")
    print(f"   Zombis: +{args.zombie_days} días | Hotspots: últimos {args.hotspot_days} días\n")

    archaeologist = GitArchaeologist(
        repo_path=args.path,
        zombie_days=args.zombie_days,
        hotspot_days=args.hotspot_days,
    )

    if not archaeologist.validate_repo():
        print(f"❌ Error: '{args.path}' no es un repositorio Git válido.")
        sys.exit(1)

    print("📜 Extrayendo historia...")
    archaeologist.extract_history()
    print(f"   {len(archaeologist.commits)} commits encontrados")

    print("🔍 Analizando métricas...")
    stats = archaeologist.analyze()

    print(f"   🧟 Zombis: {len(stats['zombies'])}")
    print(f"   🔥 Hotspots: {len([h for h in stats['hotspots'] if h['recent_commits'] >= 2])}")
    print(f"   🔗 Co-ocurrencias: {len(stats['co_occurrence'])}")

    print(f"\n🎨 Generando reporte...")
    html = archaeologist.generate_html(template_path=args.template)

    output_path = Path(args.output)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html)

    print(f"✅ Reporte guardado: {output_path.resolve()}")

    if args.open:
        import webbrowser
        webbrowser.open(f"file://{output_path.resolve()}")


if __name__ == "__main__":
    main()
