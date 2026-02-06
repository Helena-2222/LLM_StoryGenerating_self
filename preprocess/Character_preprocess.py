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
import re
import json
from typing import Optional
from pydantic import BaseModel, Field, field_validator
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import PydanticOutputParser

class CharacterProfile(BaseModel):
    name: str = Field(description="Name")
    age: str = Field(description="Age")
    gender: str = Field(description="Gender")
    occupation: str = Field(description="Occupation")
    ethnicity_belief: str = Field(description="Ethnicity/Belief")
    # 核心改动：不仅给默认值，还允许接受 None 并将其转为字符串
    appearance: Optional[str] = Field(default="To be added", description="Appearance")
    personality: Optional[str] = Field(default="To be added", description="Personality")
    values: Optional[str] = Field(default="To be added", description="Values")
    skills: Optional[str] = Field(default="To be added", description="Skills")
    motivation: Optional[str] = Field(default="To be added", description="Motivation")
    weakness: Optional[str] = Field(default="To be added", description="Weakness")
    backstory: Optional[str] = Field(default="To be added", description="Backstory")
    social_network: Optional[str] = Field(default="To be added", description="Social Network")

    # 增加一个校验器，如果 AI 传了 null (None)，强制变回字符串
    @field_validator('*', mode='before')
    @classmethod
    def prevent_null(cls, v):
        if v is None:
            return "Pending expansion"
        return v
    
class Actor:
    def __init__(self, llm, profile: CharacterProfile, prompt_path="inputs/prompts/character_actor.txt"):
        self.llm = llm
        self.profile = profile
        self.prompt_path = prompt_path
        self._load_actor_prompt()

    def _load_actor_prompt(self):
        if not os.path.exists(self.prompt_path):
            self.base_prompt = "你正在扮演一个角色，请根据设定进行戏剧化表演。"
        else:
            with open(self.prompt_path, "r", encoding="utf-8") as f:
                self.base_prompt = f.read()

    async def act(self, world_context: str, history: str):
        profile_json = self.profile.model_dump_json()
        messages = [
            {"role": "system", "content": f"{self.base_prompt}\n\n角色设定：\n{profile_json}"},
            {"role": "user", "content": f"背景：{world_context}\n历史：{history}\n开始表演："}
        ]
        return await self.llm.ainvoke(messages)

def preprocess_character(single_char_text: str, llm):
    parser = PydanticOutputParser(pydantic_object=CharacterProfile)
    prompt = ChatPromptTemplate.from_template(
        "你是一个金牌编剧。请根据片段提取信息并生成严格的JSON。\n"
        "【禁令】：绝对不准使用中文引号“”或分号；，必须全部使用英文标点。\n"
        "{format_instructions}\n内容：{raw_text}"
    )
    
    char_chain = prompt | llm
    response = char_chain.invoke({"raw_text": single_char_text, "format_instructions": parser.get_format_instructions()})
    content = response.content

    # --- 强力清洗：物理脱水 ---
    # 1. 提取大括号内容
    if "{" in content and "}" in content:
        content = content[content.find("{"):content.rfind("}")+1]
    
    # 2. 强行替换所有中文标点
    rep = {"“": '"', "”": '"', "‘": "'", "’": "'", "：": ":", "，": ",", "；": ";"}
    for k, v in rep.items():
        content = content.replace(k, v)
    
    # 3. 移除多余的换行符和反斜杠
    content = content.replace("\\n", " ").replace("\\", "/")
    
    # 4. 处理赫敏那种结尾被截断的情况（如果最后没有 } 则补上）
    content = content.strip()
    if not content.endswith("}"):
        content += '"}'

    try:
        # 先用标准 json 加载，再喂给 Pydantic 增加容错
        data = json.loads(content, strict=False)
        return CharacterProfile(**data)
    except Exception as e:
        print(f"DEBUG - 失败的JSON内容: {content}")
        # 如果还是不行，可能是键名后面漏了冒号，最后尝试一种正则表达式修复
        content = re.sub(r'(\w)"\s*:\s*', r'\1": ', content)
        data = json.loads(content, strict=False)
        return CharacterProfile(**data)