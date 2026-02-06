'''
导演审核剧情逻辑：
1.故事结构：开端（导火索事件）、发展、高潮、结局
2.有趣性
3.情节连贯性
4.角色动机合理性

若不符合以上要求，导演可以重新调整剧情
若故事太过平淡，则导演有权插入关键事件，推动故事进行
循环直到剧情符合要求

最终将通过的剧情交给输出器输出
'''

# revise/director.py
from langchain_core.messages import HumanMessage, SystemMessage
import os

class Director:
    def __init__(self, llm, prompt_path="inputs/prompts/director_system.txt"):
        self.llm = llm
        # 动态加载 Prompt 文件
        self.system_prompt = self._load_prompt(prompt_path)

    def _load_prompt(self, path):
        if not os.path.exists(path):
            raise FileNotFoundError(f"找不到 Prompt 文件: {path}")
        with open(path, "r", encoding="utf-8") as f:
            return f.read()

    async def review(self, draft_content, episode_num):
        # 构造消息
        messages = [
            {"role": "system", "content": self.system_prompt},
            {"role": "user", "content": f"这是第{episode_num}集的初稿，请审阅：\n\n{draft_content}"}
        ]
        
        response = await self.llm.ainvoke(messages)
        return response.content
    
    