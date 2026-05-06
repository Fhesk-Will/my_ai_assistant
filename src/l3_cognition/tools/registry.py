import logging

logger = logging.getLogger(__name__)


class ToolRegistry:
    """工具/技能动态加载框架（骨架）"""

    def __init__(self):
        self._tools: dict = {}

    def register(self, name: str, handler, description: str = "", triggers: list = None):
        self._tools[name] = {
            "handler": handler,
            "description": description,
            "triggers": triggers or [],
        }
        logger.info("工具已注册: %s", name)

    def unregister(self, name: str):
        self._tools.pop(name, None)

    def get(self, name: str):
        return self._tools.get(name)

    def match(self, query: str) -> list:
        matched = []
        query_lower = query.lower()
        for name, tool in self._tools.items():
            for trigger in tool["triggers"]:
                if trigger.lower() in query_lower:
                    matched.append(name)
                    break
        return matched

    def execute(self, name: str, **kwargs):
        tool = self._tools.get(name)
        if not tool:
            raise ValueError(f"工具未注册: {name}")
        return tool["handler"](**kwargs)

    def list_tools(self) -> list[dict]:
        return [
            {"name": name, "description": t["description"], "triggers": t["triggers"]}
            for name, t in self._tools.items()
        ]
