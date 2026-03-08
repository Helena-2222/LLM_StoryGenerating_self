import os
import io
import pandas as pd
from datetime import datetime
from openpyxl import load_workbook
from openpyxl.styles import Alignment

# 全局变量，缓存当前运行的目录，避免每一集都创建新时间戳文件夹
_CURRENT_SESSION_PATH = None

def save_final_script(episode_num, script_content, title, story_id="Default", max_width=80, wrap_length=10):
    """
    新增参数: story_id
    """
    global _CURRENT_SESSION_PATH

    # 1. 动态构建目录结构
    if _CURRENT_SESSION_PATH is None:
        # 只有在第一次运行该函数时生成时间戳文件夹
        base_dir = os.path.join("outputs", "FinalOutput", "Scripts", story_id)
        timestamp = datetime.now().strftime("%m%d_%H%M%S")
        _CURRENT_SESSION_PATH = os.path.join(base_dir, timestamp)
        os.makedirs(_CURRENT_SESSION_PATH, exist_ok=True)

    # 2. 保存原始文本备份
    txt_filename = f"{title}_EP{episode_num}.txt"
    txt_path = os.path.join(_CURRENT_SESSION_PATH, txt_filename)
    with open(txt_path, "w", encoding="utf-8") as f:
        f.write(script_content)

    # 3. 解析并导出 Excel (逻辑保持不变)
    try:
        table_lines = [line.strip() for line in script_content.split('\n') if '|' in line]
        if len(table_lines) < 3:
            print(f"⚠️ 第 {episode_num} 集未检测到表格，已保存 TXT。")
            return

        table_data = "\n".join(table_lines)
        df = pd.read_csv(io.StringIO(table_data), sep="|", skipinitialspace=True).dropna(axis=1, how='all')
        df = df[~df.iloc[:, 0].astype(str).str.contains('---')]
        df.columns = [c.strip() for c in df.columns]
        df = df.map(lambda x: x.strip() if isinstance(x, str) else x)

        excel_filename = f"{title}_EP{episode_num}_分镜表.xlsx"
        excel_path = os.path.join(_CURRENT_SESSION_PATH, excel_filename)
        df.to_excel(excel_path, index=False, engine='openpyxl')
        
        print(f"📊 分镜表已存至: {excel_path}")

    except Exception as e:
        print(f"❌ Excel 解析失败: {e}")