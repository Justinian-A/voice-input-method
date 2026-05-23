"""控制台用户界面"""

import sys
from typing import Optional

from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from rich.live import Live

from src.core.engine import VoiceInputEngine, EngineState, RecognitionResult


class ConsoleUI:
    """控制台用户界面"""

    def __init__(self, engine: VoiceInputEngine):
        self.engine = engine
        self.console = Console()
        self.is_running = False
        self.results: list[str] = []

        # 注册回调
        self.engine.on_result(self._on_result)

    def _on_result(self, result: RecognitionResult):
        """处理识别结果"""
        self.results.append(result.text)

        # 自动复制到剪贴板
        self._copy_to_clipboard(result.text)

        # 显示结果
        self._display_result(result)

    def _display_result(self, result: RecognitionResult):
        """显示识别结果"""
        confidence_color = "green" if result.confidence > 0.8 else "yellow" if result.confidence > 0.6 else "red"

        text = Text()
        text.append("识别结果: ", style="bold blue")
        text.append(result.text, style="white")
        text.append(f"  置信度: {result.confidence:.1%}", style=confidence_color)

        self.console.print(text)

    def _copy_to_clipboard(self, text: str):
        """复制文本到剪贴板"""
        try:
            import subprocess
            subprocess.run(["clip"], input=text.encode(), check=True, capture_output=True)
        except Exception:
            pass

    def _get_state_display(self) -> str:
        """获取状态显示文本"""
        state = self.engine.get_state()
        state_map = {
            EngineState.IDLE: "[bold yellow]● 空闲[/bold yellow]",
            EngineState.LISTENING: "[bold green]● 正在监听...[/bold green]",
            EngineState.PROCESSING: "[bold cyan]● 处理中...[/bold cyan]",
            EngineState.ERROR: "[bold red]● 错误[/bold red]",
        }
        return state_map.get(state, "未知")

    def start(self):
        """启动控制台界面"""
        self.is_running = True

        self.console.print(Panel(
            "[bold green]语音输入法已启动[/bold green]\n"
            "按 [bold cyan]Enter[/bold cyan] 开始/停止录音\n"
            "按 [bold cyan]q[/bold cyan] 退出",
            title="语音输入法 v0.1.0"
        ))

        while self.is_running:
            try:
                self.console.print(f"\n状态: {self._get_state_display()}")
                user_input = self.console.input("[bold cyan]>>> [/bold cyan]")

                if user_input.lower() == "q":
                    self.stop()
                    break
                elif user_input == "":
                    self._toggle_listening()
                else:
                    self.console.print("[yellow]请输入 q 退出或按 Enter 切换录音状态[/yellow]")

            except KeyboardInterrupt:
                self.stop()
                break

    def _toggle_listening(self):
        """切换录音状态"""
        if self.engine.get_state() == EngineState.IDLE:
            self.console.print("[bold green]开始录音...[/bold green]")
            self.engine.start_listening()
        else:
            self.console.print("[bold yellow]停止录音[/bold yellow]")
            self.engine.stop_listening()

    def stop(self):
        """停止界面"""
        self.is_running = False
        if self.engine.get_state() != EngineState.IDLE:
            self.engine.stop_listening()

        # 显示历史记录
        if self.results:
            self.console.print("\n[bold]识别历史:[/bold]")
            for i, text in enumerate(self.results, 1):
                self.console.print(f"  {i}. {text}")

        self.console.print("[bold green]已退出语音输入法[/bold green]")
