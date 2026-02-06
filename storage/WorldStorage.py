'''

资源变化
世界大事记

'''
# storage/WorldStorage.py
import json

class WorldStorage:
    def __init__(self):
        self.log_file = "storage/data/world_state.json"

    def update_event(self, episode_num, resource_change, major_event):
        """记录世界大事记，用于回溯节点"""
        state = {
            "episode": episode_num,
            "resources": resource_change,
            "events": major_event
        }
        with open(self.log_file, 'a', encoding='utf-8') as f:
            f.write(json.dumps(state, ensure_ascii=False) + "\n")