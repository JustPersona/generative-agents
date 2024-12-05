"""
Author: Joon Sung Park (joonspk@stanford.edu)

File: global_methods.py
Description: Contains functions used throughout my projects.
"""
import random
import string
import csv
import time
import datetime as dt
import pathlib
import os
import sys
import numpy
import math
import shutil, errno
import re
import requests
import hashlib
import json
import socket
import ipaddress

from os import listdir

def create_folder_if_not_there(curr_path): 
  """
  Checks if a folder in the curr_path exists. If it does not exist, creates
  the folder. 
  Note that if the curr_path designates a file location, it will operate on 
  the folder that contains the file. But the function also works even if the 
  path designates to just a folder. 
  Args:
    curr_list: list to write. The list comes in the following form:
               [['key1', 'val1-1', 'val1-2'...],
                ['key2', 'val2-1', 'val2-2'...],]
    outfile: name of the csv file to write    
  RETURNS: 
    True: if a new folder is created
    False: if a new folder is not created
  """
  outfolder_name = curr_path.split("/")
  if len(outfolder_name) != 1: 
    # This checks if the curr path is a file or a folder. 
    if "." in outfolder_name[-1]: 
      outfolder_name = outfolder_name[:-1]

    outfolder_name = "/".join(outfolder_name)
    if not os.path.exists(outfolder_name):
      os.makedirs(outfolder_name)
      return True

  return False 


def write_list_of_list_to_csv(curr_list_of_list, outfile):
  """
  Writes a list of list to csv. 
  Unlike write_list_to_csv_line, it writes the entire csv in one shot. 
  ARGS:
    curr_list_of_list: list to write. The list comes in the following form:
               [['key1', 'val1-1', 'val1-2'...],
                ['key2', 'val2-1', 'val2-2'...],]
    outfile: name of the csv file to write    
  RETURNS: 
    None
  """
  create_folder_if_not_there(outfile)
  with open(outfile, "w") as f:
    writer = csv.writer(f)
    writer.writerows(curr_list_of_list)


def write_list_to_csv_line(line_list, outfile): 
  """
  Writes one line to a csv file.
  Unlike write_list_of_list_to_csv, this opens an existing outfile and then 
  appends a line to that file. 
  This also works if the file does not exist already. 
  ARGS:
    curr_list: list to write. The list comes in the following form:
               ['key1', 'val1-1', 'val1-2'...]
               Importantly, this is NOT a list of list. 
    outfile: name of the csv file to write   
  RETURNS: 
    None
  """
  create_folder_if_not_there(outfile)

  # Opening the file first so we can write incrementally as we progress
  curr_file = open(outfile, 'a',)
  csvfile_1 = csv.writer(curr_file)
  csvfile_1.writerow(line_list)
  curr_file.close()


def read_file_to_list(curr_file, header=False, strip_trail=True): 
  """
  Reads in a csv file to a list of list. If header is True, it returns a 
  tuple with (header row, all rows)
  ARGS:
    curr_file: path to the current csv file. 
  RETURNS: 
    List of list where the component lists are the rows of the file. 
  """
  if not header: 
    analysis_list = []
    with open(curr_file) as f_analysis_file: 
      data_reader = csv.reader(f_analysis_file, delimiter=",")
      for count, row in enumerate(data_reader): 
        if strip_trail: 
          row = [i.strip() for i in row]
        analysis_list += [row]
    return analysis_list
  else: 
    analysis_list = []
    with open(curr_file) as f_analysis_file: 
      data_reader = csv.reader(f_analysis_file, delimiter=",")
      for count, row in enumerate(data_reader): 
        if strip_trail: 
          row = [i.strip() for i in row]
        analysis_list += [row]
    return analysis_list[0], analysis_list[1:]


def read_file_to_set(curr_file, col=0): 
  """
  Reads in a "single column" of a csv file to a set. 
  ARGS:
    curr_file: path to the current csv file. 
  RETURNS: 
    Set with all items in a single column of a csv file. 
  """
  analysis_set = set()
  with open(curr_file) as f_analysis_file: 
    data_reader = csv.reader(f_analysis_file, delimiter=",")
    for count, row in enumerate(data_reader): 
      analysis_set.add(row[col])
  return analysis_set


def get_row_len(curr_file): 
  """
  Get the number of rows in a csv file 
  ARGS:
    curr_file: path to the current csv file. 
  RETURNS: 
    The number of rows
    False if the file does not exist
  """
  try: 
    analysis_set = set()
    with open(curr_file) as f_analysis_file: 
      data_reader = csv.reader(f_analysis_file, delimiter=",")
      for count, row in enumerate(data_reader): 
        analysis_set.add(row[0])
    return len(analysis_set)
  except: 
    return False


