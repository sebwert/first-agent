import asyncio
import os
import sys
# Optional: Set the OLLAMA host to a remote server
base_path = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
sys.path.append(base_path)
from dotenv import load_dotenv
load_dotenv()

import json
from langchain_ollama import ChatOllama
from langchain.callbacks.base import BaseCallbackHandler



class ModelServant:
    def __init__(self):
        """Load model configuration from models.json file"""
        models_file = f"{base_path}/models.json"
        
        if models_file.exists():
            try:
                with open(models_file, 'r') as f:
                    return json.load(f)
            except (json.JSONDecodeError, FileNotFoundError) as e:
                raise(f"Error loading models.json: {e}")
        else:
            raise("models.json not found, using empty config")
    
    def getModel(self, modelName):
        class_name = self.models.get(modelName)['class_name']
        kwargs = self.models.get(modelName)['kwargs']
        
        # Convert string to actual class
        if class_name == 'ChatOllama':
            from langchain_ollama import ChatOllama
            model_class = ChatOllama
        
        return model_class(**kwargs)