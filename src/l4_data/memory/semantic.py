import logging
import uuid

logger = logging.getLogger(__name__)


class SemanticMemoryManager:
    def __init__(self, chroma_path: str):
        self.chroma_path = chroma_path
        self._client = None
        self._collection_knowledge = None
        self._collection_facts = None

    def _ensure_client(self):
        if self._client is not None:
            return

        try:
            import chromadb
            from chromadb.config import Settings
            self._client = chromadb.PersistentClient(
                path=self.chroma_path,
                settings=Settings(anonymized_telemetry=False),
            )
            self._collection_knowledge = self._client.get_or_create_collection(
                name="user_knowledge",
                metadata={"description": "用户讨论过的技术知识"},
            )
            self._collection_facts = self._client.get_or_create_collection(
                name="conversation_facts",
                metadata={"description": "对话中提到的事实性信息"},
            )
            logger.info("ChromaDB 初始化完成: %s", self.chroma_path)
        except ImportError:
            logger.warning("chromadb 未安装，语义记忆功能不可用")
        except Exception as e:
            logger.error("ChromaDB 初始化失败: %s", e)

    def add_memory(self, text: str, metadata: dict = None, collection: str = "user_knowledge",
                   memory_id: str = None):
        self._ensure_client()
        if self._client is None:
            return

        coll = self._collection_knowledge if collection == "user_knowledge" else self._collection_facts
        if coll is None:
            return

        mem_id = memory_id or str(uuid.uuid4())
        meta = metadata or {}
        meta["source"] = "conversation"

        try:
            coll.add(
                documents=[text],
                metadatas=[meta],
                ids=[mem_id],
            )
            logger.debug("语义记忆已添加: id=%s, collection=%s", mem_id, collection)
        except Exception as e:
            logger.error("添加语义记忆失败: %s", e)

    def search(self, query: str, n_results: int = 5, collection: str = "user_knowledge",
               filter_dict: dict = None) -> list:
        self._ensure_client()
        if self._client is None:
            return []

        coll = self._collection_knowledge if collection == "user_knowledge" else self._collection_facts
        if coll is None:
            return []

        try:
            kwargs = {
                "query_texts": [query],
                "n_results": min(n_results, coll.count() or 1),
            }
            if filter_dict:
                kwargs["where"] = filter_dict

            results = coll.query(**kwargs)

            items = []
            if results and results["documents"]:
                for i, doc in enumerate(results["documents"][0]):
                    item = {"text": doc}
                    if results["metadatas"] and results["metadatas"][0]:
                        item["metadata"] = results["metadatas"][0][i]
                    if results["distances"] and results["distances"][0]:
                        item["distance"] = results["distances"][0][i]
                    items.append(item)
            return items
        except Exception as e:
            logger.error("语义检索失败: %s", e)
            return []

    def add_conversation_knowledge(self, messages: list[dict]):
        user_messages = [m["content"] for m in messages if m["role"] == "user"]
        if not user_messages:
            return

        for msg in user_messages:
            if len(msg) > 10:
                self.add_memory(msg, {"type": "user_message"}, "conversation_facts")

    def get_context_for_prompt(self, query: str, limit: int = 5) -> str:
        results = self.search(query, n_results=limit, collection="user_knowledge")
        results += self.search(query, n_results=limit, collection="conversation_facts")

        if not results:
            return ""

        results.sort(key=lambda x: x.get("distance", 999))
        results = results[:limit]

        parts = ["【相关记忆】"]
        for r in results:
            parts.append(f"- {r['text'][:200]}")

        return "\n".join(parts)

    def get_stats(self) -> dict:
        self._ensure_client()
        if self._client is None:
            return {"available": False}

        try:
            return {
                "available": True,
                "knowledge_count": self._collection_knowledge.count() if self._collection_knowledge else 0,
                "facts_count": self._collection_facts.count() if self._collection_facts else 0,
            }
        except Exception:
            return {"available": True, "knowledge_count": 0, "facts_count": 0}
