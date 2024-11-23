"""
Author: Joon Sung Park (joonspk@stanford.edu)

File: gpt_structure.py
Description: Wrapper functions for calling OpenAI APIs.
"""
import json
import random
import time 
import ollama

from utils import *
from langchain_ollama import OllamaLLM
from langchain_community.embeddings import GPT4AllEmbeddings
from langchain.callbacks.manager import CallbackManager
from langchain.callbacks.streaming_stdout_final_only import FinalStreamingStdOutCallbackHandler as CallbackHandler

# ============================================================================
# ################### [Set LLM] ###################
# ============================================================================

### *** Ollama ***
llm = OllamaLLM(
    base_url=ollama_url,
    model=ollama_model,
    callback_manager=CallbackManager([CallbackHandler()])
)

def temp_sleep(seconds=0.1):
  time.sleep(seconds)

def ChatGPT_single_request(prompt): 
  temp_sleep()
  try:
    response = llm(prompt)
  except ValueError:
    print("Requested tokens exceed context window")
    ### TODO: Add map-reduce or splitter to handle this error.
    return "LLM ERROR"
  return response

# ============================================================================
# #####################[SECTION 1: CHATGPT-3 STRUCTURE] ######################
# ============================================================================

def ChatGPT_request(prompt,parameters): 
  """
  Given a prompt, make a request to LLM server and returns the response. 
  ARGS:
    prompt: a str prompt 
    parameters: optional
  RETURNS: 
    a str of LLM's response. 
  """
  # temp_sleep()
  try:
    response = llm(prompt)
  except ValueError:
    print("Requested tokens exceed context window")
    ### TODO: Add map-reduce or splitter to handle this error.
    return "LLM ERROR"
  return response

def ChatGPT_safe_generate_response(prompt, 
                                   example_output,
                                   special_instruction,
                                   repeat=3,
                                   fail_safe_response="error",
                                   func_validate=None,
                                   func_clean_up=None,
                                   verbose=False): 
  # prompt = 'GPT-3 Prompt:\n"""\n' + prompt + '\n"""\n'
  prompt = '"""\n' + prompt + '\n"""\n'
  prompt += f"Output the response to the prompt above in json. {special_instruction}\n"
  prompt += "Example output json:\n"
  prompt += '{"output": "' + str(example_output) + '"}'

  if verbose: 
    print ("LLM PROMPT")
    print (prompt)

  for i in range(repeat): 

    try: 
      curr_gpt_response = ChatGPT_request(prompt).strip()
      end_index = curr_gpt_response.rfind('}') + 1
      curr_gpt_response = curr_gpt_response[:end_index]
      curr_gpt_response = json.loads(curr_gpt_response)["output"]

      # print ("---ashdfaf")
      # print (curr_gpt_response)
      # print ("000asdfhia")
      
      if func_validate(curr_gpt_response, prompt=prompt): 
        return func_clean_up(curr_gpt_response, prompt=prompt)
      
      if verbose: 
        print ("---- repeat count: \n", i, curr_gpt_response)
        print (curr_gpt_response)
        print ("~~~~")

    except: 
      pass

  return False


def ChatGPT_safe_generate_response_OLD(prompt, 
                                   repeat=3,
                                   fail_safe_response="error",
                                   func_validate=None,
                                   func_clean_up=None,
                                   verbose=False): 
  if verbose: 
    print ("CHAT GPT PROMPT")
    print (prompt)

  for i in range(repeat): 
    try: 
      curr_gpt_response = ChatGPT_request(prompt).strip()
      if func_validate(curr_gpt_response, prompt=prompt): 
        return func_clean_up(curr_gpt_response, prompt=prompt)
      if verbose: 
        print (f"---- repeat count: {i}")
        print (curr_gpt_response)
        print ("~~~~")

    except: 
      pass
  print ("FAIL SAFE TRIGGERED") 
  return fail_safe_response


# ============================================================================
# ###################[SECTION 2: ORIGINAL GPT-3 STRUCTURE] ###################
# ============================================================================

def GPT_request(prompt,parameters): 
  """
  Given a prompt, make a request to LLM server and returns the response. 
  ARGS:
    prompt: a str prompt 
    parameters: optional 
  RETURNS: 
    a str of LLM's response. 
  """
  # temp_sleep()
  try:
    response = llm(prompt)
  except ValueError:
    print("Requested tokens exceed context window")
    ### TODO: Add map-reduce or splitter to handle this error.
    return "LLM ERROR"
  return response

