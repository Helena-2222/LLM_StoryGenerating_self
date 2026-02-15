# outputs/FinalOutput/FinalOutput.py
import os
import io
import pandas as pd
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

'''
def save_final_script(episode_num, content, title="未命名短剧"):
    # 获取本次运行的时间戳文件夹
    directory = get_session_folder()
    
    file_path = os.path.join(directory, f"EP_{episode_num:02d}.md")
    
    formatted_content = f"# {title} - 第 {episode_num} 集\n\n{content}"
    
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(formatted_content)
    
    print(f"✅ 最终剧本已存至：{file_path}")
'''

from openpyxl import load_workbook
from openpyxl.styles import Alignment

def save_final_script(episode_num, script_content, title, max_width=80, wrap_length=10):
    """
    将剧本内容保存为 Excel 分镜表和 纯文本备份
    
    Args:
        episode_num: 集数
        script_content: 剧本内容
        title: 标题
        max_width: 最大列宽
        wrap_length: 单元格字数超过此值自动换行
    """

    # 1. 创建保存目录
    base_dir = "outputs/FinalOutput/Scripts"
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    folder_path = os.path.join(base_dir, timestamp)
    os.makedirs(folder_path, exist_ok=True)

    # 2. 保存原始文本备份 (防止解析失败)
    txt_filename = f"{title}_EP{episode_num}.txt"
    txt_path = os.path.join(folder_path, txt_filename)
    with open(txt_path, "w", encoding="utf-8") as f:
        f.write(script_content)

    # 3. 解析 Markdown 表格并导出 Excel
    try:
        # 提取所有的表格行 (以 | 开头和结尾的行)
        table_lines = [line.strip() for line in script_content.split('\n') if '|' in line]
        
        if len(table_lines) < 3:  # 至少要有表头、分割线、内容行
            print(f"⚠️ 第 {episode_num} 集内容未检测到标准分镜表格，仅保存为文本。")
            return

        # 将表格行拼接成字符串流
        table_data = "\n".join(table_lines)
        
        # 使用 pandas 读取 (sep='|' 是关键)
        df = pd.read_csv(io.StringIO(table_data), sep="|", skipinitialspace=True).dropna(axis=1, how='all')
        
        # 清洗数据：
        # 去除表头下方的分割线行 (如 ---|---|---)
        df = df[~df.iloc[:, 0].astype(str).str.contains('---')]
        # 去除列名中的空格
        df.columns = [c.strip() for c in df.columns]
        # 去除单元格内容前后的空格
        df = df.map(lambda x: x.strip() if isinstance(x, str) else x)

        # 保存为 Excel
        excel_filename = f"{title}_EP{episode_num}_分镜表.xlsx"
        excel_path = os.path.join(folder_path, excel_filename)
        
        # 先使用 pandas 保存
        df.to_excel(excel_path, index=False, engine='openpyxl')
        
        # ========== 新增：设置单元格格式 ==========
        # 使用 openpyxl 加载工作簿
        wb = load_workbook(excel_path)
        ws = wb.active
        
        # 设置所有单元格自动换行
        for row in ws.iter_rows():
            for cell in row:
                # 如果单元格内容长度超过指定字数，设置自动换行
                if cell.value and len(str(cell.value)) > wrap_length:
                    cell.alignment = Alignment(wrap_text=True, vertical='center')
                    # 可选：增加行高以适应多行文本
                    ws.row_dimensions[cell.row].height = 15 * (len(str(cell.value)) // wrap_length + 1)
        
        # 可选：调整列宽
        for column in ws.columns:
            max_length = 0
            column_letter = column[0].column_letter
            
            # 计算该列最大内容长度
            for cell in column:
                if cell.value:
                    try:
                        if len(str(cell.value)) > max_length:
                            max_length = len(str(cell.value))
                    except:
                        pass
            
            # 设置列宽（限制最大宽度）
            adjusted_width = min(max_length + 2, max_width)
            ws.column_dimensions[column_letter].width = adjusted_width
        
        # 保存修改
        wb.save(excel_path)
        # ========== 新增结束 ==========
        
        print(f"📊 分镜表已成功导出: {excel_path}")
        print(f"   - 设置了自动换行（字数超过{wrap_length}自动换行）")
        print(f"   - 列宽已调整为合适大小（最大{max_width}）")

    except Exception as e:
        print(f"❌ Excel 导出失败 (解析错误): {e}")
        print("💡 已保留 .txt 原始文件。")
    """
    将剧本内容保存为 Excel 分镜表和 纯文本备份
    """
    # 1. 创建保存目录
    base_dir = "outputs/FinalOutput/Scripts"
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    folder_path = os.path.join(base_dir, timestamp)
    os.makedirs(folder_path, exist_ok=True)

    # 2. 保存原始文本备份 (防止解析失败)
    txt_filename = f"{title}_EP{episode_num}.txt"
    txt_path = os.path.join(folder_path, txt_filename)
    with open(txt_path, "w", encoding="utf-8") as f:
        f.write(script_content)

    # 3. 解析 Markdown 表格并导出 Excel
    try:
        # 提取所有的表格行 (以 | 开头和结尾的行)
        table_lines = [line.strip() for line in script_content.split('\n') if '|' in line]
        
        if len(table_lines) < 3:  # 至少要有表头、分割线、内容行
            print(f"⚠️ 第 {episode_num} 集内容未检测到标准分镜表格，仅保存为文本。")
            return

        # 将表格行拼接成字符串流
        table_data = "\n".join(table_lines)
        
        # 使用 pandas 读取 (sep='|' 是关键)
        # index_col=False 防止将第一列误认为索引
        df = pd.read_csv(io.StringIO(table_data), sep="|", skipinitialspace=True).dropna(axis=1, how='all')
        
        # 清洗数据：
        # 去除表头下方的分割线行 (如 ---|---|---)
        df = df[~df.iloc[:, 0].astype(str).str.contains('---')]
        # 去除列名中的空格
        df.columns = [c.strip() for c in df.columns]
        # 去除单元格内容前后的空格
        df = df.map(lambda x: x.strip() if isinstance(x, str) else x)

        # 保存为 Excel
        excel_filename = f"{title}_EP{episode_num}_分镜表.xlsx"
        excel_path = os.path.join(folder_path, excel_filename)
        
        # 使用 openpyxl 引擎保存
        df.to_excel(excel_path, index=False, engine='openpyxl')
        
        print(f"📊 分镜表已成功导出: {excel_path}")

    except Exception as e:
        print(f"❌ Excel 导出失败 (解析错误): {e}")
        print("💡 已保留 .txt 原始文件。")