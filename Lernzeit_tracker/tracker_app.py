# tracker_app.py
import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime, date, timedelta
import uuid

from data_manager import LernzeitDaten
from ziel_manager import ZielVerwaltung
from backup_manager import BackupManager
from export_manager import ExportManager

# ------------- App-Setup -------------
st.set_page_config(page_title="Lernzeit-Tracker", page_icon="📚", layout="wide")

PAGES = {
    "📊 Übersicht": "overview",
    "➕ Eintrag hinzufügen": "add",
    "🌞 Tagesziel": "goal",
    "📅 Wochenauswertung": "weekly",
    "🧪 Heatmap": "heatmap",
    "🔎 Filter & Export": "export",
    "☁️ Cloud-Backups": "backups",
    "📆 Zielverlauf": "targets",
    "🗑️ Datenbank löschen": "reset",
    "⚙️ Einstellungen": "settings",
}

# ------------- Session Defaults -------------
if "page" not in st.session_state:
    st.session_state.page = "📊 Übersicht"
if "auto_backup_enabled" not in st.session_state:
    st.session_state.auto_backup_enabled = True
if "eintrag_gespeichert" not in st.session_state:
    st.session_state.eintrag_gespeichert = False

# Globale (optionale) Filter (werden in allen Seiten wiederverwendet, wenn du willst)
if "global_fach" not in st.session_state:
    st.session_state.global_fach = "Alle"
if "global_von" not in st.session_state:
    st.session_state.global_von = None
if "global_bis" not in st.session_state:
    st.session_state.global_bis = None

# ------------- Data Layer -------------
data = LernzeitDaten()
ziel_mgr = ZielVerwaltung()
df = data.df.copy()

# Eine Hilfsfunktion: sichere Datums-Spalte
def ensure_datetime(df, col="Datum"):
    if col in df.columns:
        df[col] = pd.to_datetime(df[col], errors="coerce")
        df.dropna(subset=[col], inplace=True)
    return df

df = ensure_datetime(df)

# ------------- Kleine UI-Helfer -------------
def kpi(label, value, help_text=None, delta=None):
    st.metric(label, value, delta=delta, help=help_text)

def empty_state(text, button_label=None, on_click=None):
    st.info(text)
    if button_label:
        if st.button(button_label):
            if on_click:
                on_click()

def global_filter_ui(df):
    with st.sidebar.expander("🔎 Globaler Filter", expanded=False):
        faecher = ["Alle"] + sorted(df["Fach"].dropna().unique().tolist()) if not df.empty else ["Alle"]
        st.session_state.global_fach = st.selectbox("Fach", faecher, index=0)
        if not df.empty:
            min_d = df["Datum"].min().date()
            max_d = df["Datum"].max().date()
        else:
            min_d = max_d = date.today()
        st.session_state.global_von = st.date_input("Von", min_d)
        st.session_state.global_bis = st.date_input("Bis", max_d)

def apply_global_filter(df):
    if df.empty:
        return df
    mask = (df["Datum"].dt.date >= st.session_state.global_von) & (df["Datum"].dt.date <= st.session_state.global_bis)
    if st.session_state.global_fach != "Alle":
        mask &= (df["Fach"] == st.session_state.global_fach)
    return df[mask]

# ------------- Seiten -------------
def page_overview():
    st.subheader("📊 Übersicht")

    if df.empty:
        return empty_state("Noch keine Einträge vorhanden.", "➕ Jetzt ersten Eintrag anlegen", lambda: set_page("➕ Eintrag hinzufügen"))

    # KPIs
    today = date.today()
    week_start = today - timedelta(days=today.weekday())
    this_week = df[df["Datum"].dt.date >= week_start]
    today_minutes = df[df["Datum"].dt.date == today]["Dauer (Minuten)"].sum()
    week_minutes = this_week["Dauer (Minuten)"].sum()
    total_minutes = df["Dauer (Minuten)"].sum()

    c1, c2, c3 = st.columns(3)
    with c1: kpi("Heute", f"{int(today_minutes)} Min")
    with c2: kpi("Diese Woche", f"{int(week_minutes)} Min")
    with c3: kpi("Gesamt", f"{int(total_minutes)} Min")

    # Diagramme
    tabs = st.tabs(["Nach Fach", "Über Zeit"])
    with tabs[0]:
        by_subject = df.groupby("Fach")["Dauer (Minuten)"].sum().sort_values(ascending=False)
        if by_subject.empty:
            st.info("Keine Daten für Fächer vorhanden.")
        else:
            st.bar_chart(by_subject)

    with tabs[1]:
        per_day = df.groupby(df["Datum"].dt.date)["Dauer (Minuten)"].sum()
        if per_day.empty:
            st.info("Keine zeitliche Verteilung vorhanden.")
        else:
            st.line_chart(per_day)

