from pydantic import BaseModel
from typing import List, Dict, Optional, ClassVar, Any
import json
from ..CacheManager import CacheManager
from .ChatStorage import ChatStorage
from .ChatMessage import ChatMessage
from .GenerateContentRequest import GenerateContentRequest
from ..CacheConfig import CacheConfig
from google import genai
from google.genai import types
from ..Tool import Tool
from ..utils.logger import get_logger

logger = get_logger()

class ChatManager(BaseModel):
    system_prompt: str
    chat_storage: ChatStorage
    cache_manager: CacheManager
    default_config: ClassVar[Dict] = {
        "automatic_function_calling": {"disable": True},
        "tool_config": {"function_calling_config": {"mode": "auto"}},
    }

    async def generate_content_request(
        self,
        chat_id: str,
        model: str,
        client: genai.Client,
        query: str,
        tools: List[Tool] = [],
        tool_mode: str = "auto",
        cache_config: Optional[CacheConfig] = None,
        context: Optional[List[Dict[str, Any]]] = None,
    ) -> GenerateContentRequest:
        logger.info(f"Generating content request for chat_id: {chat_id}, model: {model}")
        logger.debug(f"Tools provided: {[tool.name for tool in tools]}")
        # Prepare the config with context cache and tools.
        config = self.default_config.copy()
        if cache_config:
            logger.debug("Cache configuration provided, getting config with cache")
            config = await self.__get_config_with_cache(model, client, cache_config)
        config = await self.__get_config_with_tools(config, tools, tool_mode)

        # If the there is already a conversation history, just append the query to it.
        messages = await self.chat_storage.get_history(chat_id)
        if messages or cache_config:
            logger.debug("Appending query to existing conversation history")
            messages.append(ChatMessage.from_user_query(query))
        else:
            logger.debug("Creating new conversation with system prompt")
            messages = [ChatMessage.from_user_query(self.__create_prompt_with_query(query, context))]

        return GenerateContentRequest(
            contents=messages,
            config=config
        )
    
    async def __get_config_with_cache(self, model: str, client: genai.Client, cache_config: CacheConfig) -> Dict:
        logger.debug("Getting config with cache")
        config = self.default_config.copy()
        cache_name = None
        if cache_config.auto_manage_cache:
            logger.debug("Auto-managing cache")
            cache_name = await self.cache_manager.create_or_update_cache(
                client=client,
                model=model,
                content=self.system_prompt,
                ttl=cache_config.ttl,
                cache_name=cache_config.cache_name,
            )
        elif cache_config.cache_name:
            logger.debug(f"Using existing cache: {cache_config.cache_name}")
            cache_name = await self.cache_manager.get_cache(client, cache_config.cache_name)
        
        if cache_config and not cache_name:
            logger.error("Failed to obtain cache name despite having cache configuration")
            raise ValueError("Failed to obtain cache name despite having cache configuration")
        
        if cache_name:
            logger.debug(f"Adding cache name to config: {cache_name}")
            config["cached_content"] = cache_name
        return config
    
    async def __get_config_with_tools(self, config: Dict, tools: List[Tool], tool_mode: str = "auto") -> Dict:
        logger.debug(f"Getting config with tools, mode: {tool_mode}")
        config["tools"] = [types.Tool(function_declarations=[tool.function_definition for tool in tools])]
        if not tools:
            logger.debug("No tools provided, setting tool mode to auto")
            tool_mode = "auto"
        config["tool_config"] = {"function_calling_config": {"mode": tool_mode}}
        return config
    
    def __create_prompt_with_query(self, query: str, context: Optional[List[Dict[str, Any]]] = None) -> str:
        logger.debug("Creating prompt with query")
        context_str = ""
        if context:
            try:
                context_json = json.dumps(context)
                context_str = f"\n<initial_context>\n{context_json}\n</initial_context>"
            except Exception as e:
                logger.error(f"Failed to serialize context: {str(e)}")
        
        final_prompt = f"""{self.system_prompt}

CURRENT TASK:
<user_query>{query}</user_query>{context_str}"""

        logger.debug("Final prompt with context:")
        logger.debug(final_prompt)
        
        return final_prompt