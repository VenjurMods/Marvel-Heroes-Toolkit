
import sqlite3
import json
import base64
import os
import sys
import tkinter as tk
from tkinter import ttk, filedialog, messagebox

# Logger
def log(message):
    print(message)
    current_tab = notebook.index(notebook.select())
    target_log = convert_log if current_tab == 0 else merge_log
    if target_log:
        target_log.insert(tk.END, message + "\n")
        target_log.see(tk.END)

def decode_base64(base64_string):
    try:
        return base64.b64decode(base64_string)
    except Exception as e:
        log(f"⚠️ Error decoding Base64: {e}")
        return b''

def merge_databases(source_db, target_db, output_db):
    try:
        import shutil
        import pandas as pd

        if not os.path.exists(source_db) or not os.path.exists(target_db):
            log("❌ One or both database files do not exist.")
            return

        shutil.copyfile(target_db, output_db)
        log(f"✔ Base database copied to: {output_db}")

        conn_target = sqlite3.connect(output_db)
        conn_source = sqlite3.connect(source_db)
        cursor_target = conn_target.cursor()
        cursor_source = conn_source.cursor()

        conn_target.execute("PRAGMA foreign_keys = OFF;")
        conn_target.commit()

        tables = cursor_source.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%';"
        ).fetchall()

        for (table_name,) in tables:
            try:
                df = pd.read_sql_query(f"SELECT * FROM {table_name}", conn_source)
                if not df.empty:
                    df.to_sql(table_name, conn_target, if_exists='append', index=False)
                    log(f"✔ Merged {len(df)} records into table: {table_name}")
            except Exception as e:
                log(f"⚠️ Failed to merge table {table_name}: {e}")

        conn_target.execute("PRAGMA foreign_keys = ON;")
        conn_target.commit()
        conn_target.close()
        conn_source.close()
        log("✔ Merge completed successfully.")
    except Exception as e:
        log(f"❌ Merge failed: {e}")

def wipe_database_data_only(db_path):
    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA foreign_keys = ON;")
    cursor = conn.cursor()
    tables = cursor.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%';"
    ).fetchall()
    for (table_name,) in tables:
        cursor.execute(f"DELETE FROM {table_name};")
    conn.commit()
    conn.close()

