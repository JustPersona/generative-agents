"""
Author: Joon Sung Park (joonspk@stanford.edu)
Modified by: Joon Hee Kim (rlawnsgl191@gmail.com)
File: views.py
"""

import json
from os import listdir, remove
from os.path import exists, splitext
from urllib.parse import unquote
from datetime import datetime, timedelta
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render



sim_files = {
    "demo": {
        "payload": "compressed_storage/%s/payload.json",
        "meta": "compressed_storage/%s/meta.json",
        "move": "compressed_storage/%s/master_movement.json",
    },
    "replay": {
        "payload": "storage/%s/reverie/payload.json",
        "meta": "storage/%s/reverie/meta.json",
        "move": "storage/%s/movement/%s.json",
        "env": "storage/%s/environment",
    },
    "temp": {
        "step": "temp_storage/curr_step.json",
        "sim": "temp_storage/curr_sim_code.json",
    },
    "maze": {
        "meta": "static_dirs/assets/%s/matrix/maze_meta_info.json",
    },
    "map": {
        "json": "static_dirs/assets/%s/visuals/%s.json",
    },
}



def backendIsRunning():
    return exists(sim_files["temp"]["step"])

def backendStep():
    step = None
    if backendIsRunning():
        with open(sim_files["temp"]["step"]) as f:
            step = json.load(f)["step"]
    return step

def backendSim():
    sim_code = None
    if backendIsRunning():
        with open(sim_files["temp"]["sim"]) as f:
            sim_code = json.load(f)["sim_code"]
    return sim_code

def getBackendSimInfo():
    return {
        "sim_code": backendSim(),
        "step": backendStep(),
    }



def getSim(mode, sim_code):
    file = sim_files[mode]["meta"] % sim_code
    if not exists(file):
        return

    with open(file) as f:
        data = json.load(f)
    data["mode"] = mode

    payload_file = sim_files[mode]["payload"] % sim_code
    if not exists(payload_file):
        data["payload"] = {}
    else:
        with open(payload_file) as f:
            payload_info = json.load(f)
        for method, payloads in payload_info["methods"].items():
            for idx, payload in enumerate(payloads):
                payload_info["methods"][method][idx]["payload"] = unquote(str(payload["payload"]))
        data["payload"] = payload_info
    return data

def getSims():
    data = {}
    all_sim_codes = {
        "demo": listdir("compressed_storage"),
        "replay": listdir("storage"),
    }
    for key, sim_codes in all_sim_codes.items():
        for sim_code in sim_codes:
            if sim_code in data: continue
            sim_data = getSim(key, sim_code)
            if sim_data: data[sim_code] = sim_data
    return [{"sim_code": k, **v} for k, v in sorted(data.items(), key=lambda x: datetime.strptime(x[1]["curr_time"], "%B %d, %Y, %H:%M:%S").timestamp())]



def dashboard(request):
    context = {
        "backend": getBackendSimInfo(),
        "sim_codes": getSims(),
    }
    template = "pages/dashboard.html"
    return render(request, template, context)



def live(request):
    simInfo = getBackendSimInfo()
    step = simInfo["step"]
    sim_code = simInfo["sim_code"]

    if not step:
        return render(request, "pages/backend-error.html")

    #remove(sim_files["temp"]["step"])
    return simulator(request, sim_code, step)



def simulator(request, sim_code=None, step=0, speed=2):
    if sim_code is None:
        context = {
            "search": request.GET.get("search", ""),
            "sim_codes": reversed(getSims()),
        }
        return render(request, "pages/simulation_control.html", context)

    step = int(step)
    speed = int(speed) or 2
    play_speed = 2 ** (min(6, speed)-1)

    if exists(sim_files["demo"]["meta"] % sim_code):
        mode = "demo"
    elif exists(sim_files["replay"]["meta"] % sim_code):
        mode = "replay"
        play_speed = 32
    else:
        return HttpResponse(status=404)

    with open(sim_files[mode]["meta"] % sim_code) as json_file:
        meta = json.load(json_file)
    max_step = meta["step"]
    maze_name = meta["maze_name"]
    sec_per_step = meta["sec_per_step"]
    persona_names = meta["persona_names"]
    step = min(step, max_step)

    start_datetime = datetime.strptime(meta["start_date"] + " 00:00:00", '%B %d, %Y %H:%M:%S')
    start_datetime += timedelta(seconds=step * sec_per_step)
    start_datetime = start_datetime.strftime("%Y-%m-%dT%H:%M:%S")

    with open(sim_files["maze"]["meta"] % maze_name) as json_file:
        tile_width = int(json.load(json_file)["sq_tile_size"])

    map_json = sim_files["map"]["json"] % (maze_name, maze_name)
    with open(map_json) as json_file:
        map_data = json.load(json_file)
    layers = [{"name": x["name"], "visible": x["visible"]} for x in map_data["layers"]]
    tilesets = [{"path": x["image"], "name": splitext(x["image"].split("/")[-1])[0]} for x in map_data["tilesets"]]

    if mode == "replay":
        all_movement = {}
        persona_init_pos = dict()
        curr_json = (sim_files["replay"]["env"] % sim_code) + f"/{step}.json"
        with open(curr_json) as json_file:
            persona_init_pos_dict = json.load(json_file)
            for key, val in persona_init_pos_dict.items():
                if key in persona_names:
                    persona_init_pos[key.replace(" ", "_")] = [val["x"], val["y"]]
    else: # mode == "demo"
        # Loading the movement file
        move_file = sim_files["demo"]["move"] % sim_code
        with open(move_file) as json_file:
            raw_all_movement = json.load(json_file)
            raw_all_movement[str(max_step)] = {}

        # <all_movement> is the main movement variable that we are passing to the
        # frontend. Whereas we use ajax scheme to communicate steps to the frontend
        # during the simulation stage, for this demo, we send all movement
        # information in one step.
        all_movement = dict()

        # Preparing the initial step.
        # <init_prep> sets the locations and descriptions of all agents at the
        # beginning of the demo determined by <step>.
        
        init_prep = dict()
        for int_key in range(step, -1, -1):
            if len(init_prep.keys()) == len(persona_names): break
            key = str(int_key)
            val = raw_all_movement[key]
            for p in persona_names:
                if p not in init_prep and p in val:
                    init_prep[p] = val[p]
        persona_init_pos = dict()
        for p in persona_names:
            persona_init_pos[p.replace(" ","_")] = init_prep[p]["movement"]
        all_movement[step] = init_prep

        # Finish loading <all_movement>
        for int_key in range(step+1, max_step):
            all_movement[int_key] = raw_all_movement[str(int_key)]

    persona_names = [{
        "original": x,
        "underscore": x.replace(" ", "_"),
        "initial": x[0] + x.split(" ")[-1][0],
    } for x in persona_names]

    context = {
        "sim_code": sim_code,
        "step": step,
        "max_step": max_step,
        "persona_names": persona_names,
        "persona_init_pos": json.dumps(persona_init_pos),
        "all_movement": json.dumps(all_movement),
        "tile_width": tile_width,
        "start_datetime": start_datetime,
        "sec_per_step": sec_per_step,
        "play_speed": play_speed,
        "speed": speed,
        "map": {
            "height": map_data["height"],
            "width": map_data["width"],
            "tilesets": json.dumps(tilesets),
            "layers": json.dumps(layers),
        },
        "maze_name": maze_name,
        "mode": mode,
    }
    template = "pages/simulator.html"
    return render(request, template, context)



