import sqlite3
import json
import base64
import os

os.makedirs('downloads', exist_ok=True)
conn = sqlite3.connect('backend/data/c2.db')
cursor = conn.cursor()

# Query task results that look like our file download json structure
cursor.execute('SELECT id, output FROM task_results WHERE output LIKE "%filename%" AND output LIKE "%content%";')
rows = cursor.fetchall()

for idx, (task_id, output_val) in enumerate(rows):
    try:
        data = json.loads(output_val)
        if "filename" in data and "content" in data:
            filename = data["filename"]
            file_data = base64.b64decode(data["content"])
            
            dest_path = os.path.join('downloads', f'{filename}_{task_id[:8]}')
            with open(dest_path, 'wb') as f:
                f.write(file_data)
            print(f'[+] Downloaded and saved: {dest_path}')
    except Exception as e:
        print(f'[-] Failed to parse task {task_id}: {e}')

conn.close()
