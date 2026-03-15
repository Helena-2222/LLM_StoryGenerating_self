import os

class PhaseOutput:
    @staticmethod
    def show_episode_preview(episode_num, title, content, director_review=None):
        """
        在控制台美化输出当前集数的预览内容
        """
        # 获取控制台宽度，适配显示
        try:
            term_width = os.get_terminal_size().columns
        except OSError:
            term_width = 80
        
        divider = "=" * term_width
        sub_divider = "-" * term_width

        # 1. 打印头部信息
        print("\n" + divider)
        print(f"🎬 剧集预览：{title} | 第 {episode_num} 集".center(term_width))
        print(divider)
        
        # 3. 打印剧本正文
        print(f"【📄 剧本正文详情】：\n")
        
        # 处理 Markdown 表格，让它在控制台阅读更友好
        lines = content.strip().split('\n')
        for line in lines:
            if '|' in line:
                # 简单的对齐处理：将 | 替换为更美观的垂直线条
                styled_line = line.replace('|', '┃')
                print(f"  {styled_line}")
            else:
                print(f"  {line}")

        print("\n" + divider)
        print(f"💡 系统提示：请审阅上方内容，决定是否进入下一集".center(term_width))
        print(divider + "\n")

    @staticmethod
    def show_status(msg):
        """打印简单的状态提示"""
        print(f"💡 [系统状态]: {msg}")