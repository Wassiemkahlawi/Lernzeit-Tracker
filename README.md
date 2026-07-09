# 📊 Lernzeit-Tracker

Ein personalisierter Lernzeit-Tracker mit CSV-Datenbank, Zielsystem, Heatmap, Cloud-Backup via Google Drive (inkl. Shared Drives), Filter- und Exportfunktionen – ideal für Schüler, Studierende und Selbstlernende.

---

## 🚀 Funktionen

- 📆 Einträge mit Fach, Minuten und Notizen hinzufügen
- 🎯 Tagesziele setzen und auswerten
- 📊 Wöchentliche Statistiken mit Plotly
- 🔥 Heatmap der Lernaktivität
- 🧮 Export & Filterung (z. B. nur Mathe im Juni)
- 🛡️ Automatische Sicherungen (lokal & Drive)
- 🔁 Responsive UI für Desktop & Mobil

---

## 🧱 Projektstruktur

```bash
Lernzeit-Tracker/
├── Lernzeit_tracker/
│   ├── tracker_app.py          # Hauptanwendung
│   ├── data_manager.py         # Datenverwaltung (CSV)
│   ├── ziel_manager.py         # Zielsystem & Fortschritt
│   ├── export_manager.py       # Filter- & Export-Tools
│   └── ...
├── archiv/                     # Alte Versionen (Backup)
├── .streamlit/                 # UI/Theme-Config
├── requirements.txt
├── README.md
└── .gitignore

## Bilder vom Projekt

=> About the Projekt

# Anmerkung

Google Drive Backup (archiviert)

Dieses Backup-System wurde bis März 2026 verwendet.
Es wurde entfernt, da das Projekt nicht mehr Google Workspace
bzw. Google Drive Shared Drives verwendet.

Die Dateien dienen nur als Referenz und werden nicht mehr von
der Anwendung genutzt.

# 📦 Repository klonen
git clone https://github.com/Wassiemkahlawi/Lernzeit-Tracker.git

# 📁 In das Projektverzeichnis wechseln
cd Lernzeit-Tracker

# 🔧 Abhängigkeiten installieren
pip install -r requirements.txt

# 🚀 App starten
streamlit run Lernzeit_tracker/tracker_app.py

# oder
python -m streamlit run Lernzeit_tracker/tracker_app.py
