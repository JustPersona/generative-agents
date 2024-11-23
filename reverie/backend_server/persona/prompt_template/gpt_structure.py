"""
Author: Joon Sung Park (joonspk@stanford.edu)

File: gpt_structure.py
Description: Wrapper functions for calling OpenAI APIs.
"""
import json
import random
import openai
import time 
import requests

from utils import *

# openai.api_key = openai_api_key

def temp_sleep(seconds=0.1):
  time.sleep(seconds)

def ChatGPT_single_request(prompt): 
  temp_sleep()

  completion = openai.ChatCompletion.create(
    model="gpt-3.5-turbo", 
    messages=[{"role": "user", "content": prompt}]
  )
  return completion["choices"][0]["message"]["content"]


# ============================================================================
# #####################[SECTION 1: CHATGPT-3 STRUCTURE] ######################
# ============================================================================

def GPT4_request(prompt): 
  """
  Given a prompt and a dictionary of GPT parameters, make a request to OpenAI
  server and returns the response. 
  ARGS:
    prompt: a str prompt
    gpt_parameter: a python dictionary with the keys indicating the names of  
                   the parameter and the values indicating the parameter 
                   values.   
  RETURNS: 
    a str of GPT-3's response. 
  """
  temp_sleep()

  try: 
    completion = openai.ChatCompletion.create(
    model="gpt-4", 
    messages=[{"role": "user", "content": prompt}]
    )
    return completion["choices"][0]["message"]["content"]
  
  except: 
    print ("ChatGPT ERROR")
    return "ChatGPT ERROR"


def ChatGPT_request(prompt): 
  """
  Given a prompt and a dictionary of GPT parameters, make a request to OpenAI
  server and returns the response. 
  ARGS:
    prompt: a str prompt
    gpt_parameter: a python dictionary with the keys indicating the names of  
                   the parameter and the values indicating the parameter 
                   values.   
  RETURNS: 
    a str of GPT-3's response. 
  """
  # temp_sleep()
  try: 
    completion = openai.ChatCompletion.create(
    model="gpt-3.5-turbo", 
    messages=[{"role": "user", "content": prompt}]
    )
    return completion["choices"][0]["message"]["content"]
  
  except: 
    print ("ChatGPT ERROR")
    return "ChatGPT ERROR"


def GPT4_safe_generate_response(prompt, 
                                   example_output,
                                   special_instruction,
                                   repeat=3,
                                   fail_safe_response="error",
                                   func_validate=None,
                                   func_clean_up=None,
                                   verbose=False): 
  prompt = 'GPT-3 Prompt:\n"""\n' + prompt + '\n"""\n'
  prompt += f"Output the response to the prompt above in json. {special_instruction}\n"
  prompt += "Example output json:\n"
  prompt += '{"output": "' + str(example_output) + '"}'

  if verbose: 
    print ("CHAT GPT PROMPT")
    print (prompt)

  for i in range(repeat): 

    try: 
      curr_gpt_response = GPT4_request(prompt).strip()
      end_index = curr_gpt_response.rfind('}') + 1
      curr_gpt_response = curr_gpt_response[:end_index]
      curr_gpt_response = json.loads(curr_gpt_response)["output"]
      
      if func_validate(curr_gpt_response, prompt=prompt): 
        return func_clean_up(curr_gpt_response, prompt=prompt)
      
      if verbose: 
        print ("---- repeat count: \n", i, curr_gpt_response)
        print (curr_gpt_response)
        print ("~~~~")

    except: 
      pass

  return False


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
    print ("CHAT GPT PROMPT")
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

#def GPT_request(prompt, gpt_parameter): 
#  """
#  Given a prompt and a dictionary of GPT parameters, make a request to OpenAI
#  server and returns the response. 
#  ARGS:
#    prompt: a str prompt
#    gpt_parameter: a python dictionary with the keys indicating the names of  
#                   the parameter and the values indicating the parameter 
#                   values.   
#  RETURNS: 
#    a str of GPT-3's response. 
#  """
#  temp_sleep()
#  try: 
#    response = openai.Completion.create(
#                model=gpt_parameter["engine"],
#                prompt=prompt,
#                temperature=gpt_parameter["temperature"],
#                max_tokens=gpt_parameter["max_tokens"],
#                top_p=gpt_parameter["top_p"],
#                frequency_penalty=gpt_parameter["frequency_penalty"],
#                presence_penalty=gpt_parameter["presence_penalty"],
#                stream=gpt_parameter["stream"],
#                stop=gpt_parameter["stop"],)
#    return response.choices[0].text
#  except: 
#    print ("TOKEN LIMIT EXCEEDED")
#    return "TOKEN LIMIT EXCEEDED"

