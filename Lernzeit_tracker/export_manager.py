# export_manager.py
import pandas as pd
from io import BytesIO

class ExportManager:
    @staticmethod
    def dataframe_zu_excel(df: pd.DataFrame):
        buffer = BytesIO()
        with pd.ExcelWriter(buffer, engine="xlsxwriter", datetime_format="dd.mm.yyyy") as writer:
            df.to_excel(writer, index=False, sheet_name="Lernzeit")
            wb  = writer.book
            ws  = writer.sheets["Lernzeit"]

            # Breite automatisch setzen
            for idx, col in enumerate(df.columns):
                max_len = max(
                    [len(str(v)) for v in df[col].astype(str).values] + [len(col)]
                )
                ws.set_column(idx, idx, max_len + 2)

            # Summenzeile (falls Dauer-Spalte vorhanden)
            if "Dauer (Minuten)" in df.columns and not df.empty:
                last_row = len(df) + 1
                col_idx = df.columns.get_loc("Dauer (Minuten)")
                col_letter = chr(ord('A') + col_idx)
                ws.write(last_row, col_idx - 1, "Summe:")
                ws.write_formula(last_row, col_idx, f"=SUM({col_letter}2:{col_letter}{last_row})")

        buffer.seek(0)
        return buffer, "lernzeit_export.xlsx"
