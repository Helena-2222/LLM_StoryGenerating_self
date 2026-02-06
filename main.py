#1.信息读取与处理
#读取世界观文档中的信息
#读取角色设定文档中的信息
#读取故事梗概中的信息
#补充缺乏信息

#2.剧情生成
#角色表演，形成剧情
#输出剧情文本

#3.剧情调整
#导演接收当前剧情，审判剧情

#调整剧情，直到符合要求

#4.输出剧情文本
import os
import asyncio
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI

# 导入你的组件
from preprocess.Character_preprocess import preprocess_character, Actor
from preprocess.WorldView_preprocess import preprocess_worldview
from revise.director import Director
from outputs.FinalOutput.FinalOutput import save_final_script

max_episodes=1

load_dotenv()

def clean_duplicate_lines(text):
    """剔除模型可能产生的连续重复行"""
    lines = text.split('\n')
    cleaned = []
    for i in range(len(lines)):
        if i > 0 and lines[i].strip() == lines[i-1].strip() and len(lines[i].strip()) > 0:
            continue
        cleaned.append(lines[i])
    return '\n'.join(cleaned).strip()

async def main():
    # 1. 初始化 DeepSeek 模型
    llm = ChatOpenAI(
        model='deepseek-chat',
        openai_api_key=os.getenv("DEEPSEEK_API_KEY"),
        openai_api_base='https://api.deepseek.com',
        temperature=0.7,
        model_kwargs={
            "presence_penalty": 0.6,
            "frequency_penalty": 0.8
        }
    )

    # 2. 预处理世界观
    print("\n🌍 正在处理世界观设定...")
    world_setting_path = "inputs/WorldViewSetting.txt"
    with open(world_setting_path, "r", encoding="utf-8") as f:
        world_profile = preprocess_worldview(f.read(), llm)
    
    # 3. 遍历文件夹动态加载角色
    print("\n👥 正在加载角色设定...")
    char_dir = "inputs/characters"
    actors = []
    if os.path.exists(char_dir):
        for filename in os.listdir(char_dir):
            if filename.endswith(".txt"):
                file_path = os.path.join(char_dir, filename)
                with open(file_path, "r", encoding="utf-8") as f:
                    char_content = f.read()
                try:
                    profile = preprocess_character(char_content, llm)
                    actors.append(Actor(llm, profile))
                    print(f"     ✅ [ {profile.name} ] 就绪")
                except Exception as e:
                    print(f"     ❌ [ {filename} ] 加载失败 (解析错误)")

    if not actors:
        print("💥 错误：没有演员成功登场，请检查角色文件内容。")
        return

    # 4. 初始化导演
    director = Director(llm)

    # 5. 生成主循环
    current_ep = 1
    history = f"Prologue: {', '.join([a.profile.name for a in actors])} have gathered at the scene."

    while current_ep <= max_episodes:
        print(f"\n{'='*30} 第 {current_ep} 集 {'='*30}")
        
        # 整合背景信息
        char_info = "\n".join([f"- {a.profile.name}: {a.profile.personality}" for a in actors])
        world_context = f"{world_profile.model_dump_json()}\n\n【Cast】:\n{char_info}"
        
        success = False
        retry_count = 0
        
        while not success and retry_count < 3:
            print(f"🎬 演员表演中 (尝试 {retry_count + 1}/3)...")
            
            # 由第一顺位角色（通常是哈利）领衔主演
            response = await actors[0].act(world_context, history)
            draft_script = clean_duplicate_lines(response.content)

            # --- 核心改进：即时展示剧情 ---
            print(f"\n📜 --- [ 第 {current_ep} 集剧本草稿 ] ---")
            print(draft_script)
            print("-" * 40 + "\n")

            print(f"🧐 导演正在审核...")
            review = await director.review(draft_script, current_ep)
            
            # 判断逻辑：如果导演给 PASS，或者虽然 REWRITE 但你觉得行
            if "PASS" in review.upper():
                print(f"✨ 导演签收：本集通过！")
                save_final_script(current_ep, draft_script, "Project_Alpha")
                history += f"\nEP{current_ep} Summary: {draft_script[-200:]}"
                success = True
            else:
                print(f"⚠️ 导演反馈：\n{review}")
                print("\n" + "-"*20)
                cmd = input("👉 操作：[c] 让AI按建议重写, [a] 强行通过此稿, [m] 我来改, [q] 退出: ").lower()
                
                if cmd == 'a':
                    print(f"🚀 制作人干预：强行通过！")
                    save_final_script(current_ep, draft_script, "Project_Alpha")
                    history += f"\nEP{current_ep} Summary: {draft_script[-200:]}"
                    success = True
                elif cmd == 'm':
                    manual_text = input("✍️ 请输入最终定稿内容: ")
                    save_final_script(current_ep, manual_text, "Manual_Fix")
                    history += f"\nEP{current_ep} Summary: {manual_text[-200:]}"
                    success = True
                elif cmd == 'q':
                    print("🎬 拍摄暂停。")
                    return
                else:
                    retry_count += 1
                    print("🔄 准备进行重写...")

        if success:
            current_ep += 1
        else:
            print("❌ 连续尝试失败，请检查模型状态或调整设定。")
            break

    print("\n🏁 全剧终。")

if __name__ == "__main__":
    asyncio.run(main())