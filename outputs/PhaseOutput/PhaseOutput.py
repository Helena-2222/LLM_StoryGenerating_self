# outputs/PhaseOutput/PhaseOutput.py
class PhaseLogger:
    @staticmethod
    def log_draft(episode, content):
        print(f"\n[第 {episode} 集 角色生成初稿]\n{'-'*30}\n{content}\n")

    @staticmethod
    def log_review(episode, feedback):
        color = "\033[92m" if "PASS" in feedback.upper() else "\033[91m"
        print(f"{color}[第 {episode} 集 导演审核意见] -> {feedback}\033[0m")