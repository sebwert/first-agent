import asyncio
import os
import sys
# Optional: Set the OLLAMA host to a remote server
base_path = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.append(base_path)
from dotenv import load_dotenv
load_dotenv()

import asyncio
import enum
import json
import logging
import re
from typing import Generic, TypeVar, cast

from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.prompts import PromptTemplate
from playwright.async_api import ElementHandle, Page

from pydantic import BaseModel

from browser_use.agent.views import ActionModel, ActionResult
from browser_use.browser import BrowserSession
from browser_use.controller.registry.service import Registry
from browser_use.controller.views import (
	ClickElementAction,
	CloseTabAction,
	DoneAction,
	DragDropAction,
	GoToUrlAction,
	InputTextAction,
	NoParamsAction,
	OpenTabAction,
	Position,
	ScrollAction,
	SearchGoogleAction,
	SendKeysAction,
	SwitchTabAction,
)
from browser_use.controller.service import Controller
from browser_use.utils import time_execution_sync

logger = logging.getLogger(__name__)


Context = TypeVar('Context')


class MineController(Controller):
    def __init__(
        self,
        exclude_actions: list[str] = ['drag_drop', 'read_cell_contents', 'read_sheet_contents', 
                                      'update_cell_contents', 'clear_cell_contents', 
                                      'select_cell_or_range', 'fallback_input_into_single_selected_cell'],
        output_model: type[BaseModel] | None = None,
    ):
        super().__init__(exclude_actions=exclude_actions, output_model=output_model)
        THINK_TAGS = re.compile(r'<think>.*?</think>', re.DOTALL)
        STRAY_CLOSE_TAG = re.compile(r'.*?</think>', re.DOTALL)
        def _remove_last_closing_if_unbalanced(text):
            count_open = sum(1 for char in text if char == '{')
            count_close = sum(1 for char in text if char == '}')
            
            if count_open < count_close:
                # Remove the last occurrence of '}'
                last_index = text.rfind('}')
                if last_index != -1:
                    text = text[:last_index] + text[last_index + 1:]
            
            return text
        def _remove_think_tags(text: str) -> str:
            # Step 1: Remove well-formed <think>...</think>
            text = re.sub(THINK_TAGS, '', text)
            # Step 2: If there's an unmatched closing tag </think>,
            #         remove everything up to and including that.
            text = re.sub(STRAY_CLOSE_TAG, '', text)
            text = _remove_last_closing_if_unbalanced(text)
            return text.strip()
            # Content Actions
        @self.registry.action(
            'Extract page content to retrieve specific information from the page, e.g. all company names, a specific description, all information about xyc, 4 links with companies in structured format. Use include_links true if the goal requires links. Use include_img true if the goal requires images',
        )
        async def extract_content(
            goal: str,
            page: Page,
            page_extraction_llm: BaseChatModel,
            include_links: bool = False,
            include_img: bool = False,
        ):
            from functools import partial

            import markdownify

            strip = []
            if not include_links:
                strip.append('a')
            if not include_img:
                strip.append('img')

            # Run markdownify in a thread pool to avoid blocking the event loop
            loop = asyncio.get_event_loop()
            page_html = await page.content()
            markdownify_func = partial(markdownify.markdownify, strip=strip)
            content = await loop.run_in_executor(None, markdownify_func, page_html)

            # manually append iframe text into the content so it's readable by the LLM (includes cross-origin iframes)
            for iframe in page.frames:
                try:
                    await iframe.wait_for_load_state(timeout=5000)  # extra on top of already loaded page
                except Exception as e:
                    pass

                if iframe.url != page.url and not iframe.url.startswith('data:'):
                    content += f'\n\nIFRAME {iframe.url}:\n'
                    # Run markdownify in a thread pool for iframe content as well
                    try:
                        iframe_html = await iframe.content()
                        iframe_markdown = await loop.run_in_executor(None, markdownify_func, iframe_html)
                    except Exception as e:
                        logger.debug(f'Error extracting iframe content from within page {page.url}: {type(e).__name__}: {e}')
                        iframe_markdown = ''
                    content += iframe_markdown

            prompt = 'Your task is to extract the content of the page. You will be given a page and a goal and you should extract all relevant information around this goal from the page. If the goal is vague, summarize the page. Respond in json format. Extraction goal: {goal}, Page: {page}'
            template = PromptTemplate(input_variables=['goal', 'page'], template=prompt)
            try:
                output = await page_extraction_llm.ainvoke(template.format(goal=goal, page=content))
                cleaned_content = _remove_think_tags(output.content)
                output.content = cleaned_content
                msg = f'📄  Extracted from page\n: {output.content}\n'
                logger.info(msg)
                return ActionResult(extracted_content=msg, include_in_memory=True)
            except Exception as e:
                logger.debug(f'Error extracting content: {e}')
                msg = f'📄  Extracted from page\n: {content}\n'
                logger.info(msg)
                return ActionResult(extracted_content=msg)
            # Basic Navigation Actions
        @self.registry.action(
            description='Extract search page results for links or collections of next level pages',
            allowed_domains=['*.google.com', '*.bing.com','*.duckduckgo.com']
        )
        async def extract_search_page_result(
            goal: str,
            page: Page,
            page_extraction_llm: BaseChatModel,
        ):
            from functools import partial

            import markdownify

            strip = ['img']

            # Run markdownify in a thread pool to avoid blocking the event loop
            loop = asyncio.get_event_loop()
            page_html = await page.content()
            markdownify_func = partial(markdownify.markdownify, strip=strip)
            content = await loop.run_in_executor(None, markdownify_func, page_html)

            prompt = 'Your task is to extract the content of the page and list all search results with their target urls. You get a goal. Validate the Links against this goal. Respond in json format. Extraction goal: {goal}, Page: {page}'
            template = PromptTemplate(input_variables=['goal', 'page'], template=prompt)
            try:
                output = await page_extraction_llm.ainvoke(template.format(goal=goal, page=content))
                cleaned_content = _remove_think_tags(output.content)
                output.content = cleaned_content
                msg = f'🔀  Extracted from search result\n: {output.content}\n'
                logger.info(msg)
                return ActionResult(extracted_content=msg, include_in_memory=True)
            except Exception as e:
                logger.debug(f'Error extracting search result: {e}')
                msg = f'🔀  Extracted from search result\n: {content}\n'
                logger.info(msg)
                return ActionResult(extracted_content=msg)
            # Basic Navigation Actions
        @self.registry.action(
            'Search the in Google for something with a query',
            param_model=SearchGoogleAction,
        )
        async def search_google(params: SearchGoogleAction, browser_session: BrowserSession):
            search_url = f'https://www.google.com/search?q={params.query}&udm=14'

            page = await browser_session.get_current_page()
            if page.url.strip('/') == 'https://www.google.com':
                await page.goto(search_url)
                await page.wait_for_load_state()
            else:
                page = await browser_session.create_new_tab(search_url)

            msg = f'🔍🕶️ Searched for "{params.query}" in Google'
            logger.info(msg)
            return ActionResult(extracted_content=msg, include_in_memory=True)
        @self.registry.action(
            'Get next 10 Google search results',
            allowed_domains=['*.google.com/search']
        )
        async def next_ten_google_results(browser_session: BrowserSession):
            from urllib.parse import urlparse, parse_qs, urlencode, urlunparse
            page = await browser_session.get_current_page()
            search_url = page.url

            parsed = urlparse(search_url)
            query_params = parse_qs(parsed.query)

            # Get current start value, default to 0
            current_start = int(query_params.get('start', [0])[0])
            next_start = current_start + 10

            # Update the start parameter
            query_params['start'] = [str(next_start)]

            # Rebuild the URL
            new_query = urlencode(query_params, doseq=True)
            new_url = urlunparse(parsed._replace(query=new_query))
        
            await page.goto(new_url)
            await page.wait_for_load_state()

            msg = f'⏭️📄 Next 10 Google search results starting from "{str(next_start)}" loaded'
            logger.info(msg)
            return ActionResult(extracted_content=msg, include_in_memory=True)
        
        @self.registry.action(
            'Search the in Bing for something with a query',
            param_model=SearchGoogleAction,
        )
        async def search_bing(params: SearchGoogleAction, browser_session: BrowserSession):
            search_url = f'https://www.bing.com/search?q{params.query}'

            page = await browser_session.get_current_page()
            if page.url.strip('/') == 'https://www.bing.com':
                await page.goto(search_url)
                await page.wait_for_load_state()
            else:
                page = await browser_session.create_new_tab(search_url)

            msg = f'🔍✨  Searched for "{params.query}" in Bing'
            logger.info(msg)
            return ActionResult(extracted_content=msg, include_in_memory=True)
        @self.registry.action(
            'Search the in DuckDuckGo for something with a query',
            param_model=SearchGoogleAction,
        )
        async def search_duckduckgo(params: SearchGoogleAction, browser_session: BrowserSession):
            search_url = f'https://duckduckgo.com/?q?q{params.query}'

            page = await browser_session.get_current_page()
            if page.url.strip('/') == 'https://duckduckgo.com.com':
                await page.goto(search_url)
                await page.wait_for_load_state()
            else:
                page = await browser_session.create_new_tab(search_url)

            msg = f'🔍🦆  Searched for "{params.query}" in DuckDuckGo'
            return ActionResult(extracted_content=msg, include_in_memory=True)


