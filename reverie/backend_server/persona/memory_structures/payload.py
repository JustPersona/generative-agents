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

    def load(self):
        return self.data
    
    
    def load_url_data(self, url):
        if url in self.data:
            return self.data[url]
        else:
            print(f"{url} not found in the data.")
            return {}
        
    def load_successful_data(self):
        successful_data = {}
        for url, details in self.data.items():
            if "basic" in details:
                successful_records = []
                for record in details["basic"]:
                    if record.get("observations") == "exploit_successful":
                        filtered_record = {key: value for key, value in record.items() if key not in {"step", "reasoning", "observations", "next_step"}}
                        successful_records.append(filtered_record)
                if successful_records:
                    if url not in successful_data:
                        successful_data[url] = []
                    successful_data[url].extend(successful_records)
        return successful_data

    def load_patch_data(self):
        patch_data = []
        for step, patch in self.data.items():
            filtered_patch = {key: value for key, value in patch.items() if key != "successful_data"}
            patch_data.append(filtered_patch)
        return patch_data


    def save_attack_data(self, url, data, key_type="basic"):
        if url not in self.data:
            self.data[url] = {}

        if key_type not in self.data[url]:
            self.data[url][key_type] = []

        step_number = len(self.data[url][key_type]) + 1
        step_data = {"step": step_number}
        step_data.update(data)

        self.data[url][key_type].append(step_data)

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


    def save_patch_data(self, patch_data):
        step_number = len(self.data) + 1
        self.data[step_number] = patch_data
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


    def save_bast_patch(self, best_patch_data):
        step_number = len(self.data) + 1
        self.data[step_number] = best_patch_data

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

