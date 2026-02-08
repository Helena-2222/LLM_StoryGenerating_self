# outputs/FinalOutput/FinalOutput.py
import os
from datetime import datetime

# 全局变量，记录本次运行的唯一存储目录
_SESSION_FOLDER = None

def get_session_folder():
    """获取或创建本次运行的专属文件夹"""
    global _SESSION_FOLDER
    if _SESSION_FOLDER is None:
        base_dir = "outputs/FinalOutput/Scripts"
        # 生成时间戳格式：0520_143005 (月日_时分秒)
        timestamp = datetime.now().strftime("m%d_%H%M%S")
        _SESSION_FOLDER = os.path.join(base_dir, timestamp)
        
    if not os.path.exists(_SESSION_FOLDER):
        os.makedirs(_SESSION_FOLDER)
    return _SESSION_FOLDER

def save_final_script(episode_num, content, title="未命名短剧"):
    # 获取本次运行的时间戳文件夹
    directory = get_session_folder()
    
    file_path = os.path.join(directory, f"EP_{episode_num:02d}.md")
    
    formatted_content = f"# {title} - 第 {episode_num} 集\n\n{content}"
    
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(formatted_content)
    
    print(f"✅ 最终剧本已存至：{file_path}")