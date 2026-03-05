from fastapi.staticfiles import StaticFiles
from fastapi import FastAPI, BackgroundTasks
from pydantic import BaseModel
import uuid
import os
import traceback  # 1. 必须导入这个库

# 导入你现有的逻辑
from main import main as run_story_generation 

app = FastAPI(title="AI 剧本分镜生成器")
# 这行代码的意思是：把本地的 outputs 文件夹映射到网址的 /download 路径下
app.mount("/download", StaticFiles(directory="outputs"), name="download")

# 定义输入模型
class StoryRequest(BaseModel):
    story_id: str = "Rebirth"
    max_ep: int = 13
    target_length: int = 800

# 模拟一个简单的任务状态存储
tasks = {}

@app.post("/generate_story")
async def generate_story_api(request: StoryRequest, background_tasks: BackgroundTasks):
    """
    接收请求并启动生成任务
    """
    task_id = str(uuid.uuid4())
    tasks[task_id] = {"status": "processing", "result": None}
    
    # 异步执行生成逻辑，不阻塞请求返回
    background_tasks.add_task(run_wrapper, task_id, request)
    
    return {"task_id": task_id, "message": "任务已启动，请稍后查询结果"}


async def run_wrapper(task_id, request):
    try:
        # 你的业务逻辑
        result = await run_story_generation (
            max_ep=request.max_ep, 
            target_length=request.target_length
        )
        tasks[task_id] = {"status": "completed", "result": result}
        print(f"✅ 任务 {task_id} 完成")
        
    except Exception as e:
        # 2. 关键：这行代码会将详细的错误行号、调用过程直接打在 VS Code 的黑色控制台里
        print(f"❌ 任务 {task_id} 发生崩溃，详细错误堆栈如下：")
        traceback.print_exc() 
        
        # 3. 也可以把详细错误返回给 API 响应体（方便在浏览器看）
        full_error = traceback.format_exc()
        tasks[task_id] = {
            "status": "failed", 
            "error": str(e),
            "details": full_error  # 把详细堆栈塞进返回结果
        }

@app.get("/check_result/{task_id}")
async def check_result(task_id: str):
    """
    根据 task_id 查询生成进度和结果
    """
    return tasks.get(task_id, {"status": "not_found"})

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)