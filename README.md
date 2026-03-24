# 🎙️ DictaFlow — Dictado por voz para Windows

Habla y el texto aparece donde tengas el cursor. En cualquier app.

Combina lo mejor de [sflow](https://github.com/jtabasco/sflow) (Joel Tabasco) y [VozFlow](https://github.com/jorgetorresbiz/vozflow) (Jorge Torres) en una sola herramienta.

---

## ✨ Features

| Feature | Origen |
|---------|--------|
| Paste nativo Win32 (más fiable) | sflow |
| Dashboard con historial de transcripciones | sflow |
| Pill flotante animada con barras de audio | sflow |
| Selector de micrófono GUI | VozFlow |
| Selector de idioma (es/en/pt/fr/de/it/ca) | VozFlow |
| Diálogo de configuración completo | VozFlow |
| Inicio con Windows | VozFlow |
| Arranque sin micrófono (espera conexión BT) | DictaFlow |
| Hotkey Ctrl+Alt (no genera caracteres) | DictaFlow |
| Eliminar transcripciones individuales o todas | DictaFlow |
| Instalador con acceso directo automático | DictaFlow |

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
5. Te pregunta si quieres un acceso directo en el escritorio

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

### Dashboard
Historial de transcripciones buscable en: `http://localhost:5678`

### Configuración
Clic derecho en el icono de la bandeja del sistema → ⚙️ Configuración

---

## 📁 Estructura

```
dictaflow/
├── install.bat          ← Ejecutar para instalar
├── launch.vbs           ← Arranca sin ventana (acceso directo)
├── launch.bat           ← Arranca sin terminal
├── build_exe.bat        ← Crear ejecutable .exe
├── app.py               ← Punto de entrada
├── config.py            ← Configuración centralizada
├── audio_recorder.py    ← Captura de micrófono (sounddevice + Win32)
├── transcriber.py       ← API de Groq Whisper
├── clipboard_paster.py  ← Pegado nativo Win32
├── hotkey_manager.py    ← Detección de teclas (Win32 polling)
├── pill_ui.py           ← Indicador visual flotante (PyQt6)
├── tray_icon.py         ← Icono en bandeja del sistema
├── settings_dialog.py   ← Ventana de configuración
├── db.py                ← SQLite (historial + settings)
├── make_icon.py         ← Generador del icono .ico
├── dashboard/
│   ├── server.py        ← Flask dashboard
│   └── templates/
│       └── index.html   ← UI del historial
└── assets/
    └── icon.ico         ← Icono de la app (se genera en instalación)
```

---

## 🛠️ Requisitos

- Windows 10/11
- Python 3.10+
- Conexión a internet (para la API de Groq)
- Micrófono (integrado o Bluetooth — la app espera si no está conectado)

---

## 🔧 Crear ejecutable (opcional)

```bash
build_exe.bat
```

Genera `dist/DictaFlow.exe` — no necesita Python instalado.

---

## 🙏 Créditos

- **[sflow](https://github.com/jtabasco/sflow)** por Joel Tabasco — Win32 nativo, dashboard, pill UI animada
- **[VozFlow](https://github.com/jorgetorresbiz/vozflow)** por Jorge Torres — Settings GUI, selector micrófono, inicio con Windows
- **DictaFlow** — Merge + mejoras por Jordi (comunidad [SaaS Factory](https://www.skool.com/saas-factory))

Todos inspirados en [sflow para macOS](https://github.com/daniel-carreon/sflow) por Daniel Carreón.

---

## 📄 Licencia

MIT — Úsalo como quieras.
