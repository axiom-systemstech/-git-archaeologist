<div align="center">

# 🏺 Git Archaeologist

**Descubre zombis, hotspots y relaciones ocultas en tu historial de Git.**

Un forense para tu código. Sin dependencias externas. Un solo archivo HTML de salida.

[![Python](https://img.shields.io/badge/python-3.8%2B-blue)](https://python.org)
[![License](https://img.shields.io/badge/license-MIT-green)](LICENSE)
[![GitHub stars](https://img.shields.io/github/stars/axiom-systemstech/git-archaeologist?style=social)](https://github.com/axiom-systemstech/git-archaeologist)

</div>

---

## ✨ ¿Qué hace?

Git Archaeologist analiza la historia completa de tu repositorio Git y genera un **reporte HTML interactivo** que revela:

| Característica | Descripción |
|---|---|
| 🧟 **Zombies** | Archivos que no se tocan en +180 días. Código muerto que ocupa espacio mental. |
| 🔥 **Hotspots** | Archivos con actividad frenética reciente. Posible deuda técnica o falta de abstracción. |
| 🔗 **Grafo de co-ocurrencia** | ¿Qué archivos siempre se commitan juntos? Arrastra los nodos. Si dos módulos siempre rompen juntos, deberían estar más cerca. |
| 📅 **Timeline de actividad** | Heatmap tipo GitHub pero por archivo y mes. Visualiza la evolución del proyecto. |

> **Sin dependencias.** Solo Python estándar + Git. El HTML de salida es 100% autocontenido: sin CDN, sin internet, sin trackers.

---

## 🚀 Instalación

```bash
# Clona el repo
git clone https://github.com/tuusuario/git-archaeologist.git
cd git-archaeologist

# No necesitas instalar nada. Python 3.8+ y Git.
python git_archaeologist.py --help
```

---

## 📖 Uso

### Analiza el repo actual
```bash
python git_archaeologist.py
```
Abre `git_report.html` en tu navegador.

### Analiza otro repo
```bash
python git_archaeologist.py /ruta/a/tu/proyecto
```

### Personaliza umbrales
```bash
# Zombis = 90 días sin tocar, hotspots = últimos 30 días
python git_archaeologist.py --zombie-days 90 --hotspot-days 30
```

### Salida personalizada + abrir navegador
```bash
python git_archaeologist.py --output mi_analisis.html --open
```

### Usa tu propia plantilla HTML
```bash
python git_archaeologist.py --template templates/mi_estilo.html
```

---

## 🖼️ Vista previa

### Dashboard de métricas
Muestra commits totales, archivos, zombis y hotspots de un vistazo.

### Archivos Zombies
Tabla ordenada por días sin actividad. Barra de riesgo visual. Ideal para identificar código muerto que se puede eliminar o documentar.

### Hotspots
Archivos más modificados en la ventana reciente. Si un archivo aparece aquí constantemente, es candidato a refactorización o tests más exhaustivos.

### Grafo interactivo de co-ocurrencia
- **Nodos** = archivos (tamaño proporcional a commits)
- **Líneas** = frecuencia de edición conjunta
- **Arrastrable** = pincha y mueve nodos
- **Tooltip** = hover para ver commits y líneas de código

> Si `api.py` y `auth.py` siempre se editan juntos, quizá deberían fusionarse o vivir en el mismo módulo.

### Timeline de actividad
Heatmap estilo GitHub contributions pero por archivo. Verde intenso = mucha actividad. Gris = inactividad. Desplazable horizontalmente.

---

## 🧪 Ejemplo de salida

```
🏺 Git Archaeologist
   Repo: /home/dev/mi-proyecto
   Zombis: +180 días | Hotspots: últimos 90 días

📜 Extrayendo historia...
   847 commits encontrados

🔍 Analizando métricas...
   🧟 Zombis: 12
   🔥 Hotspots: 8
   🔗 Co-ocurrencias: 24

🎨 Generando reporte...
✅ Reporte guardado: /home/dev/mi-proyecto/git_report.html
```

---

## 🏗️ Arquitectura

```
git_archaeologist.py
├── GitArchaeologist
│   ├── validate_repo()          # Verifica que es un repo Git
│   ├── extract_history()        # Parsea git log --name-only
│   ├── analyze()                # Calcula métricas
│   ├── generate_html()          # Renderiza plantilla
│   └── _default_template()      # HTML inline autocontenido
└── main()                       # CLI con argparse
```

**Cero dependencias externas.** Todo el análisis se hace con:
- `subprocess` para ejecutar Git
- `collections.Counter` para estadísticas
- `datetime` para ventanas temporales
- `json` para serializar datos al frontend
- Canvas API + requestAnimationFrame para el grafo físico

---

## 🛣️ Roadmap

- [ ] Detección de "autor propietario" por archivo
- [ ] Comparativa entre ramas (`main` vs `develop`)
- [ ] Detección de código duplicado entre zombis
- [ ] Exportar a Markdown para README
- [ ] Modo CI: falla si hay más de N zombis nuevos
- [ ] Filtro por extensión de archivo
- [ ] Soporte para monorepos con múltiples paquetes

---

## 🤝 Contribuir

```bash
# Fork, clone y crea una rama
git checkout -b feat/mi-mejora

# Asegúrate de que funciona en tu repo
python git_archaeologist.py --open

# Commit y PR
git commit -m "feat: añade detección de autores propietarios"
```

---

## 📄 Licencia

MIT. Haz lo que quieras. Si te sirve, dale una ⭐ en GitHub y cuéntalo en LinkedIn/X.

---

<div align="center">

Hecho con 💀 y 🔥 por <a href="https://github.com/axiom-systemstech">@tuusuario</a>

</div>
