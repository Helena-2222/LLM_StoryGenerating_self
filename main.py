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
from preprocess.Character_preprocess import preprocess_character, Actor, CharacterProfile
from preprocess.WorldView_preprocess import preprocess_worldview
from revise.director import Director
from outputs.FinalOutput.FinalOutput import save_final_script

load_dotenv()

async def get_speaker_scores(llm, actors, world_context, current_history):
    """【决策中心】：动态评估角色发言优先级"""
    actor_info = "\n".join([f"- {a.profile.name}: {a.profile.personality} (目标: {a.profile.motivation})" for a in actors])
    
    score_prompt = (
        f"你是一位资深剧本导演。请根据当前情境，评估各角色的发言优先级。\n"
        f"【角色设定】：\n{actor_info}\n"
        f"【环境】：{world_context}\n"
        f"【近期剧情】：\n{current_history[-600:]}\n\n"
        "请为每个角色打分（0.0-1.0）：1.状态 2.动机 3.性格 4.时机。\n"
        "请严格按此JSON格式输出：\n"
        '{"角色名": {"total_score": 综合分, "reason": "简述原因"}}'
    )

    try:
        response = await llm.ainvoke(score_prompt)
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

    # --- 存档路径设置 ---
    story_id = "Rebirth"
    session_dir = f"sessions/{story_id}"
    char_cache_dir = f"{session_dir}/characters_cache"
    os.makedirs(char_cache_dir, exist_ok=True)
    
    world_cache_path = f"{session_dir}/worldview_cache.json"
    history_state_path = f"{session_dir}/history_state.txt"

    # 2. 预处理世界观 (增加空文件校验)
    world_cache_path = f"{session_dir}/worldview_cache.json"
    world_data = None

    if os.path.exists(world_cache_path) and os.path.getsize(world_cache_path) > 0:
        print("\n♻️ 发现世界观缓存，正在秒级加载...")
        try:
            with open(world_cache_path, "r", encoding="utf-8") as f:
                world_data = json.load(f)
        except json.JSONDecodeError:
            print("⚠️ 缓存文件损坏，准备重新生成...")

    if not world_data:
        print("\n🌍 正在初始化世界观设定...")
        with open(f"inputs/{story_id}/WorldViewSetting.txt", "r", encoding="utf-8") as f:
            world_data = preprocess_worldview(f.read(), llm)
            # 写入缓存
            with open(world_cache_path, "w", encoding="utf-8") as f:
                content = world_data.model_dump_json() if hasattr(world_data, 'model_dump_json') else json.dumps(world_data)
                f.write(content)

    # 3. 加载角色 (带缓存校验逻辑)
    print("\n👥 正在唤醒角色灵魂...")
    actors = []
    char_input_dir = f"inputs/{story_id}/characters"
    
    for filename in sorted(os.listdir(char_input_dir)):
        if filename.endswith(".txt"):
            char_name = filename.replace(".txt", "")
            cache_path = f"{char_cache_dir}/{char_name}_profile.json"
            profile = None
            
            # 只有当文件存在且大小大于 0 时才尝试加载
            if os.path.exists(cache_path) and os.path.getsize(cache_path) > 0:
                try:
                    with open(cache_path, "r", encoding="utf-8") as f:
                        profile_data = json.load(f)
                        profile = CharacterProfile(**profile_data)
                    print(f"  - 角色 [{char_name}] 加载自缓存存档")
                except (json.JSONDecodeError, Exception) as e:
                    print(f"  - 角色 [{char_name}] 缓存损坏，准备重新生成...")

            # 如果没加载成功，则重新预处理
            if profile is None:
                print(f"  - 角色 [{char_name}] 正在进行初始 AI 补全...")
                with open(os.path.join(char_input_dir, filename), "r", encoding="utf-8") as f:
                    profile = preprocess_character(f.read(), llm)
                    # 写入缓存
                    with open(cache_path, "w", encoding="utf-8") as f:
                        f.write(profile.model_dump_json())
            
            actors.append(Actor(llm, profile))

    # 4. 初始化历史与标题
    director = Director(llm)
    with open(f"inputs/{story_id}/SeriesTitle.txt", "r", encoding="utf-8") as f:
        title = f.read().strip()

    # 断点续传逻辑
    if os.path.exists(history_state_path):
        with open(history_state_path, "r", encoding="utf-8") as f:
            history = f.read()
        # 通过计算历史记录中的标记，确定起始集数
        completed_eps = history.count("--- 第") 
        start_ep = completed_eps + 1
        print(f"🎬 检测到历史存档，将从第 {start_ep} 集开始接龙...")
    else:
        with open(f"inputs/{story_id}/HistorySetting.txt", "r", encoding="utf-8") as f:
            history = f.read()
        start_ep = 1

    max_ep = 12
    target_length = 800
    max_retries = 1

    # 5. 创作大循环
    for episode_num in range(start_ep, max_ep + 1):
        print(f"\n{'='*20} 🎬 第 {episode_num} 集 创作开始 {'='*20}")
        
        success = False
        retry_count = 0
        current_guidance = ""
        
        while not success and retry_count < max_retries:
            episode_script = ""
            consecutive_count = {a.profile.name: 0 for a in actors}
            
            print(f"📡 导演正在决策发言权 (尝试 {retry_count + 1})...")

            while len(episode_script) < target_length:
                scores = await get_speaker_scores(llm, actors, str(world_data), history + "\n" + episode_script)
                sorted_actors = sorted(actors, key=lambda a: scores.get(a.profile.name, {}).get('total_score', 0), reverse=True) if scores else actors

                current_actor = sorted_actors[0]
                if consecutive_count[current_actor.profile.name] >= 2 and len(sorted_actors) > 1:
                    current_actor = sorted_actors[1]

                print(f"🎤 [{current_actor.profile.name}] 获得发言权 (长度: {len(episode_script)})")
                action_resp = await current_actor.act(
                    world_context=str(world_data),
                    history=history + "\n" + episode_script,
                    director_guidance=current_guidance
                )
                
                content = action_resp.content.strip()
                episode_script += content + "\n\n"

                for name in consecutive_count:
                    consecutive_count[name] = consecutive_count[name] + 1 if name == current_actor.profile.name else 0

                if len(episode_script) >= target_length:
                    break

            # 导演审核
            print(f"🧐 正在审片...")
            review_result = await director.review(episode_script, episode_num)
            
            if "PASS" in review_result.upper():
                print(f"✨ 审核通过！")
                save_final_script(episode_num, episode_script, title)
                history += f"\n--- 第 {episode_num} 集剧情回顾 ---\n{episode_script}"
                success = True
            else:
                retry_count += 1
                current_guidance = review_result
                print(f"❌ 导演拒绝: {review_result[:60]}...")

        # 兜底：若重试耗尽，强制出片
        if not success:
            print(f"⚠️ 第 {episode_num} 集重试耗尽，强制采用最后版本。")
            save_final_script(episode_num, episode_script, title)
            history += f"\n--- 第 {episode_num} 集剧情回顾 (强行通过) ---\n{episode_script}"
            success = True

        # 每集结束，实时同步历史到 sessions 目录
        with open(history_state_path, "w", encoding="utf-8") as f:
            f.write(history)

    print("\n🏁 剧本创作任务完成！缓存已更新，历史已存入 sessions 目录。")

if __name__ == "__main__":
    asyncio.run(main())