def check_if_file_exists(curr_file): 
  """
  Checks if a file exists
  ARGS:
    curr_file: path to the current csv file. 
  RETURNS: 
    True if the file exists
    False if the file does not exist
  """
  try: 
    with open(curr_file) as f_analysis_file: pass
    return True
  except: 
    return False


def find_filenames(path_to_dir, suffix=".csv"):
  """
  Given a directory, find all files that ends with the provided suffix and 
  returns their paths.  
  ARGS:
    path_to_dir: Path to the current directory 
    suffix: The target suffix.
  RETURNS: 
    A list of paths to all files in the directory. 
  """
  filenames = listdir(path_to_dir)
  return [ path_to_dir+"/"+filename 
           for filename in filenames if filename.endswith( suffix ) ]


def average(list_of_val): 
  """
  Finds the average of the numbers in a list.
  ARGS:
    list_of_val: a list of numeric values  
  RETURNS: 
    The average of the values
  """
  return sum(list_of_val)/float(len(list_of_val))


def std(list_of_val): 
  """
  Finds the std of the numbers in a list.
  ARGS:
    list_of_val: a list of numeric values  
  RETURNS: 
    The std of the values
  """
  std = numpy.std(list_of_val)
  return std


def copyanything(src, dst):
  """
  Copy over everything in the src folder to dst folder. 
  ARGS:
    src: address of the source folder  
    dst: address of the destination folder  
  RETURNS: 
    None
  """
  try:
    shutil.copytree(src, dst)
  except OSError as exc: # python >2.5
    if exc.errno in (errno.ENOTDIR, errno.EINVAL):
      shutil.copy(src, dst)
    else: raise



def target_validation(target_url):
    """
    Verify URL is an internal network

    ARGS:
        target_url: URL to check
    RETURNS:
        True: if target_url is internal network
        False: if target_url is external network
    """
    hostname = target_url.split("://")[1].split("/")[0].split(":")[0]
    return ipaddress.ip_address(socket.gethostbyname(hostname)).is_private

def is_dvwa(target_url):
    """
    Verify that it is DVWA Login Page

    ARGS:
        target_url: URL to check
    RETURNS:
        True: if target_url is DVWA Login Page
        False: if target_url is not DVWA Login Page
    """
    return "<title>Login :: Damn Vulnerable Web Application (DVWA)</title>" in requests.get(target_url).text

def login_to_dvwa(dvwa_url, username="admin", password="password", security="low"):
    session = requests.Session()
    response = session.get(dvwa_url)
    token_match = re.search(r'<input type=\'hidden\' name=\'user_token\' value=\'([^\']+)\'', response.text)
    if token_match:
        user_token = token_match.group(1)
    params = {
        'username': username,
        'password': password,
        'Login': 'Login',
        'user_token': user_token
    }
    login_response = session.post(dvwa_url, data=params)
    cookies = session.cookies.get_dict()
    cookies['security'] = security
    # print("cookies :", cookies)
    return cookies


def get_payloads(personas, target_personas, payload_loader):
    """
    특정 페르소나 그룹의 데이터를 로드하고 해시화

    input :
    personas (dict) : 모든 페르소나 정보
    target_personas (list) : 데이터를 로드할 대상 그룹
    payload_loader (str) : 데이터를 로드할 메서드 이름 ("load_successful_data", "load_patch_data").

    output :
    로드한 데이터, 해당 데이터의 해시값
    """
    def hash_data(data):
        return hashlib.sha256(json.dumps(data, sort_keys=True).encode()).hexdigest()

    payload_datas = [] if payload_loader == "load_patch_data" else {}
    patch_id = 1

    for persona_name in target_personas:
        persona_payload = personas.get(persona_name).payload
        if not persona_payload:
            continue

        load_method = getattr(persona_payload, payload_loader, None)
        if not callable(load_method):
            continue

        loaded_data = load_method()

        if payload_loader == "load_patch_data" and isinstance(loaded_data, list):
            for patch in loaded_data:
                patch["patch_id"] = patch_id
                payload_datas.append(patch)
                patch_id += 1
        elif payload_loader == "load_successful_data" and isinstance(loaded_data, dict):
            for key, value in loaded_data.items():
                payload_datas.setdefault(key, []).extend(value)

    return payload_datas, hash_data(payload_datas) if payload_datas else ([], None if payload_loader == "load_patch_data" else {}, None)



if __name__ == '__main__':
  pass
