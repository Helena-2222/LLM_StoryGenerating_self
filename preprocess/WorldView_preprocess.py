#S1.读取世界观文档中的信息

'''
S2.如果信息缺乏，则补充缺乏信息,确保信息包括：
1.故事发生时间
2.故事发生地点
3.物理环境
4.社会环境（政治、经济、文化）

补充信息后要向用户说明补充的内容
'''

#S3.把处理好的世界观交给环境模拟器
# preprocess/WorldView_preprocess.py
import os
from pydantic import BaseModel, Field
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import PydanticOutputParser

# 1. 定义世界观模型
class WorldProfile(BaseModel):
    time_period: str = Field(description="故事发生的时间")
    location: str = Field(description="故事发生地点")
    physical_env: str = Field(description="物理环境（重力、气候、特殊现象）")
    social_env: str = Field(description="社会环境（政治、经济、文化背景）")
    rules: str = Field(description="核心规则：物理限制与社会规定")
    resource_dist: str = Field(description="资源分布状况")
    logic_supplement: str = Field(description="为了逻辑自洽补充的额外世界观细节")

# 2. 预处理函数
def preprocess_worldview(raw_text: str, llm):
    parser = PydanticOutputParser(pydantic_object=WorldProfile)
    
    prompt = ChatPromptTemplate.from_template(
        "你是一个资深世界观架构师。请从以下文本中提取世界观设定。\n"
        "如果信息缺乏，请基于逻辑进行扩充，确保信息包括时间、地点、物理环境、社会环境。\n"
        "{format_instructions}\n"
        "原始设定：{raw_text}"
    )
    
    chain = prompt | llm | parser
    
    full_world = chain.invoke({
        "raw_text": raw_text, 
        "format_instructions": parser.get_format_instructions()
    })
    
    print(f"✅ 世界观 [{full_world.location}] 预处理完成，已补全社会背景与规则。")
    return full_world