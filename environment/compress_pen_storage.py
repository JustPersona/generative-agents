#!/usr/bin/env python3

"""
Author: Joon Sung Park (joonspk@stanford.edu)
Modified by: Joon Hee Kiim (rlawnsgl191@gmail.com)

File: compress_pen_storage.py
Description: Compresses a simulation for replay demos.
"""

import json
from os.path import exists, abspath
from shutil import copytree, rmtree



def compress(pen_code):
    dirname = abspath(f"{__file__}/../..")
    frontend_root = f"{dirname}/environment/frontend_server"
    pen_storage = f"{frontend_root}/storage/{pen_code}"
    compressed_storage = f"{frontend_root}/compressed_storage/{pen_code}"
    persona_folder = pen_storage + "/personas"
    move_folder = pen_storage + "/movement"
    reverie_folder = pen_storage + "/reverie"
    meta_file = reverie_folder + "/meta.json"

    if not exists(pen_storage):
        raise FileNotFoundError(pen_storage[len(dirname):])
    elif exists(compressed_storage):
        raise FileExistsError(compressed_storage[len(dirname):])
    with open(meta_file) as f:
        meta = json.load(f)

    try:
        step = int(meta["step"])
        if step == 0: raise
    except:
        raise ValueError(f"step is 0 or not found in {meta_file[len(dirname):]}")

    persona_names = meta["persona_names"]

    persona_last_move = dict()
    master_move = dict()
    for i in range(step):
        master_move[i] = dict()
        with open(f"{move_folder}/{i}.json") as json_file:
            i_move_dict = json.load(json_file)["persona"]
        for p in persona_names:
            if i == 0 or i_move_dict[p] != persona_last_move[p]:
                persona_last_move[p] = i_move_dict[p]
                master_move[i][p] = i_move_dict[p]

    try:
        copytree(reverie_folder, compressed_storage)
        copytree(persona_folder, f"{compressed_storage}/personas/")
        with open(f"{compressed_storage}/master_movement.json", "w") as outfile:
            outfile.write(json.dumps(master_move, indent=2))
    except Exception as e:
        rmtree(compressed_storage)
        raise e



if __name__ == '__main__':
    pen_code = input("Penetration Testing Name: ")
    compress(pen_code)