def page_add():
    st.subheader("➕ Eintrag hinzufügen")

    if st.session_state.eintrag_gespeichert:
        st.success("✅ Eintrag wurde gespeichert")
        st.session_state.eintrag_gespeichert = False

    last_subject = df["Fach"].iloc[-1] if not df.empty else ""
    fach = st.text_input("📘 Fach", value=last_subject)
    col1, col2 = st.columns([1,1])
    with col1:
        dauer = st.number_input("⏱️ Minuten", min_value=1, step=1, value=25)
    with col2:
        datum = st.date_input("📅 Datum", value=date.today())
    notiz = st.text_area("📝 Notiz (optional)")

    # Quick Buttons
    qb = st.radio("Schnellwahl", [15,25,50,90, "Custom"], horizontal=True, index=1)
    if qb != "Custom":
        dauer = int(qb)

    if st.button("💾 Speichern"):
        if not fach.strip():
            st.warning("Bitte gib ein Fach ein.")
            return
        new_row = pd.DataFrame(
            [[str(uuid.uuid4()), fach.strip(), dauer, datum, notiz, "90"]],
            columns=["ID","Fach","Dauer (Minuten)","Datum","Notiz","Tagesziel"]
        )
        data.neuen_eintrag_hinzufuegen(new_row)
        st.session_state.eintrag_gespeichert = True
        st.rerun()

def page_goal():
    st.subheader("🌞 Tagesziel")

    if df.empty:
        return empty_state("Du hast noch keine Einträge. Lege zuerst einen an.", "➕ Eintrag hinzufügen", lambda: set_page("➕ Eintrag hinzufügen"))

    ziel_minuten = st.number_input("🎯 Tagesziel (Minuten)", min_value=10, step=10, value=90)
    heute = date.today()
    gesamt = df[df["Datum"].dt.date == heute]["Dauer (Minuten)"].sum()
    fortschritt = 0 if ziel_minuten == 0 else min(1, gesamt / ziel_minuten)
    st.progress(int(fortschritt * 100), text=f"{int(gesamt)} / {ziel_minuten} Minuten")

    # Hinweis
    if fortschritt >= 1:
        st.success("✅ Ziel erreicht – stark!")
    elif fortschritt >= 0.5:
        st.info("ℹ️ Halbzeit! Du bist gut dabei.")
    else:
        st.warning(f"💪 Noch {ziel_minuten - int(gesamt)} Minuten bis zum Ziel.")

    ziel_mgr.ziel_speichern(ziel_minuten)

def page_heatmap():
    st.subheader("🧪 Heatmap")

    if df.empty:
        return empty_state("Keine Daten für Heatmap vorhanden.", "➕ Eintrag hinzufügen", lambda: set_page("➕ Eintrag hinzufügen"))

    dff = apply_global_filter(df)  # optional – kannst du auch weglassen
    if dff.empty:
        return empty_state("Im gewählten Zeitraum gibt es keine Daten.")

    tmp = dff.copy()
    tmp["Datum"] = pd.to_datetime(tmp["Datum"])
    tmp["tag"] = tmp["Datum"].dt.date
    heat = tmp.groupby("tag")["Dauer (Minuten)"].sum().reset_index()
    heat["Wochentag"] = pd.to_datetime(heat["tag"]).dt.day_name()
    heat["Kalenderwoche"] = pd.to_datetime(heat["tag"]).dt.isocalendar().week
    heat["Wochentag"] = pd.Categorical(
        heat["Wochentag"],
        categories=["Monday","Tuesday","Wednesday","Thursday","Friday","Saturday","Sunday"],
        ordered=True
    )

    fig = px.density_heatmap(
        data_frame=heat,
        x="Kalenderwoche", y="Wochentag", z="Dauer (Minuten)",
        color_continuous_scale="Viridis",
        labels={"Dauer (Minuten)": "Minuten"},
        title="Lernzeit pro Tag"
    )
    st.plotly_chart(fig, use_container_width=True)

