import sys
sys.path.append('../../')

import json
import datetime
import os

from global_methods import *



class Payload:
    def __init__(self, f_saved=''):
        self.file_path = f_saved
        self.data = {}
        if check_if_file_exists(self.file_path):
            with open(self.file_path, 'r') as file:
                self.data = json.load(file)

    def save(self, out_json): 
        pass

    def load_url_data(self, url):
        if url in self.data:
            return self.data[url]
        else:
            print(f"{url} not found in the data.")
            return {}
        
    # def get_successful_payload_data(self):
    #     successful_data = []
    #     for url, payload_info in self.data.items():
    #         basic_data = payload_info.get("basic", [])
    #         for entry in basic_data:
    #             if entry.get("observations") == "exploit_successful":
    #                 successful_data.append({"url": url, "data": entry})
    #     return successful_data
        

    def save_attack_data(self, url, data, timestamp, key_type="basic"):
        if url not in self.data:
            self.data[url] = {}

        if key_type not in self.data[url]:
            self.data[url][key_type] = []

        if isinstance(data, dict):
            last_step = (
                self.data[url][key_type][-1].get("step", 0) if self.data[url][key_type] else 0
            )
            step_number = last_step + 1
            step_data = {"step": step_number}
            step_data.update(data)
            step_data["timestamp"] = timestamp

            self.data[url][key_type].append(step_data)
        else:
            if data not in self.data[url][key_type]:
                self.data[url][key_type].append(data)

        try:
            with open(self.file_path, "w") as outfile:
                json.dump(self.data, outfile, indent=2)
            return True
        except IOError as e:
            print(f"File I/O error: {e}")
            return False
        except Exception as e:
            print(f"Unexpected error during file save: {e}")
            return False
        

    def save_patch_data():
        pass