# ============================================================================
llama_api_url = llama_api + "/api/chat/"
def GPT_request(prompt, llama_parameter, suffix=None,
                  tools=None, format='json', options=None, 
                  stream=False, keep_alive='5m'):
    """
    Ollama API에 요청을 보냄
        Parameters: https://github.com/ollama/ollama/blob/main/docs/api.md
        - model: 모델 이름
        - messages: 채팅의 메시지, 채팅 기억
            role: 메시지의 역할로, system, user, assistant, 또는 tool
            content: 메시지의 내용입니다.
            images (선택): 메시지에 포함할 이미지 목록입니다 (llava와 같은 다중 모달 모델용).
            tool_calls (선택): 모델이 사용하고자 하는 도구의 목록입니다.
        - tools: 모델이 사용할 수 있는 도구 (지원되는 경우, stream = false만)

        - format: 응답 형식. json만 가능.
        - options: Modelfile 문서에 나열된 추가 모델 매개변수, 예: 온도입니다.
        - stream: false인 경우 응답이 개별 객체의 스트림이 아닌 단일 응답 객체로 반환됩니다.
        - keep_alive: 요청 후 모델이 메모리에 얼마나 오랫동안 로드된 상태로 유지될지를 제어합니다 (기본값: 5분).
    """
    temp_sleep()

    # 요청 데이터 설정
    data = {
        "model": llama_model,  # 모델 이름
        "messages": [
           {"role": "system", "content": "Output the response to the prompt above in json. output json: {\"result\": the answer to a question. }"},
           {"role": "user", "content": prompt},  # 프롬프트
           {"role": "user", "content": "Output the response to the prompt above in json. output json: {\"result\": the answer to a question. }"}
        ],
        "suffix": suffix,                     # 응답 후 추가 텍스트 (선택 사항)
        "tools": tools,                       # 모델이 사용할 수 있는 도구 (선택 사항)
        "format": format,                     # 응답 형식 (json)
        "options": {                          # 추가 모델 파라미터
            "num_predict": llama_parameter["max_tokens"],  # 최대 토큰 수
            "mirostat": llama_parameter["temperature"],     # 온도
            "top_p": llama_parameter["top_p"]               # top_p
            # "stop": llama_parameter["stop"]               # 선택 사항
        },
        "stream": stream,                     # 스트리밍 여부
        "keep_alive": keep_alive              # 유지 시간
    }
    # None 값 제거
    data = {k: v for k, v in data.items() if v is not None}

    try: 
        response = requests.post(
            llama_api_url,  # Ollama API 엔드포인트
            json=data
        )
        response.raise_for_status()  # HTTP 오류가 발생하면 예외를 발생시킴
        json_response = response.json()  # == json.loads(response.content.decode('utf-8'))
        # print(json_response)
        content = json_response['message']['content'].strip()
        result_json = json.loads(content)
        return result_json['result']  # "result" 키의 값만 반환
    except requests.exceptions.RequestException as e:
        print(f"API 요청 에러: {e}")
    except json.JSONDecodeError as e:
        print(f"JSON 파싱 에러: {e}")
    except KeyError as e:
        print(f"예상치 못한 응답 형식: {e}")
    return "ERROR"
# ============================================================================


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

  f = open(prompt_lib_file, "r")
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
    if verbose: 
      print ("---- repeat count: ", i, curr_gpt_response)
      print (curr_gpt_response)
      print ("~~~~")
  return fail_safe_response

#def get_embedding(text, model="text-embedding-ada-002"):
#  text = text.replace("\n", " ")
#  if not text: 
#    text = "this is blank"
#  return openai.Embedding.create(
#          input=[text], model=model)['data'][0]['embedding']

# https://ollama.com/blog/embedding-models
# Model                   Parameter Size
# mxbai-embed-large       334M   (1.2 GB)
# nomic-embed-text       137M   (849 MB)
# all-minilm           23M
def get_embedding(text, model="mxbai-embed-large"):
    text = text.replace("\n", " ")
    if not text:
        text = "this is blank"
    if model not in [m['model'].split(':')[0] for m in ollama.list().get('models', [])]:
        ollama.pull(model)
    response = ollama.embeddings(model=model, prompt=text)
    return response['embedding']


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