def page_export():
    st.subheader("🔎 Filter & Export")
    if df.empty:
        return empty_state("Noch keine Daten zum Exportieren.")
    dff = apply_global_filter(df)
    st.dataframe(dff, use_container_width=True)
    if dff.empty:
        return st.info("Keine Daten im gewählten Bereich.")
    buffer, name = ExportManager.dataframe_zu_excel(dff)  # später ersetzen durch Auto-Format-Version
    st.download_button("⬇️ Export als Excel", data=buffer, file_name=name,
                       mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

def page_backups():
    st.subheader("☁️ Cloud-Backups")
    backup = BackupManager()

    if not backup.folder_id:
        st.error("❌ Kein Zugriff auf Drive-Ordner. Bitte Zugang oder Ordner-ID prüfen.")
        return

    # Status
    st.caption(f"Drive-Ordner-ID: `{backup.folder_id}`")
    if st.session_state.auto_backup_enabled and not backup.ist_heute_backup_durchgefuehrt():
        uploaded = backup.upload(data.pfad, file_name=f"AutoBackup_{datetime.now().strftime('%Y-%m-%d')}.csv")
        if uploaded:
            backup.log_schreiben()
            st.success("🔄 Auto-Backup erfolgreich durchgeführt.")
        else:
            st.warning("⚠️ Auto-Backup fehlgeschlagen.")

    if st.button("📤 Manuelles Backup jetzt hochladen"):
        ts = datetime.now().strftime("%Y-%m-%d-%H-%M")
        uploaded = backup.upload(data.pfad, file_name=f"Lernzeit_backup_{ts}.csv")
        if uploaded:
            st.success(f"✅ Hochgeladen als: {uploaded}")
        else:
            st.warning("❌ Fehler beim Hochladen.")

    st.divider()
    st.subheader("📄 Deine letzten Backups")
    df_backups = backup.liste_backups()
    if df_backups.empty:
        st.info("Noch keine Backups im Drive-Ordner gefunden.")
    else:
        for _, row in df_backups.iterrows():
            col1, col2 = st.columns([3,1])
            col1.write(f"📁 **{row['Name']}** – 📅 {row['Datum']}")
            col2.markdown(f"[⬇️ Download]({row['Download']})", unsafe_allow_html=True)

def page_weekly():
    st.subheader("📅 Wochenauswertung")
    if df.empty:
        return empty_state("Keine Daten vorhanden.")
    tmp = df.copy()
    tmp["Datum"] = pd.to_datetime(tmp["Datum"])
    tmp["KW"] = tmp["Datum"].dt.isocalendar().week
    tmp["Jahr"] = tmp["Datum"].dt.year
    g = tmp.groupby(["Jahr", "KW"])["Dauer (Minuten)"].sum().reset_index()
    g["Label"] = g["Jahr"].astype(str) + "-KW" + g["KW"].astype(str)
    st.bar_chart(g.set_index("Label")["Dauer (Minuten)"])

def page_targets():
    st.subheader("📆 Zielverlauf")
    df_z = ziel_mgr.get_df()
    if df_z.empty:
        st.info("Noch keine Tagesziele gespeichert.")
    else:
        st.dataframe(df_z, use_container_width=True)

def page_settings():
    st.subheader("⚙️ Einstellungen")
    st.session_state.auto_backup_enabled = st.checkbox("🔄 Auto-Backup aktivieren", value=st.session_state.auto_backup_enabled)

def page_reset():
    st.subheader("🗑️ Datenbank löschen")
    st.warning("⚠️ Diese Aktion löscht alle Daten unwiderruflich.")
    if st.checkbox("Ich bin sicher"):
        if st.button("🔥 Jetzt löschen"):
            data.df = pd.DataFrame(columns=["ID","Fach","Dauer (Minuten)","Datum","Notiz","Tagesziel"])
            data.speichern()
            ziel_mgr.df = pd.DataFrame(columns=["Datum","Tagesziel"])
            ziel_mgr.df.to_csv(ziel_mgr.pfad, index=False)
            st.success("✅ Alle Daten wurden gelöscht.")
            st.rerun()

# Helper to change page from callbacks
def set_page(name):
    st.session_state.page = name
    st.rerun()

# ------------- Sidebar Navigation -------------
with st.sidebar:
    st.markdown("## 📚 Lernzeit-Tracker")
    choice = st.radio("Seite wählen:", list(PAGES.keys()), index=list(PAGES.keys()).index(st.session_state.page))
    if choice != st.session_state.page:
        set_page(choice)
    # Optional: globaler Filter
    global_filter_ui(df)

# ------------- Router -------------
page_map = {
    "📊 Übersicht": page_overview,
    "➕ Eintrag hinzufügen": page_add,
    "🌞 Tagesziel": page_goal,
    "📅 Wochenauswertung": page_weekly,
    "🧪 Heatmap": page_heatmap,
    "🔎 Filter & Export": page_export,
    "☁️ Cloud-Backups": page_backups,
    "📆 Zielverlauf": page_targets,
    "🗑️ Datenbank löschen": page_reset,
    "⚙️ Einstellungen": page_settings,
}
page_map[st.session_state.page]()
