# backup_manager.py
from pydrive2.auth import GoogleAuth
from pydrive2.drive import GoogleDrive
from oauth2client.service_account import ServiceAccountCredentials
import os
import pandas as pd
import streamlit as st
from datetime import date


class BackupManager:
    def __init__(self, log_file="backup_log.txt"):
        self.creds_file = os.path.join(os.path.dirname(os.path.dirname(__file__)), "service_account.json")
        self.logfile = log_file
        self.folder_name = "Lernzeit_Autobackups"
        self.shared_drive_id = "0AG0GwLBiWQHxUk9PVA"
        self.drive = self._init_drive()
        self.folder_id = self._get_or_create_folder()

    def _init_drive(self):
        gauth = GoogleAuth()
        gauth.credentials = ServiceAccountCredentials.from_json_keyfile_name(
            self.creds_file,
            scopes=["https://www.googleapis.com/auth/drive"]
        )
        return GoogleDrive(gauth)

    def _get_or_create_folder(self):
        try:
            query = (
                f"title='{self.folder_name}' and mimeType='application/vnd.google-apps.folder' "
                "and trashed=false"
            )
            folders = self.drive.ListFile({
                "q": query,
                "supportsAllDrives": True,
                "driveId": self.shared_drive_id,
                "corpora": "drive",
                "includeItemsFromAllDrives": True
            }).GetList()

            if folders:
                return folders[0]["id"]

            folder_metadata = {
                "title": self.folder_name,
                "mimeType": "application/vnd.google-apps.folder",
                "parents": [{"id": self.shared_drive_id}],
            }

            folder = self.drive.CreateFile(folder_metadata)
            folder.Upload()
            return folder["id"]

        except Exception as e:
            st.error(f"⚠️ Fehler beim Abrufen/Erstellen des Ordners: {e}")
            return None

    def upload(self, dateipfad, file_name="Lernzeit_backup.csv"):
        if not self.drive or not self.folder_id:
            st.error("❌ Drive nicht initialisiert oder Ordner-ID fehlt.")
            return None
        try:
            file_drive = self.drive.CreateFile({
                "title": file_name,
                "parents": [{"id": self.folder_id}],
                "mimeType": "text/csv"
            })
            file_drive.SetContentFile(dateipfad)
            file_drive.Upload()
            return file_drive["title"]
        except Exception as e:
            st.error(f"❌ Fehler beim Hochladen des Backups: {e}")
            return None

    def liste_backups(self):
        if not self.drive or not self.folder_id:
            return pd.DataFrame()
        try:
            query = f"'{self.folder_id}' in parents and trashed=false"
            files = self.drive.ListFile({
                "q": query,
                "supportsAllDrives": True,
                "driveId": self.shared_drive_id,
                "corpora": "drive",
                "includeItemsFromAllDrives": True
            }).GetList()

            rows = [{
                "ID": f["id"],
                "Name": f["title"],
                "Datum": f.get("createdDate", "")[:10],
                "Download": f"https://drive.google.com/uc?id={f['id']}&export=download"
            } for f in files]

            return pd.DataFrame(rows)
        except Exception as e:
            st.error(f"❌ Fehler beim Abrufen der Backups: {e}")
            return pd.DataFrame()

    def ist_heute_backup_durchgefuehrt(self):
        if not os.path.exists(self.logfile):
            return False
        with open(self.logfile, "r") as f:
            return f.read().strip() == str(date.today())

    def log_schreiben(self):
        with open(self.logfile, "w") as f:
            f.write(str(date.today()))
