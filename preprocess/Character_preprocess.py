#S1.读取角色设定文档中的信息

'''
S2.如果信息缺乏，则补充缺乏信息,确保信息包括：
1.基本信息： 姓名、年龄、性别、职业、种族/国籍、信仰
2.外貌特征
3.性格
4.价值观
5.智力与技能
6.目标/行为动机/欲望
7.核心恐惧/弱点
8.记忆与人物小传：影响性格的关键往事
9.社会关系网：谁是朋友？有无宿敌？谁是深爱的人？

补充信息后要向用户说明补充的内容
'''

#S3.把处理好的角色设定交给演员
# preprocess/Character_preprocess.py
import os
from pydantic import BaseModel, Field
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import PydanticOutputParser

# S2. 定义角色全维度模型，确保信息完整
class CharacterProfile(BaseModel):
    name: str = Field(description="姓名")
    age: str = Field(description="年龄")
    gender: str = Field(description="性别")
    occupation: str = Field(description="职业")
    ethnicity_belief: str = Field(description="种族/国籍/信仰")
    appearance: str = Field(description="外貌特征")
    personality: str = Field(description="性格详细描述")
    values: str = Field(description="价值观与处事准则")
    skills: str = Field(description="智力水平与特长技能")
    motivation: str = Field(description="核心目标/行为动机/欲望")
    weakness: str = Field(description="核心恐惧或致命弱点")
    backstory: str = Field(description="影响性格的关键往事/人物小传")
    social_network: str = Field(description="社会关系网（朋友、宿敌、爱人）")

class Actor:
    def __init__(self, llm, profile: CharacterProfile, prompt_path="inputs/prompts/character_actor.txt"):
        self.llm = llm
        self.profile = profile
        self.memory = []          # 记忆流
        self.reflections = "处于初始状态，保持原有性格。"  # 缓存的反思内容
        self.step_count = 0        # 步进计数器
        self.prompt_path = prompt_path
        self.base_prompt = self._load_actor_prompt()

    def _load_actor_prompt(self):
        if not os.path.exists(self.prompt_path):
            return "你正在扮演一个角色，请根据设定进行戏剧化表演。"
        with open(self.prompt_path, "r", encoding="utf-8") as f:
            return f.read()

    async def _reflect(self, current_observation: str):
        """
        内部反思：提炼心态，不向用户输出
        """
        # 只取最近的记忆片段进行高层次抽象
        recent_context = "\n".join(self.memory[-6:]) 
        reflect_prompt = ChatPromptTemplate.from_template(
            "你正在扮演 {name}。请根据以下近期经历：\n{memories}\n"
            "进行一次深度的内心自省。你现在的压力值、信任感和下一步的隐秘打算是什么？\n"
            "请直接给出心态描述（50字以内），严禁输出剧本格式。"
        )
        chain = reflect_prompt | self.llm
        resp = await chain.ainvoke({
            "name": self.profile.name,
            "memories": recent_context + "\n观察：" + current_observation
        })
        self.reflections = resp.content.strip()
        # 重置计数器
        self.step_count = 0

    async def act(self, world_context: str, history: str, director_guidance: str = ""):
        # 1. 更新观察并累加步数
        observation = history.strip().split('\n')[-2:] if history else []
        current_obs = " | ".join(observation)
        self.step_count += 1

        # 2. 每 3 轮执行一次“慢思考”反思，平时只用缓存
        if self.step_count >= 3:
            print(f"🧠 [{self.profile.name}] 正在进行深度反思...") # 调试用，实际运行可关闭
            await self._reflect(current_obs)

        # 3. 构造表演指令（反思内容作为背景，不要求 AI 输出反思过程）
        '''
        format_instruction = (
            f"### 你的身份：{self.profile.name}\n"
            f"### 当前心态（仅供参考，不要输出）：{self.reflections}\n"
            f"### 表演格式要求：\n"
            f"1. 严格使用格式：角色名【行动描述】：对话内容\n"
            f"2. 行动描述 < 10字，台词 < 30字。\n"
            f"3. 你的台词和行动必须体现你当下的心态变化。\n"
        )'''
        
        format_instruction = (
        f"### 你的身份：{self.profile.name}\n"
        f"### 当前心态：{self.reflections}\n"
        f"### 任务：请以分镜师的视角，输出当前剧情的分镜表格。\n"
        f"### 格式要求：\n"
        f"1. 必须使用 Markdown 表格输出。\n"
        f"2. 表格表头为：镜号 | 景别 | 画面内容 | 运镜 | 台词 | 音效 | 特效\n"
        f"3. 保持角色性格，台词要短促有力。\n"
    )
        
        full_system_prompt = f"{self.base_prompt}\n\n{format_instruction}\n# 核心设定：\n{self.profile.model_dump_json()}"
        
        user_input = (
            f"【环境】：{world_context}\n"
            f"【前情】：{history}\n"
            f"请接续：{self.profile.name}【...】：..."
        )
        
        if director_guidance:
            user_input += f"\n【注意】：{director_guidance}"

        messages = [
            {"role": "system", "content": full_system_prompt},
            {"role": "user", "content": user_input}
        ]
        
        response = await self.llm.ainvoke(messages)
        content = response.content.strip()

        # 4. 将自己的表现存入记忆
        self.memory.append(content)
        
        return response
    
# S1 & S2. 读取并补全角色信息逻辑
def preprocess_character(raw_text: str, llm):
    parser = PydanticOutputParser(pydantic_object=CharacterProfile)
    
    prompt = ChatPromptTemplate.from_template(
        "你是一个金牌编剧。请根据以下原始设定，提取并补全角色信息。\n"
        "注意：如果原始设定信息缺失，请发挥想象力进行艺术补充，确保角色具有戏剧张力。\n"
        "{format_instructions}\n"
        "原始设定：{raw_text}"
    )
    
    chain = prompt | llm | parser
    
    # 执行补全
    full_profile = chain.invoke({
        "raw_text": raw_text, 
        "format_instructions": parser.get_format_instructions()
    })
    
    # 向用户说明补充逻辑
    print(f"\n✅ 角色 [{full_profile.name}] 预处理完成：")
    print(f"   - 动机补全：{full_profile.motivation[:30]}...")
    print(f"   - 弱点设定：{full_profile.weakness[:30]}...")
    
    return full_profile