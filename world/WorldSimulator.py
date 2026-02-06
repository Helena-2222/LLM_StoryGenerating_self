'''
包含信息包括：
地点
资源
物理限制与社会规定

角色在这里进行行动、交互（表演剧情）
'''
# world/WorldSimulator.py
class WorldSimulator:
    def __init__(self, world_config):
        self.config = world_config
        self.state_log = []

    def get_world_prompt(self):
        return f"""
        当前地点：{self.config['location']}
        资源状况：{self.config['resources']}
        物理限制与法规：{self.config['rules']}
        """

    def update_world(self, action_result):
        # 记录角色行动对世界的影响
        self.state_log.append(action_result)