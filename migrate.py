# migrate.py
import sqlite3
from datetime import datetime

def fix_orphaned_sessions():
    db_path = "data/db/assistant_memory.db"
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # 找出所有在 chat_history 表里有，但在 sessions 表里没有的幽灵 session_id
    cursor.execute('''
        SELECT DISTINCT session_id FROM chat_history 
        WHERE session_id NOT IN (SELECT session_id FROM sessions)
    ''')
    orphans = cursor.fetchall()

    if not orphans:
        print("没有需要修复的旧对话。")
        return

    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # 为这些幽灵对话在 sessions 表里补办“身份证”
    for orphan in orphans:
        sid = orphan[0]
        cursor.execute('''
            INSERT INTO sessions (session_id, title, updated_at)
            VALUES (?, ?, ?)
        ''', (sid, "旧版本遗留对话", now))
        
    conn.commit()
    conn.close()
    print(f"✅ 成功找回并修复了 {len(orphans)} 个旧会话！")

if __name__ == "__main__":
    fix_orphaned_sessions()