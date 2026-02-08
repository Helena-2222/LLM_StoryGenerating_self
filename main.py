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
import json
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI

# 导入自定义模块
from preprocess.Character_preprocess import preprocess_character, Actor
from preprocess.WorldView_preprocess import preprocess_worldview
from revise.director import Director
from outputs.FinalOutput.FinalOutput import save_final_script

load_dotenv()

async def get_speaker_scores(llm, actors, world_context, current_history):
    """
    【决策中心】：动态评估角色发言优先级。
    指标：1.短期状态 2.动机 3.性格 4.时机 (各1.0分)
    """
    actor_info = "\n".join([f"- {a.profile.name}: {a.profile.personality} (目标: {a.profile.motivation})" for a in actors])
    
    score_prompt = (
        f"你是一位资深剧本导演。请根据当前情境，评估各角色的发言优先级。\n"
        f"【角色设定】：\n{actor_info}\n"
        f"【环境】：{world_context}\n"
        f"【近期剧情】：\n{current_history[-600:]}\n\n"
        "请为每个角色在以下四项指标（0.0-1.0）打分：\n"
        "1. 状态(State): 情绪波动程度。\n"
        "2. 动机(Motivation): 当前话题与目标的关联度。\n"
        "3. 性格(Personality): 外向/急躁者得分高。\n"
        "4. 时机(Timing): 环境是否利于其介入。\n\n"
        "请严格按此JSON格式输出：\n"
        '{"角色名": {"total_score": 综合分, "reason": "简述原因"}}'
    )

    try:
        response = await llm.ainvoke(score_prompt)
        # 提取JSON块
        text = response.content
        json_str = text[text.find("{"):text.rfind("}")+1]
        return json.loads(json_str)
    except Exception as e:
        print(f"⚠️ 评分系统波动，将采用默认顺序。错误: {e}")
        return None

async def main():
    # 1. 初始化模型
    llm = ChatOpenAI(
        model='deepseek-chat',
        openai_api_key=os.getenv("DEEPSEEK_API_KEY"),
        openai_api_base='https://api.deepseek.com',
        temperature=0.7
    )

    # 2. 预处理世界观
    print("\n🌍 正在初始化世界观设定...")
    with open("inputs/Rebirth/WorldViewSetting.txt", "r", encoding="utf-8") as f:
        world_data = preprocess_worldview(f.read(), llm)
    
    # 3. 加载角色（保持实例，以维持记忆流）
    print("\n👥 正在唤醒角色灵魂...")
    actors = []
    char_dir = "inputs/Rebirth/characters"
    for filename in sorted(os.listdir(char_dir)):
        if filename.endswith(".txt"):
            with open(os.path.join(char_dir, filename), "r", encoding="utf-8") as f:
                profile = preprocess_character(f.read(), llm)
                actors.append(Actor(llm, profile))

    if not actors:
        print("❌ 未检测到有效角色设定，程序退出。")
        return

    # 4. 初始化配置
    director = Director(llm)
    with open("inputs/Rebirth/HistorySetting.txt", "r", encoding="utf-8") as f:
        history = f.read()
    with open("inputs/Rebirth/SeriesTitle.txt", "r", encoding="utf-8") as f:
        title = f.read()

    max_ep = 3
    target_length = 800
    max_retries = 1

    # 5. 创作大循环
    for episode_num in range(1, max_ep + 1):
        print(f"\n{'='*20} 🎬 第 {episode_num} 集 创作开始 {'='*20}")
        
        success = False
        retry_count = 0
        current_guidance = ""
        
        while not success and retry_count < max_retries:
            episode_script = ""
            consecutive_count = {a.profile.name: 0 for a in actors} # 记录连击数
            
            print(f"📡 导演正在根据剧情流分配表演权 (尝试 {retry_count + 1})...")

            while len(episode_script) < target_length:
                # 动态获取当前谁该说话
                scores = await get_speaker_scores(llm, actors, str(world_data), history + "\n" + episode_script)
                
                # 排序逻辑：得分高者优先
                if scores:
                    sorted_actors = sorted(
                        actors, 
                        key=lambda a: scores.get(a.profile.name, {}).get('total_score', 0), 
                        reverse=True
                    )
                else:
                    sorted_actors = actors

                # 选角：如果得分第一的角色已经“连击”超过2次，且还有其他人选，则换人
                current_actor = sorted_actors[0]
                if consecutive_count[current_actor.profile.name] >= 2 and len(sorted_actors) > 1:
                    current_actor = sorted_actors[1]

                # 角色表演
                print(f"🎤 [{current_actor.profile.name}] 获得发言权 (当前集长度: {len(episode_script)})")
                action_resp = await current_actor.act(
                    world_context=str(world_data),
                    history=history + "\n" + episode_script,
                    director_guidance=current_guidance
                )
                
                content = action_resp.content.strip()
                episode_script += content + "\n\n"

                # 更新连击计数
                for name in consecutive_count:
                    if name == current_actor.profile.name:
                        consecutive_count[name] += 1
                    else:
                        consecutive_count[name] = 0

                if len(episode_script) >= target_length:
                    break

            # 导演审核
            print(f"🧐 表演结束，导演正在审片...")
            review_result = await director.review(episode_script, episode_num)
            
            if "PASS" in review_result.upper():
                print(f"✨ 审核通过！")
                save_final_script(episode_num, episode_script, title)
                history += f"\n--- 第 {episode_num} 集剧情回顾 ---\n{episode_script}"
                success = True
            else:
                retry_count += 1
                current_guidance = review_result
                print(f"❌ 导演拒绝签收，重试理由: {review_result[:60]}...")

        if not success:
            print(f"⚠️ 第 {episode_num} 集重试次数已耗尽。")
            print(f"🎬 [强制出片]: 导演虽然不完全满意，但为了进度，我们决定采用最后一次生成的版本。")
            
            # 即使导演没给 PASS，我们也强制保存最后一次的结果
            save_final_script(episode_num, episode_script, title)
            
            # 同时也必须更新历史，否则下一集会失去上下文
            history += f"\n--- 第 {episode_num} 集剧情回顾 (强行通过) ---\n{episode_script}"
            
            # 设置为 True 以便顺利进入下一集
            success = True

    print("\n🏁 剧本创作任务圆满完成！所有文件已按时间戳分类保存。")

if __name__ == "__main__":
    asyncio.run(main())