
import sys
import json

sys.path.append('../../')

from global_methods import *
from persona.prompt_template.gpt_structure import *
from persona.prompt_template.print_prompt import *

from utils import *



def run_gpt_prompt_identify_vulnerable_files(persona, successful_data, test_input=None):
    def create_prompt_input(directory_files, successful_data, test_input=None): 
        if test_input: return test_input
        prompt_input = [directory_files]
        prompt_input += [successful_data]
        return prompt_input
    
    def __func_clean_up(llama_response, prompt=""):
        try:
            response_json = json.loads(llama_response)
            for file_info in response_json.get("vulnerable_files", []):
                file_info["file_path"] = file_info.get("file_path", "").strip().lstrip("/")
                file_info["reason"] = file_info.get("reason", "").strip()
            return response_json
        except json.JSONDecodeError:
            return llama_response

    def __func_validate(gpt_response, prompt=""):
        try:
            response_json = json.loads(gpt_response)
            if "vulnerable_files" not in response_json:
                return False
            for file_info in response_json.get("vulnerable_files", []):
                if "file_path" not in file_info or "reason" not in file_info:
                    return False
                file_path = file_info["file_path"].lstrip("/")
                if file_path not in directory_files:
                    return False
            return True
        except json.JSONDecodeError:
            return False

    def get_fail_safe(): 
        return "ERROR"
    
    def generate_file_paths_list(server_path):
      file_paths = []
      for root, dirs, files in os.walk(server_path):
          for file in files:
              full_path = os.path.join(root, file)
              relative_path = os.path.relpath(full_path, server_path)
              file_paths.append(relative_path.replace("\\", "/"))

      return file_paths

    directory_files = generate_file_paths_list(server_path)
    print("서버 파일 경로 목록 :", directory_files)
    vulnerability_url = list(successful_data.keys())[0]
    print("취약한 URL :", vulnerability_url)

    gpt_param = ''
    prompt_template = "persona/prompt_template/v4/identify_vulnerable_files.txt"
    # prompt_template = "C:/Users/siro/Desktop/evaluating_generative_agents-main/reverie/backend_server/persona/prompt_template/v4/identify_vulnerable_files.txt"

    # prompt_input = create_prompt_input(directory_files, successful_data, test_input)
    prompt_input = create_prompt_input(directory_files, vulnerability_url, test_input)
    prompt = generate_prompt(prompt_input, prompt_template)
    fail_safe = get_fail_safe()
    output = safe_generate_response_json(prompt, gpt_param, 5, fail_safe,
                                    __func_validate, __func_clean_up)
        
    return output, [output, prompt, gpt_param, prompt_input, fail_safe]





def run_gpt_patch_instructions(persona, successful_data, vulnerable_file, test_input=None):
    def create_prompt_input(successful_data, vulnerable_file_code, test_input=None): 
        if test_input: return test_input
        prompt_input = [successful_data]
        prompt_input += [vulnerable_file_code]
        return prompt_input
    
    def __func_clean_up(llama_response, prompt=""):
        try:
            response_json = json.loads(llama_response)
            return response_json
        except json.JSONDecodeError:
            return llama_response

    def __func_validate(gpt_response, prompt=""):
        try:
            response_json = json.loads(gpt_response)
            return True
        except json.JSONDecodeError:
            return False

    def get_fail_safe(): 
        return "ERROR"
    
    def get_vulnerable_file_code(vulnerable_file):
        file_path = vulnerable_file.get("file_path")
        absolute_path = os.path.join(server_path, file_path)
        file_entry = {"file_path": file_path}

        try:
            with open(absolute_path, "r", encoding="utf-8") as file:
                file_content = file.read()
                file_entry["code"] = file_content
        except FileNotFoundError:
            file_entry["code"] = "File not found."
        except Exception as e:
            file_entry["code"] = f"Error reading file: {e}"

        return file_entry

    vulnerable_file_code = get_vulnerable_file_code(vulnerable_file)
    print("취약한 파일 코드:", vulnerable_file_code)

    gpt_param = ''
    prompt_template = "persona/prompt_template/v4/patch_vulnerabilities.txt"
    # prompt_template = "C:/Users/siro/Desktop/evaluating_generative_agents-main/reverie/backend_server/persona/prompt_template/v4/patch_vulnerabilities.txt"

    prompt_input = create_prompt_input(successful_data, vulnerable_file_code, test_input)
    prompt = generate_prompt(prompt_input, prompt_template)
    fail_safe = get_fail_safe()
    output = safe_generate_response_json(prompt, gpt_param, 5, fail_safe,
                                    __func_validate, __func_clean_up)
        
    return output, [output, prompt, gpt_param, prompt_input, fail_safe], vulnerable_file_code
