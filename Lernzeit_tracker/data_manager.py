import pandas as pd
from datetime import datetime, timedelta

class LernzeitDaten:
    def __init__(self, pfad="daten.csv"):
        self.pfad = pfad
        self.df = pd.DataFrame()
        self._lade_oder_erzeuge_csv()

    def _lade_oder_erzeuge_csv(self):
        try:
            self.df = pd.read_csv(self.pfad)
            self.df["Datum"] = pd.to_datetime(self.df["Datum"], errors="coerce")
            self.df = self.df.dropna(subset=["Datum"])
            self.df["Notiz"] = self.df.get("Notiz", "").fillna("")
            self.df["Tagesziel"] = self.df.get("Tagesziel", "")
            sechs_monate_zurueck = datetime.today() - timedelta(days=180)
            self.df = self.df[self.df["Datum"] >= sechs_monate_zurueck]
        except Exception:
            self.df = pd.DataFrame(columns=["ID","Fach","Dauer (Minuten)","Datum","Notiz","Tagesziel"])
        self.speichern()

    def speichern(self):
        self.df.to_csv(self.pfad, index=False)

    def neuen_eintrag_hinzufuegen(self, eintrag_df):
        self.df = pd.concat([self.df, eintrag_df], ignore_index=True)
        self.df["Datum"] = pd.to_datetime(self.df["Datum"], errors="coerce")
        self.speichern()
