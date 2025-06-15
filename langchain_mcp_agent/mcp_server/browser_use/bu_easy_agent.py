import asyncio
import os
import sys
# Optional: Set the OLLAMA host to a remote server
base_path = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(base_path)
from dotenv import load_dotenv
load_dotenv()

from browser_use.agent.views import AgentHistoryList
from langchain_mcp_agent.mcp_server.browser_use._agent_master import AgentMaster
from langchain_mcp_agent.mcp_server.browser_use.controller.mine_controller import MineController

class BUEasyAgent(AgentMaster):
    main_model_name="qwen3:30b-nothink"
    planner_model_model_name="qwen3:30b-nothink"
    controller = MineController()
    
    task_template= """
Answere the following question with a quick research.
  question: {task}
"""
    
    async def run_search(self, task:str) -> AgentHistoryList:
        prompt = self.task_template.format(task=task)
        result: AgentHistoryList = None
        if task.strip():
            agent1 = self.getAgent(task=prompt.strip())
            result = await agent1.run(max_steps=self._max_steps)
        return result.final_result()

async def main():
    agent = BUEasyAgent(enable_memory=False)
    result = await agent.act('Find the number of bones in the human body')
    print('\n\n', result.final_result())

if __name__ == '__main__':
	asyncio.run(main())