def replay_persona_state(request, sim_code, step, persona_name): 
    sim_code = sim_code
    step = int(step)

    persona_name_underscore = persona_name
    persona_name = " ".join(persona_name.split("_"))
    memory = f"compressed_storage/{sim_code}/personas/{persona_name}/bootstrap_memory"
    if not exists(memory): 
        memory = f"storage/{sim_code}/personas/{persona_name}/bootstrap_memory"

    with open(memory + "/scratch.json") as json_file:  
        scratch = json.load(json_file)

    with open(memory + "/spatial_memory.json") as json_file:  
        spatial = json.load(json_file)

    with open(memory + "/associative_memory/nodes.json") as json_file:  
        associative = json.load(json_file)

    a_mem_event = []
    a_mem_chat = []
    a_mem_thought = []

    for count in range(len(associative.keys()), 0, -1): 
        node_id = f"node_{str(count)}"
        node_details = associative[node_id]

        if node_details["type"] == "event":
            a_mem_event += [node_details]

        elif node_details["type"] == "chat":
            a_mem_chat += [node_details]

        elif node_details["type"] == "thought":
            a_mem_thought += [node_details]
    
    context = {"sim_code": sim_code,
               "step": step,
               "persona_name": persona_name, 
               "persona_name_underscore": persona_name_underscore, 
               "scratch": scratch,
               "spatial": spatial,
               "a_mem_event": a_mem_event,
               "a_mem_chat": a_mem_chat,
               "a_mem_thought": a_mem_thought}
    template = "pages/persona_state.html"
    return render(request, template, context)



def process_environment(request): 
    """
    <FRONTEND to BACKEND> 
    This sends the frontend visual world information to the backend server. 
    It does this by writing the current environment representation to 
    "storage/environment.json" file. 

    ARGS:
        request: Django request
    RETURNS: 
        HttpResponse: string confirmation message. 
    """
    # f_curr_sim_code = "temp_storage/curr_sim_code.json"
    # with open(f_curr_sim_code) as json_file:  
    #   sim_code = json.load(json_file)["sim_code"]

    data = json.loads(request.body)
    step = data["step"]
    sim_code = data["sim_code"]
    environment = data["environment"]

    with open(f"storage/{sim_code}/environment/{step}.json", "w") as outfile:
        outfile.write(json.dumps(environment, indent=2))

    return HttpResponse("received")

def update_environment(request):
    """
    <BACKEND to FRONTEND>
    This sends the backend computation of the persona behavior to the frontend
    visual server.
    It does this by reading the new movement information from
    "storage/movement.json" file.

    ARGS:
        request: Django request
    RETURNS:
        HttpResponse
    """

    data = json.loads(request.body)
    step = data["step"]
    sim_code = data["sim_code"]

    response_data = {"<step>": -1}
    stepFile = sim_files["replay"]["move"] % (sim_code, step)
    if exists(stepFile):
        with open(stepFile) as json_file:
            response_data = json.load(json_file)
            response_data["<step>"] = step
    return JsonResponse(response_data)

def path_tester_update(request):
    """
    Processing the path and saving it to path_tester_env.json temp storage for 
    conducting the path tester. 

    ARGS:
        request: Django request
    RETURNS: 
        HttpResponse: string confirmation message. 
    """
    data = json.loads(request.body)
    camera = data["camera"]

    with open(f"temp_storage/path_tester_env.json", "w") as outfile:
        outfile.write(json.dumps(camera, indent=2))

    return HttpResponse("received")