def import_json_to_db(json_path, db_path):
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        with open(json_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        is_bulk_format = "Account" in data and "Players" in data
        is_single_account_export = "Id" in data and "Player" in data

        if is_bulk_format:
            account_data = data.get("Account")
            player_data_list = data.get("Players", [])
            avatars = data.get("Avatars", [])
            teamups = data.get("TeamUps", [])
            items = data.get("Items", [])
        elif is_single_account_export:
            account_data = {
                "Id": data.get("Id"),
                "Email": data.get("Email", ""),
                "PlayerName": data.get("PlayerName", ""),
                "PasswordHash": decode_base64(data.get("PasswordHash", "")),
                "Salt": decode_base64(data.get("Salt", ""))
            }
            player_data_list = [data.get("Player")]
            avatars = data.get("Avatars", [])
            teamups = data.get("TeamUps", [])
            items = data.get("Items", [])
        else:
            raise ValueError("Unsupported JSON format.")

        if account_data:
            cursor.execute("""
                INSERT INTO Account (Id, Email, PlayerName, PasswordHash, Salt, UserLevel, Flags)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                account_data.get("Id"),
                account_data.get("Email"),
                account_data.get("PlayerName"),
                account_data.get("PasswordHash"),
                account_data.get("Salt"),
                0,
                0
            ))
            log(f"✔ Imported Account ID {account_data.get('Id')}")

        account_id = account_data.get("Id")

        for player in player_data_list:
            if not player:
                continue
            archive_blob = decode_base64(player.get("ArchiveData", ""))
            cursor.execute("""
                INSERT INTO Player (DbGuid, ArchiveData, StartTarget, StartTargetRegionOverride, AOIVolume, GazillioniteBalance)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                player.get("DbGuid"),
                archive_blob,
                player.get("StartTarget", 0),
                player.get("StartTargetRegionOverride", 0),
                player.get("AOIVolume", 0),
                player.get("GazillioniteBalance", 0)
            ))
            log(f"✔ Imported Player ID {player.get('DbGuid')} with ArchiveData length {len(archive_blob)}")

        conn.commit()

        for group, table in [(avatars, "Avatar"), (teamups, "TeamUp"), (items, "Item")]:
            for obj in group:
                if not obj:
                    continue
                archive_blob = decode_base64(obj.get("ArchiveData", ""))
                cursor.execute(f"""
                    INSERT INTO {table} (DbGuid, ContainerDbGuid, InventoryProtoGuid, Slot, EntityProtoGuid, ArchiveData)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    obj.get("DbGuid"),
                    obj.get("ContainerDbGuid", account_id),
                    obj.get("InventoryProtoGuid", 0),
                    obj.get("Slot", 0),
                    obj.get("EntityProtoGuid", 0),
                    archive_blob
                ))
                log(f"✔ Imported {table} ID {obj.get('DbGuid')}")

        conn.commit()
        cursor.execute("PRAGMA foreign_keys = ON;")
        conn.commit()

        for tbl in ["Account", "Player", "Avatar", "TeamUp", "Item"]:
            count = cursor.execute(f"SELECT COUNT(*) FROM {tbl}").fetchone()[0]
            log(f"✔ {tbl}s in DB: {count}")

        log("✔ Import complete!")
        conn.close()
    except Exception as e:
        log(f"❌ Import failed: {e}")

def select_files_and_import():
    json_path = filedialog.askopenfilename(title="Select JSON File", filetypes=(("JSON Files", "*.json"),))
    if not json_path:
        return
    db_path = filedialog.askopenfilename(title="Select Database File", filetypes=(("SQLite Database Files", "*.db"),))
    if not db_path:
        return
    wipe_database_data_only(db_path)
    import_json_to_db(json_path, db_path)

root = tk.Tk()
root.title("Marvel Heroes Toolkit v2.1.2")
root.resizable(True, True)
root.grid_rowconfigure(0, weight=1)
root.grid_columnconfigure(0, weight=1)

notebook = ttk.Notebook(root)
notebook.pack(fill=tk.BOTH, expand=True)


# Convert Tab
convert_tab = ttk.Frame(notebook)
convert_tab.grid_rowconfigure(0, weight=0)
convert_tab.grid_rowconfigure(1, weight=1)
convert_tab.grid_columnconfigure(0, weight=1)

import_button = tk.Button(convert_tab, text="Import JSON to DB", command=select_files_and_import)
import_button.grid(row=0, column=0, pady=10, sticky="n")

convert_log_frame = tk.Frame(convert_tab)
convert_log_frame.grid(row=1, column=0, sticky="nsew")
convert_scrollbar = tk.Scrollbar(convert_log_frame)
convert_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
convert_log = tk.Text(convert_log_frame, height=10, width=100, yscrollcommand=convert_scrollbar.set)
convert_log.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
convert_scrollbar.config(command=convert_log.yview)

notebook.add(convert_tab, text="Convert JSON to DB")


merge_tab = ttk.Frame(notebook)
merge_source_var = tk.StringVar()
merge_target_var = tk.StringVar()
merge_output_var = tk.StringVar()

def select_merge_file(var):
    path = filedialog.askopenfilename(filetypes=[("SQLite DB", "*.db")])
    if path:
        var.set(path)

def run_merge():
    source = merge_source_var.get()
    target = merge_target_var.get()
    output = merge_output_var.get()
    log("⚙️ Starting database merge process...")
    merge_databases(source, target, output)

    try:
        conn = sqlite3.connect(output)
        cursor = conn.cursor()
        for table in ["Account", "Player", "Avatar", "TeamUp", "Item"]:
            cursor.execute(f"SELECT COUNT(*) FROM sqlite_master WHERE type='table' AND name='{table}'")
            if cursor.fetchone()[0]:
                count = cursor.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
                log(f"✔ {table}s in merged DB: {count}")
        conn.close()
        log("✔ Merge verification complete!")
    except Exception as e:
        log(f"❌ Verification failed: {e}")

for label, var in [("Source DB (copy from):", merge_source_var),
                   ("Target DB (base):", merge_target_var),
                   ("Output DB (merged):", merge_output_var)]:
    ttk.Label(merge_tab, text=label).pack(pady=(10, 0))
    ttk.Entry(merge_tab, textvariable=var, width=60).pack()
    ttk.Button(merge_tab, text="Browse", command=lambda v=var: select_merge_file(v)).pack()

ttk.Button(merge_tab, text="Run Merge", command=run_merge).pack(pady=10)
# Merge log display
merge_log_frame = tk.Frame(merge_tab)
merge_log_frame.pack(fill=tk.BOTH, expand=True)
merge_scrollbar = tk.Scrollbar(merge_log_frame)
merge_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
merge_log = tk.Text(merge_log_frame, height=10, width=100, yscrollcommand=merge_scrollbar.set)
merge_log.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
merge_scrollbar.config(command=merge_log.yview)

notebook.add(merge_tab, text="Merge DB Files")



try:
    icon_path = os.path.join(sys._MEIPASS if getattr(sys, 'frozen', False) else os.path.dirname(__file__), 'marvel_toolkit.ico')
    root.iconbitmap(icon_path)
except Exception as e:
    log(f"⚠️ Could not load icon: {e}")

menubar = tk.Menu(root)
helpmenu = tk.Menu(menubar, tearoff=0)
helpmenu.add_command(label="About", command=lambda: messagebox.showinfo(
    "About", "Marvel Heroes Toolkit\nVersion 2.1.2\nCreated by VenjurMods\nhttps://github.com/VenjurMods/Marvel-Heroes-Toolkit"))
menubar.add_cascade(label="Help", menu=helpmenu)
root.config(menu=menubar)

root.mainloop()
