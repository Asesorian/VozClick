# 🎙️ DictaFlow — Dictado por voz para Windows

Habla y el texto aparece donde tengas el cursor. En cualquier app.

DictaFlow nace de [sflow para macOS](https://github.com/daniel-carreon/sflow), la herramienta de dictado por voz creada por Daniel Carreón. Dos miembros de la comunidad [SaaS Factory](https://www.skool.com/saas-factory) la portaron a Windows de forma independiente: [sflow Windows](https://github.com/jtabasco/sflow) por Joel Tabasco y [VozFlow](https://github.com/jorgetorresbiz/vozflow) por Jorge Torres. DictaFlow combina lo mejor de ambas en una sola herramienta: el motor Win32 nativo y el dashboard de Joel con la configuración visual y el selector de micrófono de Jorge.

---

## ✨ Features

| Feature | Origen |
|---------|--------|
| Paste nativo Win32 (más fiable) | sflow |
| Dashboard con historial de transcripciones | sflow |
| Waveform animado con curvas Bezier | sflow Mac |
| Pill flotante con ancho variable y animación | sflow Mac |
| Iconos de estado dibujados (✓ spinner ✕) | sflow Mac |
| **✨ Refiner IA** — reformatea tu dictado como email, informe, prompt... | sflow Mac |
| Arranque rápido (deferred loading) | sflow Mac |
| Selector de micrófono GUI | VozFlow |
| Selector de idioma (es/en/pt/fr/de/it/ca) | VozFlow |
| Diálogo de configuración con pestañas | VozFlow |
| Inicio con Windows | VozFlow |
| Arranque sin micrófono (espera conexión BT) | DictaFlow |
| Hotkey Ctrl+Alt (no genera caracteres) | DictaFlow |
| Eliminar transcripciones individuales o todas | DictaFlow |
| Instalador con acceso directo automático (con icono) | DictaFlow |
| Multi-provider: Groq Llama (gratis), OpenAI, Anthropic | DictaFlow |

---

## 🚀 Instalación

```bash
git clone https://github.com/Asesorian/dictaflow.git
cd dictaflow
install.bat
```

El instalador:
1. Verifica que tengas Python instalado
2. Instala las dependencias automáticamente
3. Genera el icono de la app
4. Te pide la API key de Groq (gratis)
5. Te pregunta si quieres crear un acceso directo en el escritorio (con icono de micrófono) para arrancar DictaFlow sin terminal

---

## 🔑 API Key (gratis)

DictaFlow usa [Groq Whisper](https://console.groq.com) para transcribir (~300 minutos/día gratis):

1. Ve a [console.groq.com/keys](https://console.groq.com/keys)
2. Crea una cuenta gratuita
3. Genera una API key
4. Pégala durante la instalación (o después en Configuración)

---

## 🎮 Uso

| Atajo | Qué hace |
|-------|----------|
| **Ctrl+Alt** (mantener) | Graba mientras mantienes. Suelta → pega el texto. |
| **Shift × 2** (doble tap) | Modo manos libres. Shift de nuevo para parar. |

### ✨ Refiner IA
Después de cada transcripción aparece un botón **✨ Refinar texto**. Al pulsarlo puedes elegir tipo de salida (email, informe, prompt, etc.) y dar contexto. El Refiner reestructura tu dictado desordenado en texto pulido y listo para usar. Vista previa lado a lado para comparar original vs refinado antes de aplicar.

**Providers disponibles:**
- **Groq Llama 3.3 70B** — gratis, misma API key que la transcripción (default)
- **OpenAI GPT-4o** — requiere API key de OpenAI
- **Anthropic Claude Sonnet 4** — requiere API key de Anthropic

Configura el provider en ⚙️ Configuración → pestaña ✨ Refiner IA.

### Dashboard
Historial de transcripciones buscable en: `http://localhost:5678`

### Configuración
Clic derecho en el icono de la bandeja del sistema → ⚙️ Configuración

---

## 📁 Estructura

```
dictaflow/
├── install.bat              ← Ejecutar para instalar
├── launch.vbs               ← Arranca sin ventana (acceso directo)
├── app.py                   ← Punto de entrada (deferred loading)
├── config.py                ← Configuración centralizada
├── audio_recorder.py        ← Captura de micrófono + audio queue
├── transcriber.py           ← Groq Whisper API
├── refiner.py               ← ✨ Refiner IA multi-provider
├── clipboard_paster.py      ← Pegado nativo Win32
├── hotkey_manager.py        ← Detección de teclas (Win32 polling)
├── pill_ui.py               ← Pill flotante con waveform animado
├── refine_widget.py         ← Botón "Refinar" post-transcripción
├── refine_config_widget.py  ← Configurador tipo salida + contexto
├── preview_widget.py        ← Vista previa original vs refinado
├── tray_icon.py             ← Icono en bandeja del sistema
├── settings_dialog.py       ← Configuración (General + Refiner IA)
├── db.py                    ← SQLite (historial + settings)
├── make_icon.py             ← Generador del icono .ico
├── dashboard/
│   ├── server.py            ← Flask dashboard
│   └── templates/
│       └── index.html       ← UI del historial
└── assets/
    └── icon.ico             ← Icono de la app
```

---

## 🛠️ Requisitos

- Windows 10/11
- Python 3.10+
- Conexión a internet (para las APIs)
- Micrófono (integrado o Bluetooth — la app espera si no está conectado)

---

## 🔧 Crear ejecutable (opcional)

```bash
build_exe.bat
```

Genera `dist/DictaFlow.exe` — no necesita Python instalado.

---

## 🙏 Créditos

- **[sflow macOS](https://github.com/daniel-carreon/sflow)** por Daniel Carreón — concepto original, Refiner IA, waveform, pill animado
- **[sflow Windows](https://github.com/jtabasco/sflow)** por Joel Tabasco — Win32 nativo, dashboard, pill UI
- **[VozFlow](https://github.com/jorgetorresbiz/vozflow)** por Jorge Torres — Settings GUI, selector micrófono, inicio con Windows
- **DictaFlow** — Merge + mejoras por Jordi (comunidad [SaaS Factory](https://www.skool.com/saas-factory))

---

## 📄 Licencia

MIT — Úsalo como quieras.
