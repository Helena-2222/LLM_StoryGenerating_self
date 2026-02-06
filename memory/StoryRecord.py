#将角色在世界环境中的行动串成剧本

# memory/StoryRecord.py

class StoryRecorder:
    @staticmethod
    async def extract_drama_snapshot(llm, episode_script):
        """
        从长篇剧本中提取戏剧性核心，存入 Storage，避免琐碎记忆。
        """
        prompt = f"""
        请将以下剧本压缩为三个关键点：
        1. 产生的核心冲突 (Conflict)
        2. 角色关系发生的实质性变化 (Relationship Change)
        3. 留下的待解悬念 (Cliffhanger)
        
        剧本内容：{episode_script}
        """
        response = await llm.ainvoke(prompt)
        return response.content