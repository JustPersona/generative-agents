import re
import sys
import json
import requests
from urllib.parse import quote, unquote
from bs4 import BeautifulSoup
from bs4.element import Tag, NavigableString

sys.path.append('../../')

from global_methods import *
from persona.prompt_template.gpt_structure import *
from persona.prompt_template.print_prompt import *



def run_gpt_prompt_identify_vulnerable_files():
    def create_prompt_input(attack, test_input=None): 
        if test_input: return test_input
        prompt_input = [attack]
        return prompt_input
    
    def __func_clean_up(llama_response, prompt=""):
        try:
            response_json = json.loads(llama_response)
            for key in response_json:
                if isinstance(response_json[key], list):
                    response_json[key] = [item.strip() for item in response_json[key]]
                elif isinstance(response_json[key], str):
                    response_json[key] = response_json[key].strip()
            return json.dumps(response_json, ensure_ascii=False, indent=2)
        except json.JSONDecodeError:
            return llama_response

    def __func_validate(gpt_response, prompt=""):
        try:
            response_json = json.loads(gpt_response)
            required_fields = ["description", "attack_steps", "vulnerable_http_responses", "possible_impacts"]
            return all(field in response_json for field in required_fields) and \
                isinstance(response_json["description"], str) and \
                all(isinstance(step, str) for step in response_json["attack_steps"]) and \
                all(isinstance(response, str) for response in response_json["vulnerable_http_responses"]) and \
                all(isinstance(impact, str) for impact in response_json["possible_impacts"])
        except json.JSONDecodeError:
            return False

    def get_fail_safe(): 
        return "ERROR"

    gpt_param = ''
    prompt_template = "persona/prompt_template/v4/explanation_of_attack.txt"
    prompt_input = create_prompt_input(attack, test_input)
    prompt = generate_prompt(prompt_input, prompt_template)
    fail_safe = get_fail_safe()
    output = safe_generate_response_json(prompt, gpt_param, 5, fail_safe,
                                    __func_validate, __func_clean_up)
        
    return output, [output, prompt, gpt_param, prompt_input, fail_safe]


