import pandas as pd
from datetime import date, datetime

class ZielVerwaltung:
    def __init__(self, pfad="ziele.csv"):
        self.pfad = pfad
        self.df = pd.DataFrame()
        self._lade_oder_erzeuge()

    def _lade_oder_erzeuge(self):
        try:
            self.df = pd.read_csv(self.pfad)
            self.df["Datum"] = pd.to_datetime(self.df["Datum"])
        except:
            self.df = pd.DataFrame(columns=["Datum", "Tagesziel"])
            self.df.to_csv(self.pfad, index=False)

    def ziel_speichern(self, ziel_minuten):
        heute = pd.to_datetime(date.today())
        if not (self.df["Datum"] == heute).any():
            neu = pd.DataFrame([[heute, ziel_minuten]], columns=["Datum", "Tagesziel"])
            self.df = pd.concat([self.df, neu], ignore_index=True)
            self.df.to_csv(self.pfad, index=False)

    def get_df(self):
        return self.df.sort_values("Datum", ascending=False)
