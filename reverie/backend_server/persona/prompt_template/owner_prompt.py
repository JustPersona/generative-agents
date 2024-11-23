
import sys
import json

sys.path.append('../../')

from global_methods import *
from persona.prompt_template.gpt_structure import *
from persona.prompt_template.print_prompt import *



def run_gpt_prompt_select_best_patch(persona, patch_datas, test_input=None):
    def create_prompt_input(patch_datas, test_input=None): 
        if test_input: return test_input
        prompt_input = [patch_datas]
        return prompt_input
    
    def __func_clean_up(llama_response, prompt=""):
        try:
            response_json = json.loads(llama_response)
            best_patch = response_json.get("best_patch", {})
            best_patch["patch_id"] = int(best_patch["patch_id"])
            return best_patch
        except json.JSONDecodeError:
            return llama_response

    def __func_validate(gpt_response, prompt=""):
        try:
            response = json.loads(gpt_response).get("best_patch", {})
            patch_id = int(response.get("patch_id", -1))
            reason = response.get("reason")
            valid_patch_ids = [patch["patch_id"] for patch in patch_datas] + [0]
            return isinstance(reason, str) and patch_id in valid_patch_ids
        except (json.JSONDecodeError, ValueError):
            return False

    def get_fail_safe(): 
        return "ERROR"
    
    gpt_param = ''
    prompt_template = "persona/prompt_template/v4/select_best_patch.txt"
    # prompt_template = "C:/Users/siro/Desktop/evaluating_generative_agents-main/reverie/backend_server/persona/prompt_template/v4/select_best_patch.txt"

    prompt_input = create_prompt_input(patch_datas, test_input)
    prompt = generate_prompt(prompt_input, prompt_template)
    fail_safe = get_fail_safe()
    output = safe_generate_response_json(prompt, gpt_param, 5, fail_safe,
                                    __func_validate, __func_clean_up)
        
    return output, [output, prompt, gpt_param, prompt_input, fail_safe]
