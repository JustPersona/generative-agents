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

from utils import *


def run_gpt_prompt_explanation_of_attack(persona, attack, test_input=None):
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
   




def run_gpt_prompt_create_payload(persona, attack, explanation_of_attack, target_url, cookies=None, test_input=None):
    def create_prompt_input(attack, test_input=None): 
        if test_input: return test_input, []
        prompt_input = [attack]
        prompt_input.append(explanation_of_attack)
        load_payloads_result = persona.payload.load_url_data(target_url)
        prompt_input.append(load_payloads_result)
        if load_payloads_result and "basic" in load_payloads_result:
            basic_data = load_payloads_result["basic"]
            if isinstance(basic_data, list):
                payloads = [request["payload"] for request in basic_data if "payload" in request]
            else:
                payloads = []
        else:
            payloads = []
        prompt_input.append(form_elements)
        return prompt_input, payloads

    def __func_clean_up(llama_response, prompt=""):
        try:
            response_json = json.loads(llama_response)
            response_json.pop("reasoning", None)
            return response_json
        except json.JSONDecodeError:
            return llama_response
  
    def __func_validate(gpt_response, prompt=""):
        try:
            response_json = json.loads(gpt_response)
            payload = response_json.get("payload")
            if not payload or any(kw in payload for kw in ["query_parameter", "VALUE"]):
                return False
            if not isinstance(payload, str):
                return False
            if payload.startswith('?'):
                payload = payload[1:]
            if not _is_url_encoded(payload):
                payload = _url_encode(payload)
            return payload not in payloads
        except json.JSONDecodeError:
            return False
        
    def get_fail_safe(): 
        return {"payload": "ERROR"}
    
    def find_form_elements(url, cookies=None):
        response = requests.get(url, cookies=cookies)
        method_match = re.search(r'<form[^>]+method=["\']?([^"\'>]+)', response.text, re.IGNORECASE)
        method = method_match.group(1).upper() if method_match else None
        form_elements = []
        inputs = re.findall(r'<input[^>]*>|<textarea[^>]*>|<select[^>]*>|<button[^>]*>', response.text, re.IGNORECASE)
        for input_tag in inputs:
            form_elements.append(input_tag.strip())

        return method, form_elements

    def _url_encode(payload):
        parts = payload.split('&')
        encoded_parts = []
        for part in parts:
            if '=' in part:
                key, value = part.split('=', 1)
                encoded_value = quote(value, safe='')
                encoded_parts.append(f"{key}={encoded_value}")
            else:
                encoded_parts.append(part)
        return '&'.join(encoded_parts)

    def _is_url_encoded(s):
        return s != unquote(s)

    method, form_elements = find_form_elements(target_url, cookies)

    gpt_param = ''
    prompt_template = "persona/prompt_template/v4/create_payload.txt"
    prompt_input, payloads = create_prompt_input(attack, test_input)
    prompt = generate_prompt(prompt_input, prompt_template)
    fail_safe = get_fail_safe()
    output = safe_generate_response_json(
        prompt,
        gpt_param,
        repeat=50,
        fail_safe_response=fail_safe,
        func_validate=__func_validate,
        func_clean_up=__func_clean_up
    )
    if output["payload"].startswith('?'):
        output["payload"] = output["payload"][1:]
    if not _is_url_encoded(output["payload"]):
        output["payload"] = _url_encode(output["payload"])
        
    return output, [output, prompt, gpt_param, prompt_input, fail_safe], method






