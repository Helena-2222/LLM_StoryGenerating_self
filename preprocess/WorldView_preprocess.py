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
import json
import re
from pydantic import BaseModel, Field
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import PydanticOutputParser

# --- 定义世界观模型 ---
class WorldModel(BaseModel):
    time_period: str = Field(description="时代背景")
    location: str = Field(description="地理位置与空间结构")
    physics_rules: str = Field(description="魔法/物理底层规则")
    social_env: str = Field(description="社会/政治/经济环境")
    power_structure: str = Field(description="权力结构与关键冲突点")
    logic_consistency: str = Field(
        default="逻辑自洽：魔法规则与社会冲突保持一致。", 
        description="世界观逻辑自洽性说明"
    )

def preprocess_worldview(raw_text: str, llm):
    parser = PydanticOutputParser(pydantic_object=WorldModel)
    
    prompt = ChatPromptTemplate.from_template(
        "You are a master screenwriter. Based on the raw text, extract and expand a detailed worldview guide.\n"
        "【Strict Requirements】:\n"
        "1. Output MUST be in strict JSON format. Use ONLY English double quotes (\").\n"
        "2. Do NOT use unescaped double quotes inside strings.\n"
        "{format_instructions}\n"
        "Raw Settings: {raw_text}"
    )
    
    # 修改变量名，避开 Python 关键字/内置库名
    world_chain = prompt | llm
    
    response = world_chain.invoke({
        "raw_text": raw_text, 
        "format_instructions": parser.get_format_instructions()
    })
    
    content = response.content

    # --- 强力清洗逻辑 ---
    # 1. 提取 JSON 块
    if "{" in content and "}" in content:
        content = content[content.find("{"):content.rfind("}")+1]
    
    # 2. 物理替换中文标点
    rep = {"“": '"', "”": '"', "：": ":", "，": ",", "；": ";"}
    for k, v in rep.items():
        content = content.replace(k, v)

    # 3. 修复字符串内部非法引号：寻找夹在汉字或字母中间的引号并替换
    content = re.sub(r'([\u4e00-\u9fa5\w])"([\u4e00-\u9fa5\w])', r'\1“\2', content)

    # 4. 移除多余换行
    content = content.replace("\\n", " ").replace("\n", " ")

    try:
        return parser.parse(content)
    except Exception:
        print("⚠️ 世界观解析微调中...")
        try:
            # 最后的保底措施
            raw_dict = json.loads(content, strict=False)
            return WorldModel(**raw_dict)
        except Exception as e:
            print(f"❌ 严重解析错误，内容预览：{content[:200]}")
            raise e