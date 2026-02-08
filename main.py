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
# main.py
import asyncio
import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI

# 正确导入你的模块
from preprocess.Character_preprocess import preprocess_character, Actor
from preprocess.WorldView_preprocess import preprocess_worldview
from revise.director import Director
from outputs.FinalOutput.FinalOutput import save_final_script

load_dotenv()

async def main():
    # 1. 初始化模型
    llm = ChatOpenAI(
        model='deepseek-chat',
        openai_api_key=os.getenv("DEEPSEEK_API_KEY"),
        openai_api_base='https://api.deepseek.com'
    )

    # 2. 预处理数据
    with open("inputs/Science_Fiction/WorldViewSetting.txt", "r", encoding="utf-8") as f:
        world_data = preprocess_worldview(f.read(), llm)
    
    actors = []
    char_dir = "inputs/Science_Fiction/characters"
    for filename in os.listdir(char_dir):
        if filename.endswith(".txt"):
            with open(os.path.join(char_dir, filename), "r", encoding="utf-8") as f:
                profile = preprocess_character(f.read(), llm)
                actors.append(Actor(llm, profile))

    # 3. 初始化导演
    director = Director(llm)

    # 4. 生成剧情循环
    with open("inputs/Science_Fiction/HistorySetting.txt", "r", encoding="utf-8") as f:
        history = f.read()

    with open("inputs/Science_Fiction/SeriesTitle.txt", "r", encoding="utf-8") as f:
        title = f.read()
    
    current_ep=1
    max_ep=3
    max_retries = 1  # 最大重试次数

    
    # 5. 生成剧情循环
    for episode_num in range(current_ep, max_ep + 1):
        print(f"\n{'='*20} 🎬 开始制作 第 {episode_num} 集 {'='*20}")
        
        success = False
        retry_count = 0
        current_guidance = "" # 初始导演指引为空
        
        while not success and retry_count < max_retries:
            if retry_count > 0:
                print(f"🔄 正在进行第 {retry_count} 次重写尝试...")

            episode_script = ""  # 本集累计剧本
            target_length = 800  # 目标字数
            
            # --- 演员接龙表演逻辑 ---
            while len(episode_script) < target_length:
                for actor in actors:
                    # 传入历史、当前集已写内容，以及导演的修改建议
                    action_resp = await actor.act(
                        world_context=str(world_data), 
                        history=history + "\n" + episode_script,
                        director_guidance=current_guidance
                    )
                    content = action_resp.content.strip()
                    episode_script += content + "\n\n"
                    
                    if len(episode_script) >= target_length:
                        break
            
            # --- 导演审核逻辑 ---
            print(f"🧐 剧本生成完毕（约{len(episode_script)}字），提交导演审核...")
            review_result = await director.review(episode_script, episode_num)
            
            if "PASS" in review_result.upper():
                print(f"✅ 第 {episode_num} 集审核通过！已保存。")
                save_final_script(episode_num, episode_script, title)
                history += f"\n--- 第 {episode_num} 集回顾 ---\n{episode_script}" # 更新长久记忆
                success = True
            else:
                retry_count += 1
                current_guidance = review_result # 将导演的批评作为下一轮的指令
                print(f"❌ 审核未通过 (尝试 {retry_count}/{max_retries})")
                print(f"📢 导演反馈：{review_result[:100]}...") # 打印简略反馈

        if not success:
            print(f"⚠️ 警告：第 {episode_num} 集在 {max_retries} 次重试后仍未通过，自动进入下一集。")
            #save_final_script(episode_num, episode_script, title)
            #history += f"\n--- 第 {episode_num} 集回顾 ---\n{episode_script}" # 更新长久记忆

    print("\n🏁 剧本创作任务完成！")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass