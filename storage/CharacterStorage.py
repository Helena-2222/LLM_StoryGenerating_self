'''
动态记录角色历史信息：
行动（极其日常的琐事除外）
情绪状态
认知状态
人际关系状态
技能状态
'''
# storage/CharacterStorage.py
import json

class CharacterStorage:
    def __init__(self, char_id):
        self.char_id = char_id
        self.history_file = f"storage/data/char_{char_id}_history.json"

    def record_step(self, episode_num, action, emotion, relations, skills):
        """记录阶段性模拟成果"""
        snapshot = {
            "episode": episode_num,
            "action": action,
            "emotion": emotion,
            "relationships": relations,
            "skills": skills
        }
        # 这里建议用追加方式保存，或者存入数据库
        with open(self.history_file, 'a', encoding='utf-8') as f:
            f.write(json.dumps(snapshot, ensure_ascii=False) + "\n")

