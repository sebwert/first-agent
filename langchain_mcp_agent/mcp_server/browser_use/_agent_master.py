import asyncio
import os
import sys
# Optional: Set the OLLAMA host to a remote server
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.append(base_path)
from dotenv import load_dotenv
load_dotenv()

from browser_use import Agent
from browser_use.agent.views import AgentHistoryList
from browser_use.agent.memory import MemoryConfig
from browser_use.browser import BrowserProfile, BrowserSession
from tools._model_servant import ModelServant
from langchain_core.language_models.chat_models import BaseChatModel, LangSmithParams
from browser_use.controller.service import Controller

class AgentMaster:
	def __init__(self, **kwargs):
		for key in kwargs:
			if key in self.agentConfig:
				self.agentConfig[key] = kwargs[key] 
    
		if 'main_model' in kwargs:
			self.main_model_name = kwargs['main_model']
		if 'planner_model' in kwargs:
					self.planner_model_model_name = kwargs['planner_model']
		if 'extract_model' in kwargs:
					self.extract_model_model_name = kwargs['extract_model']
     
		if 'task' in kwargs:
			self.task = kwargs['task']
		if 'extend_system_message' in kwargs:
			self.extend_system_message = kwargs['extend_system_message']
		if 'extend_planner_system_message' in kwargs:
			self.extend_planner_system_message = kwargs['extend_planner_system_message']
		if 'max_steps' in kwargs:
			self._max_steps = kwargs['max_steps']
		if 'initial_actions' in kwargs:
			self._initial_actions = kwargs['initial_actions']
   
		self.setModels()
		self.setMemory()

	task = """
	Do something stupid with your head
	"""

	extend_system_message = """
	DONT LOGIN ANYWHERE. DONT USE TRIPADVISOR. Use english for saving results.
	"""
	extend_planner_system_message="""
	START WITH SEARCH engines like google, bing or duckduckgo. SET ALL PAGES TO ENGLISH LANGUAGE. DONT USE TRIPADVISOR.
	"""
 
	agent: Agent = None
	agentConfig = {
		'max_actions_per_step': 10,
		'use_vision': False,
		'enable_memory': True,
		'validate_output': False,
		'tool_calling_method': 'auto', #'function_calling', 'json_mode', 'raw', 'auto', 'tools'
		'planner_interval':5,
		'is_planner_reasoning': True,
		'max_input_tokens': 40000,
		'max_failures': 10,
	}
	main_model_name: str = None
	main_model: BaseChatModel = None
	embedder_model_name: str = None
	embedder_model: BaseChatModel = None
	planner_model_model_name: str = None
	planner_model: BaseChatModel = None
	extract_model_model_name: str = None
	extract_model: BaseChatModel = None
	memory: MemoryConfig = None
	controller: Controller = None

	_max_steps = 999
	_initial_actions = None
	
	_browser_profile = BrowserProfile(
		window_size={'width': 900, 'height': 1280},  # Small size for demonstration
		# **playwright.devices['iPhone 13']         # or you can use a playwright device profile
		device_scale_factor=1.0,                  # change to 2~3 to emulate a high-DPI display for high-res screenshots
		# viewport={'width': 800, 'height': 600},   # set the viewport (aka content size)
		# screen={'width': 800, 'height': 600},     # hardware display size to report to websites via JS
		headless=True,  # Use non-headless mode to see the window
	)
 	#TODO: Make browser setting configurable
	_browser_session = BrowserSession(
		browser_profile=_browser_profile,
		user_data_dir='~/.config/browseruse/profiles/stealth',
		#stealth=True,
		headless=True,
		disable_security=False,
		#deterministic_rendering=False,
	)

	async def run_search(self) -> AgentHistoryList:
		agent = self.getAgent()
		result: str = None
		if self.task.strip():
			result = await agent.run(max_steps=self._max_steps)
		return result

	def setModels(self):
		
		Servant = ModelServant()
		if self.main_model_name:
			self.main_model=Servant.getModel(self.main_model_name)
			#self.agentConfig['max_input_tokens'] = self.main_model['kwargs']['num_ctx']
   
		if self.embedder_model_name:
			self.embedder_model=Servant.getModel(self.embedder_model_name)
		else:
			self.embedder_model=self.main_model   
   
		if self.planner_model_model_name:
			self.planner_model= Servant.getModel(self.planner_model_model_name)
		else:
			self.extend_planner_system_message = None
   
		if self.extract_model_model_name:
			self.extract_model=Servant.getModel(self.extract_model_model_name)
  
	def getAgent(self, **kwargs) -> Agent: 
		agent =  Agent(
			task					= kwargs['task'] if 'task' in kwargs else self.task,
			extend_system_message	= kwargs['extend_system_message'] if 'extend_system_message' in kwargs else self.extend_system_message,
			extend_planner_system_message= kwargs['extend_planner_system_message'] if 'extend_planner_system_message' in kwargs else  self.extend_planner_system_message,
   			page_extraction_llm		= kwargs['extract_model'] if 'extract_model' in kwargs else  self.extract_model,
			llm						= kwargs['main_model'] if 'main_model' in kwargs else  self.main_model,
			planner_llm				= kwargs['planner_model'] if 'planner_model' in kwargs else self.planner_model,
			memory_config			= kwargs['memory'] if 'memory' in kwargs else self.memory,
			browser_session			= kwargs['_browser_session'] if '_browser_session' in kwargs else self._browser_session,
			initial_actions			= kwargs['_initial_actions'] if '_initial_actions' in kwargs else self._initial_actions,
			controller				= kwargs['controller'] if 'controller' in kwargs else self.controller,
			max_actions_per_step	= kwargs['max_actions_per_step'] if 'max_actions_per_step' in kwargs else self.agentConfig['max_actions_per_step'],
			use_vision				= kwargs['use_vision'] if 'use_vision' in kwargs else self.agentConfig['use_vision'],
			#save_conversation_path="logs/conversation",
			enable_memory			= kwargs['enable_memory'] if 'enable_memory' in kwargs else self.agentConfig['enable_memory'],
			validate_output			= kwargs['validate_output'] if 'validate_output' in kwargs else self.agentConfig['validate_output'],
			tool_calling_method		= kwargs['tool_calling_method'] if 'tool_calling_method' in kwargs else self.agentConfig['tool_calling_method'], #'function_calling', 'json_mode', 'raw', 'auto', 'tools'
			planner_interval		= kwargs['planner_interval'] if 'planner_interval' in kwargs else self.agentConfig['planner_interval'],
			is_planner_reasoning	= kwargs['is_planner_reasoning'] if 'is_planner_reasoning' in kwargs else self.agentConfig['is_planner_reasoning'],
			max_input_tokens		= kwargs['max_input_tokens'] if 'max_input_tokens' in kwargs else self.agentConfig['max_input_tokens'],
			max_failures			= kwargs['max_failures'] if 'max_failures' in kwargs else self.agentConfig['max_failures']
		)
		return agent

	def setMemory(self):
		if self.agentConfig['enable_memory']:
			self.memory = MemoryConfig( # Ensure llm_instance is passed if not using default LLM config
				llm_instance=self.embedder_model,      # Important: Pass the agent's LLM instance here
				agent_id="my_custom_agent",
				memory_interval=5
			)




