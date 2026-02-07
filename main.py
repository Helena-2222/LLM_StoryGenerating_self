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
    with open("inputs/WorldViewSetting.txt", "r", encoding="utf-8") as f:
        world_data = preprocess_worldview(f.read(), llm)
    
    with open("inputs/CharacterSetting.txt", "r", encoding="utf-8") as f:
        char_raw = f.read()
        # 简单起见，这里假设你的 preprocess 返回一个 Actor 列表
        # 如果你之前只处理单人，这里需要稍微修改逻辑来循环处理
        char_profile = preprocess_character(char_raw, llm) 
        actor = Actor(llm, char_profile) # 先以哈利为例跑通

    # 3. 初始化导演
    director = Director(llm)

    # 4. 生成剧情循环
    with open("inputs/HistorySetting.txt", "r", encoding="utf-8") as f:
        init = f.read()

    with open("inputs/SeriesTitle.txt", "r", encoding="utf-8") as f:
        title = f.read()
    
    current_ep=1
    max_ep=3

    print(f"🚀 开始生成第1集剧本...")
    
    # 模拟角色行动
    action_resp = await actor.act(str(world_data), init)
    draft_script = action_resp.content
    
    # 导演审核
    review_result = await director.review(draft_script, 1)
        
    if "PASS" in review_result.upper():
        save_final_script(1, draft_script, title)
    else:
        print(f"❌ 导演要求重写：{review_result}")
        # 这里可以加入重试逻辑

    history = init + "\n" + draft_script
    for episode_num in range(current_ep+1, max_ep + 1):
        print(f"🚀 开始生成第{episode_num}集剧本...")
    
        # 模拟角色行动
        action_resp = await actor.act(str(world_data), history)
        draft_script = action_resp.content

        # 导演审核
        review_result = await director.review(draft_script, episode_num)
        
        if "PASS" in review_result.upper():
            save_final_script(episode_num, draft_script, title)
        else:
            print(f"❌ 导演要求重写：{review_result}")
            # 这里可以加入重试逻辑
        history += "\n" + draft_script

if __name__ == "__main__":
    asyncio.run(main())