def run_gpt_prompt_response_attack_reasoning(persona, attack, explanation_of_attack, target_url, method, create_payload, cookies=None, test_input=None):   
    def create_prompt_input(attack, test_input=None): 
        if test_input: return test_input
        prompt_input = [attack]
        prompt_input += [explanation_of_attack]
        prompt_input += [create_payload]
        prompt_input += [HTML_differences]
        return prompt_input

    def __func_clean_up(llama_response, prompt=""):
        try:
            response_json = json.loads(llama_response)
            cleaned_response = {key: response_json[key] for key in ["reasoning", "observations"] if key in response_json}
            return cleaned_response
        except json.JSONDecodeError:
            return llama_response
  
    def __func_validate(gpt_response, prompt=""):
        try:
            response_json = json.loads(gpt_response)
            return all(field in response_json for field in ["reasoning", "observations"]) and \
                response_json["observations"] in ["exploit_successful", "exploit_unsuccessful"]
        except json.JSONDecodeError:
            return False

    def get_fail_safe(): 
        return "ERROR"
    
    def compare_html_responses(response_default: requests.Response, response_add_payload: requests.Response) -> list[dict]:
        soup1 = BeautifulSoup(response_default.text, 'html.parser')
        soup2 = BeautifulSoup(response_add_payload.text, 'html.parser')
        changes = []
        def compare_elements(elem1: Tag | NavigableString | None, elem2: Tag | NavigableString | None, path: str = ""):
            if elem1 is None and elem2 is None:
                return
            if elem1 is None:
                changes.append({"type": "added", "content": str(elem2), "path": path})
                return
            if elem2 is None:
                changes.append({"type": "removed", "content": str(elem1), "path": path})
                return
            if isinstance(elem1, Tag) and isinstance(elem2, Tag):
                if elem1.name != elem2.name or elem1.attrs != elem2.attrs:
                    changes.append({"type": "modified", "original": str(elem1), "modified": str(elem2), "path": path})

                if elem2.name == "script":
                    script_content1 = elem1.get_text(strip=True) if elem1.name == "script" else ""
                    script_content2 = elem2.get_text(strip=True)
                    if script_content1 != script_content2:
                        if "<script>" in script_content2 or any(keyword in script_content2.lower() for keyword in ["alert", "eval", "document"]):
                            changes.append({"type": "added_script", "content": str(elem2), "path": path})
                dangerous_attrs = {'onload', 'onclick', 'onerror', 'onmouseover'}
                new_attrs = dangerous_attrs & set(elem2.attrs.keys()) - set(elem1.attrs.keys())
                if new_attrs:
                    for attr in new_attrs:
                        changes.append({"type": "dangerous_attribute_added", "tag": elem2.name, "attribute": attr, "value": elem2.attrs.get(attr), "path": path})
            elif isinstance(elem1, NavigableString) and isinstance(elem2, NavigableString):
                if elem1 != elem2:
                    changes.append({"type": "modified", "original": str(elem1), "modified": str(elem2), "path": path})
            children1 = list(elem1.children) if isinstance(elem1, Tag) else []
            children2 = list(elem2.children) if isinstance(elem2, Tag) else []
            for i in range(max(len(children1), len(children2))):
                child1 = children1[i] if i < len(children1) else None
                child2 = children2[i] if i < len(children2) else None
                compare_elements(child1, child2, path + f"/{elem1.name}[{i}]")
        if soup1.body and soup2.body:
            compare_elements(soup1.body, soup2.body)
        elif soup1.body is None and soup2.body:
            changes.append({"type": "added", "content": str(soup2.body), "path": "/body"})
        elif soup1.body and soup2.body is None:
            changes.append({"type": "removed", "content": str(soup1.body), "path": "/body"})
        if response_default.status_code != response_add_payload.status_code:
            changes.append({"type": "status_code_changed", "original": response_default.status_code, "modified": response_add_payload.status_code})
        if response_default.headers != response_add_payload.headers:
            header_changes = {key: (response_default.headers.get(key), response_add_payload.headers.get(key)) for key in response_add_payload.headers if response_default.headers.get(key) != response_add_payload.headers.get(key) and key.lower() != "date"}
            if header_changes:
                changes.append({"type": "headers_modified", "changes": header_changes})
        if response_default.cookies != response_add_payload.cookies:
            cookie_changes = {key: (response_default.cookies.get(key), response_add_payload.cookies.get(key)) for key in response_add_payload.cookies if response_default.cookies.get(key) != response_add_payload.cookies.get(key)}
            changes.append({"type": "cookies_modified", "changes": cookie_changes})
        pre_tag = soup2.find('pre')
        if pre_tag:
            error_message = pre_tag.text
            if "syntax" in error_message or "error" in error_message.lower():
                changes.append({"type": "error_message", "content": error_message, "path": "/error"})
        if not changes:
            changes.append({"type": "no_change", "message": "No changes detected between the default and modified responses."})

        return changes

    headers = {
    'Referer': target_url,
    'Content-Type': 'application/json'
    }
    
    if method.lower() == 'get':
        response_default = requests.get(
            url=target_url,
            headers=headers,
            cookies=cookies,
            # allow_redirects=True,
        )
        response_add_payload = requests.get(
            url=f"{target_url}?{create_payload}",
            headers=headers,
            cookies=cookies,
            # allow_redirects=True,
        )
    elif method.lower() == 'post':
        response_default = requests.post(
            url=target_url,
            headers=headers,
            cookies=cookies,
        )
        response_add_payload = requests.post(
            url=target_url,
            headers=headers,
            cookies=cookies,
            data=create_payload
        )
    else:  # PUT method
        response_default = requests.put(
            url=target_url,
            headers=headers,
            cookies=cookies,
        )
        response_add_payload = requests.put(
            url=target_url,
            headers=headers,
            cookies=cookies,
            data=create_payload
        )
    HTML_differences = compare_html_responses(response_default, response_add_payload)

    gpt_param = ''
    prompt_template = "persona/prompt_template/v4/response_attack_reasoning.txt"
    prompt_input = create_prompt_input(attack, test_input)
    prompt = generate_prompt(prompt_input, prompt_template)
    fail_safe = get_fail_safe()

    if not any(change.get("type") == "no_change" for change in HTML_differences):
        output = safe_generate_response_json(
            prompt,
            gpt_param,
            repeat=5,
            fail_safe_response=fail_safe,
            func_validate=__func_validate,
            func_clean_up=__func_clean_up
        )
    else:
        output = {"reasoning": "No significant changes detected, attack unsuccessful.", "observations": "exploit_unsuccessful"}
    return output, [output, prompt, gpt_param, prompt_input, fail_safe], HTML_differences