def generate_prompt(curr_input, prompt_lib_file): 
  """
  Takes in the current input (e.g. comment that you want to classifiy) and 
  the path to a prompt file. The prompt file contains the raw str prompt that
  will be used, which contains the following substr: !<INPUT>! -- this 
  function replaces this substr with the actual curr_input to produce the 
  final promopt that will be sent to the GPT3 server. 
  ARGS:
    curr_input: the input we want to feed in (IF THERE ARE MORE THAN ONE
                INPUT, THIS CAN BE A LIST.)
    prompt_lib_file: the path to the promopt file. 
  RETURNS: 
    a str prompt that will be sent to OpenAI's GPT server.  
  """
  if type(curr_input) == type("string"): 
    curr_input = [curr_input]
  curr_input = [str(i) for i in curr_input]

  f = open(prompt_lib_file, "r", encoding="utf-8")
  prompt = f.read()
  f.close()
  for count, i in enumerate(curr_input):   
    prompt = prompt.replace(f"!<INPUT {count}>!", i)
  if "<commentblockmarker>###</commentblockmarker>" in prompt: 
    prompt = prompt.split("<commentblockmarker>###</commentblockmarker>")[1]
  return prompt.strip()


def safe_generate_response(prompt, 
                           gpt_parameter,
                           repeat=5,
                           fail_safe_response="error",
                           func_validate=None,
                           func_clean_up=None,
                           verbose=False): 
  if verbose: 
    print (prompt)

  for i in range(repeat): 
    curr_gpt_response = GPT_request(prompt, gpt_parameter)
    if func_validate(curr_gpt_response, prompt=prompt): 
      return func_clean_up(curr_gpt_response, prompt=prompt)
    else:
      print('==== ERROR IN RESPONSE ====')
      print(curr_gpt_response)
      print('~~~~')
    if verbose: 
      print ("---- repeat count: ", i, curr_gpt_response)
      print (curr_gpt_response)
      print ("~~~~")
  print("==== USING FAILSAFE ====")
  return fail_safe_response


def safe_generate_response_json(prompt, 
                                gpt_parameter,
                                repeat=5,
                                fail_safe_response="error",
                                func_validate=None,
                                func_clean_up=None,
                                verbose=False): 
    if verbose: 
        print(prompt)

    try:
        for i in range(repeat):
            llm.format = "json"
            curr_gpt_response = GPT_request(prompt, gpt_parameter)
            print('생성한 응답 :',curr_gpt_response)
            if func_validate(curr_gpt_response, prompt=prompt): 
                return func_clean_up(curr_gpt_response, prompt=prompt)
            if verbose: 
                print('==== ERROR IN RESPONSE ==== \n', curr_gpt_response)
            
        print("==== USING FAILSAFE ====")
        return fail_safe_response

    finally:
        llm.format = ""


def get_embedding(text, model=None):
 # Use GPT4All local embeddings 
 # https://python.langchain.com/docs/integrations/text_embedding/gpt4all
 text = text.replace("\n", " ")
 if not text: 
  text = "this is blank"
 gpt4all_embd = GPT4AllEmbeddings()
 return gpt4all_embd.embed_query(text)


# https://ollama.com/blog/embedding-models
# Model                   Parameter Size
# mxbai-embed-large       334M   (1.2 GB)
# nomic-embed-text       137M   (849 MB)
# all-minilm           23M

# def get_embedding(text, model="mxbai-embed-large"):
#     text = text.replace("\n", " ")
#     if not text:
#         text = "this is blank"
#     if model not in [m['model'].split(':')[0] for m in ollama.list().get('models', [])]:
#         ollama.pull(model)
#     response = ollama.embeddings(model=model, prompt=text)
#     return response['embedding']



if __name__ == '__main__':
  gpt_parameter = {"engine": "text-davinci-003", "max_tokens": 50, 
                   "temperature": 0, "top_p": 1, "stream": False,
                   "frequency_penalty": 0, "presence_penalty": 0, 
                   "stop": ['"']}
  curr_input = ["driving to a friend's house"]
  prompt_lib_file = "prompt_template/test_prompt_July5.txt"
  prompt = generate_prompt(curr_input, prompt_lib_file)

  def __func_validate(gpt_response): 
    if len(gpt_response.strip()) <= 1:
      return False
    if len(gpt_response.strip().split(" ")) > 1: 
      return False
    return True
  def __func_clean_up(gpt_response):
    cleaned_response = gpt_response.strip()
    return cleaned_response

  output = safe_generate_response(prompt, 
                                 gpt_parameter,
                                 5,
                                 "rest",
                                 __func_validate,
                                 __func_clean_up,
                                 True)

  print (output)




















