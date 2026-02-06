# outputs/FinalOutput/FinalOutput.py
import os

def save_final_script(episode_num, content, title="未命名短剧"):
    directory = "outputs/FinalOutput/Scripts"
    if not os.path.exists(directory):
        os.makedirs(directory)
    
    file_path = f"{directory}/EP_{episode_num:02d}.md"
    
    formatted_content = f"# {title} - 第 {episode_num} 集\n\n{content}"
    
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(formatted_content)
    print(f"✅ 最终剧本已存至：{file_path}")