def run_gpt_prompt_generate_next_step(persona, attack, explanation_of_attack, target_url, create_payload, HTML_differences, reasoning, observations, test_input=None):   
    def create_prompt_input(attack, test_input=None): 
        if test_input: return test_input
        prompt_input = [attack]
        prompt_input += [explanation_of_attack]
        load_payloads_result = persona.payload.load_url_data(target_url)
        prompt_input += [load_payloads_result]
        prompt_input += [create_payload]
        prompt_input += [HTML_differences]
        prompt_input += [reasoning]
        prompt_input += [observations]
        return prompt_input

    def __func_clean_up(llama_response, prompt=""):
        try:
            response_json = json.loads(llama_response)
            return {"next_step": response_json["next_step"].strip()} if "next_step" in response_json else llama_response
        except json.JSONDecodeError:
            return llama_response
  
    def __func_validate(gpt_response, prompt=""):
        try:
            if not gpt_response:
                return False
            response_json = json.loads(gpt_response)
            has_next_step = "next_step" in response_json
            is_next_step_str = isinstance(response_json["next_step"], str)
            return has_next_step and is_next_step_str
        except json.JSONDecodeError:
            return False

    def get_fail_safe(): 
        return "ERROR"

    gpt_param = ''
    prompt_template = "persona/prompt_template/v4/generate_next_step.txt"
    prompt_input = create_prompt_input(attack, test_input)
    prompt = generate_prompt(prompt_input, prompt_template)
    fail_safe = get_fail_safe()
    output = safe_generate_response_json(
        prompt,
        gpt_param,
        repeat=5,
        fail_safe_response=fail_safe,
        func_validate=__func_validate,
        func_clean_up=__func_clean_up
    )
        
    return output, [output, prompt, gpt_param, prompt_input, fail_safe]


