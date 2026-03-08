import uuid
import asyncio
from typing import List, Optional, Dict, Any
from fastapi import FastAPI, BackgroundTasks, HTTPException
from pydantic import BaseModel
from main import main as run_story_main  # 导入你的主逻辑函数

app = FastAPI(title="AI 剧本创作系统")

# --- 数据模型 ---
class CharacterInput(BaseModel):
    name: str
    description: str

class StoryRequest(BaseModel):
    story_id: str = "Rebirth"
    max_ep: int = 15
    target_length: int = 800
    worldview_text: Optional[str] = None  # 可选：直接输入世界观
    characters_list: Optional[List[CharacterInput]] = None  # 可选：直接输入角色列表

# 任务状态存储
tasks: Dict[str, Any] = {}

async def run_wrapper(task_id: str, request: StoryRequest):
    try:
        # 调用 main.py 里的主函数
        result = await run_story_main(
            story_id=request.story_id,
            max_ep=int(request.max_ep),
            target_length=int(request.target_length),
            max_retries = 1,
            worldview_text=request.worldview_text,
            characters_list=request.characters_list
        )
        tasks[task_id] = {"status": "completed", "result": result}
    except Exception as e:
        import traceback
        traceback.print_exc() # 在控制台打印详细报错
        tasks[task_id] = {"status": "failed", "error": str(e)}

@app.post("/generate_story")
async def generate_story(request: StoryRequest, background_tasks: BackgroundTasks):
    task_id = str(uuid.uuid4())
    tasks[task_id] = {"status": "processing"}
    background_tasks.add_task(run_wrapper, task_id, request)
    return {"task_id": task_id, "message": "任务已启动，请通过查询接口查看进度"}

@app.get("/check_result/{task_id}")
async def check_result(task_id: str):
    if task_id not in tasks:
        raise HTTPException(status_code=404, detail="任务不存在")
    return tasks[task_id]

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)