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
        self.prompt_path = prompt_path
        self.base_prompt = self._load_actor_prompt()

    def _load_actor_prompt(self):
        """从外部文件加载角色行动逻辑模板"""
        if not os.path.exists(self.prompt_path):
            # 如果文件不存在，给一个基础兜底，防止报错
            return "你正在扮演一个角色，请根据设定进行戏剧化表演。"
        with open(self.prompt_path, "r", encoding="utf-8") as f:
            return f.read()

    # preprocess/Character_preprocess.py 核心修改部分

    async def act(self, world_context: str, history: str, director_guidance: str = ""):
        # 强制要求剧本格式和字数控制
        format_instruction = (
            f"### 你的身份：{self.profile.name}\n"
            f"### 表演格式要求：\n"
            f"1. 必须严格遵守剧本格式：角色名【行动描述】：对话内容\n"
            f"2. 每次行动描述控制在10字以内，对话内容控制在 30 个字以内。\n"
            f"3. 你的行动要符合性格设定：{self.profile.personality}\n"
        )
        
        full_system_prompt = f"{self.base_prompt}\n\n{format_instruction}\n# 详细设定：\n{self.profile.model_dump_json()}"
        
        user_input = (
            f"【世界背景】：{world_context}\n"
            f"【前情提要/已发生的对话】：\n{history}\n"
            f"请根据以上信息，接续写下 {self.profile.name} 的一次行动和一句台词："
        )
        
        if director_guidance:
            user_input += f"\n【导演指令】：{director_guidance}"

        messages = [
            {"role": "system", "content": full_system_prompt},
            {"role": "user", "content": user_input}
        ]
        
        return await self.llm.ainvoke(messages)

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