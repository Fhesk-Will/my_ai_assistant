from datetime import datetime
from core.memory import MemoryManager


def fix_orphaned_sessions():
    memory = MemoryManager()
    orphans = memory.get_orphaned_sessions()

    if not orphans:
        print("没有需要修复的旧对话。")
        return

    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    for sid in orphans:
        memory.update_session_meta(sid, title="旧版本遗留对话")

    print(f"成功找回并修复了 {len(orphans)} 个旧会话！")


if __name__ == "__main__":
    fix_orphaned_sessions()
