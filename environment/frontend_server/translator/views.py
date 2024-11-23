"""
Author: Joon Sung Park (joonspk@stanford.edu)
Modified by: Joon Hee Kim (rlawnsgl191@gmail.com)
File: views.py
"""

import sys, json, shutil
from os import listdir, remove
from os.path import exists, splitext
from urllib.parse import unquote
from datetime import datetime, timedelta
from tempfile import TemporaryDirectory

from django.http import HttpResponse, JsonResponse
from django.shortcuts import render
from django.views.decorators.http import require_http_methods

sys.path.append("..")
from compress_pen_storage import compress



pen_files = {
    "memory": {
        "payload": "/personas/Black Hacker/bootstrap_memory/payload.json",
    },
    "compressed": {
        "root": "compressed_storage/%s",
        "meta": "compressed_storage/%s/meta.json",
        "move": "compressed_storage/%s/master_movement.json",
    },
    "forkable": {
        "root": "storage/%s",
        "meta": "storage/%s/reverie/meta.json",
        "move": "storage/%s/movement/%s.json",
        "env": "storage/%s/environment/%s.json",
    },
    "delete": {
        "root": "../trash",
        "name": "../trash/%s-%s",
    },
    "temp": {
        "root": "temp_storage",
        "step": "temp_storage/curr_step.json",
        "code": "temp_storage/curr_sim_code.json",
        "env": "temp_storage/path_tester_env.json",
    },
    "maze": {
        "root": "static_dirs/assets/%s/maze",
        "visuals": "static_dirs/assets/%s/visuals/%s.json",
    },
}



# Functions

def backendIsRunning():
    return exists(pen_files["temp"]["step"])

def backendStep():
    step = None
    if backendIsRunning():
        with open(pen_files["temp"]["step"]) as f:
            step = json.load(f).get("step")
    return step

def backendCode():
    pen_code = None
    if backendIsRunning():
        with open(pen_files["temp"]["code"]) as f:
            pen_code = json.load(f).get("pen_code")
    return pen_code

def getBackendInfo():
    return {
        "pen_code": backendCode(),
        "step": backendStep(),
    }



def getMapData(maze_name="the_ville"):
    map_json = pen_files["maze"]["visuals"] % (maze_name, maze_name)
    if not exists(map_json):
        return {}

    with open(map_json) as json_file:
        map_data = json.load(json_file)
    layers = [{"name": x["name"], "visible": x["visible"]} for x in map_data["layers"]]
    tilesets = [{"path": x["image"], "name": splitext(x["image"].split("/")[-1])[0]} for x in map_data["tilesets"]]

    return {
        "height": map_data["height"],
        "width": map_data["width"],
        "tilesets": json.dumps(tilesets),
        "layers": json.dumps(layers),
    }

def getPayloadInfo(mode=None, pen_code=None, *, to_list=False):
    data = {
        "count": {
            "vulnerabilities": 0,
            "payloads": 0
        },
        "data": [],
    }
    payload_file = (pen_files[mode]["root"] % pen_code) + pen_files["memory"]["payload"]
    if exists(payload_file):
        with open(payload_file) as f:
            payload_data = json.load(f)
        for url, items in payload_data.items():
            data["count"]["payloads"] += len(items["basic"])
            for idx, payload in enumerate(items["basic"]):
                if payload["observations"] == "exploit_successful":
                    data["count"]["vulnerabilities"] += 1
                items["basic"][idx] = json.loads(json.dumps(items["basic"][idx]).replace("<", "&lt;").replace(">", "&gt;"))
            data["data"] += [{"url": url, **items}]

    if to_list is True:
        tmp = {}
        for x in data["data"]:
            for y in x["basic"]:
                y["url"] = x["url"]
                tmp[y["timestamp"]] = y
        data = tmp
    return data

def getPen(pen_code, mode=None):
    modes = []
    if exists(pen_files["compressed"]["meta"] % pen_code):
        modes += ["compressed"]
    if exists(pen_files["forkable"]["meta"] % pen_code):
        modes += ["forkable"]
    if len(modes) == 0: return
    mode = mode or modes[0]

    with open(pen_files[mode]["meta"] % pen_code) as f:
        data = json.load(f)
    data["mode"] = mode
    for x in modes: data[x] = True

    data["payloads"] = getPayloadInfo(mode, pen_code)
    return data

def getPens():
    data = {}
    all_pen_codes = penList()
    for mode, pen_codes in all_pen_codes.items():
        for pen_code in pen_codes:
            if pen_code in data: continue
            pen_data = getPen(pen_code, mode)
            if pen_data: data[pen_code] = pen_data
    return [{"pen_code": k, **v} for k, v in sorted(data.items(), key=lambda x: datetime.strptime(x[1]["curr_time"], "%B %d, %Y, %H:%M:%S").timestamp())]

def penList(mode=None):
    data = {}
    if mode is None or mode == "compressed":
        data["compressed"] = [x for x in listdir("compressed_storage") if exists(pen_files["compressed"]["meta"] % x)]
    if mode is None or mode == "forkable":
        data["forkable"] = [x for x in listdir("storage") if exists(pen_files["forkable"]["meta"] % x)]
    return data

def getChartData(data=None, *, min=0):
    if data is None: data = getPens()

    chart_keys = ["attack", "url"]
    chart_data = {k: {"labels": [], "datasets": []} for k in chart_keys}

    for x in data:
        if not x["payloads"]["data"]: continue
        for y in x["payloads"]["data"]:
            url = y.get("url")
            for z in y["basic"]:
                chart_data["attack"] = addChartData(chart_data["attack"], z["attack_name"], z["observations"] == "exploit_successful")
                chart_data["url"] = addChartData(chart_data["url"], url or z["url"], [1, z["observations"] == "exploit_successful"])

    # basics = [basic for x in data if x["payloads"]["data"] for y in x["payloads"]["data"] for basic in y["basic"]]

    # chart_data["attack"] = {"labels": sorted(set([basic["attack_name"] for basic in basics]))}
    # chart_data["attack"]["datasets"] = [
    #     len(list(filter(
    #         lambda basic: basic["attack_name"] == label and basic["observations"] == "exploit_successful",
    #         [basic for basic in basics]
    #     ))) for label in chart_data["attack"]["labels"]
    # ]

    # chart_data["url"] = {"labels": sorted(set([basic["attack_name"] for basic in basics]))}

    # chart_data = [{
    #     "pen_code": x["pen_code"],
    #     "vulnerabilities": x["payloads"]["count"]["vulnerabilities"],
    #     "payloads": x["payloads"]["count"]["payloads"],
    # } for x in data if x["step"] != 0]

    for k in chart_keys:
        a_min = min - len(chart_data[k]["labels"])
        chart_data[k]["labels"] += [""] * a_min
        chart_data[k]["datasets"] += [0] * a_min

    return chart_data

def addChartData(data, label, value=0):
    try:
        idx = data["labels"].index(label)
        if type(value) != list:
            data["datasets"][idx] += value
        else:
            for i, x in enumerate(value):
                data["datasets"][idx][i] += x
    except:
        idx = -1
        data["labels"].append(label)
        data["datasets"].append(value)
    return data



# Views

def robots(request):
    lines = [
        "User-agent: *",
        "Disallow: /",
    ]
    return HttpResponse("\n".join(lines), content_type="text/plain")

@require_http_methods(["GET"])
def dashboard(request):
    context = {
        "backend": getBackendInfo(),
        "pen_codes": getPens(),
    }
    context["chart"] = getChartData(context["pen_codes"], min=4)
    template = "pages/dashboard.html"
    return render(request, template, context)

@require_http_methods(["POST"])
def pen_info(request):
    pen_code = json.loads(request.body).get("pen_code").strip()
    data = getPen(pen_code)
    if not data:
        return HttpResponse("Not found", status=404)
    return JsonResponse(data)

@require_http_methods(["POST"])
def pen_info_update(request):
    if not request.user.is_staff:
        return HttpResponse(status=404)

    data = json.loads(request.body)
    pen_code = data.get("pen_code", "").strip()
    new_pen_code = data.get("new_pen_code", "").strip()

    if not pen_code or not new_pen_code:
        return HttpResponse("Bad Request", status=400)
    elif pen_code == new_pen_code:
        return HttpResponse()

    all_pen_codes = penList()
    for mode, pen_codes in all_pen_codes.items():
        for curr_pen_code in pen_codes:
            with open(pen_files[mode]["meta"] % curr_pen_code) as f:
                meta = json.load(f)
            fork_pen_code = meta["fork_sim_code"]
            if fork_pen_code == pen_code:
                meta["fork_sim_code"] = new_pen_code
                with open(pen_files[mode]["meta"] % curr_pen_code, "w") as f:
                    json.dump(meta, f, indent=2)
            if curr_pen_code == pen_code:
                shutil.move(pen_files[mode]["root"] % pen_code, pen_files[mode]["root"] % new_pen_code)
    return JsonResponse(data)



@require_http_methods(["GET"])
def path_tester(request, maze_name="hacker_ville"):
    maps = [x for x in listdir("static_dirs/assets") if exists(pen_files["maze"]["visuals"] % (x, x))]
    if maze_name not in maps:
        return HttpResponse(status=404)
    map_data = getMapData(maze_name)
    map_data["list"] = maps

    context = {
        "pen_code": f"Path Tester: {maze_name}",
        "map": map_data,
        "maze_name": maze_name,
        "mode": "tester",
    }
    template = "pages/pen_test_play.html"
    return render(request, template, context)



@require_http_methods(["GET"])
def backend(request):
    penInfo = getBackendInfo()
    step = penInfo["step"]
    pen_code = penInfo["pen_code"]

    if not step or not pen_code:
        return render(request, "pages/backend-error.html")

    #remove(pen_files["temp"]["step"])
    return pen_test(request, pen_code, step)



@require_http_methods(["GET"])
def pen_test(request, pen_code=None, step=0, speed=2):
    if pen_code is None:
        context = {
            "search": request.GET.get("search", ""),
            "pen_codes": reversed(getPens()),
        }
        return render(request, "pages/pen_test_details.html", context)

    step = int(step)
    speed = int(speed) or 2
    play_speed = 2 ** (min(6, speed)-1)

    if exists(pen_files["compressed"]["meta"] % pen_code):
        mode = "compressed"
    elif exists(pen_files["forkable"]["meta"] % pen_code):
        mode = "forkable"
        speed = 6
        play_speed = 32
    else:
        return HttpResponse(status=404)

    payloads = getPayloadInfo(mode, pen_code, to_list=True)
    with open(pen_files[mode]["meta"] % pen_code) as json_file:
        meta = json.load(json_file)
    max_step = meta["step"]
    maze_name = meta["maze_name"]
    sec_per_step = meta["sec_per_step"]
    persona_names = meta["persona_names"]
    step = min(step, max_step)

    start_datetime = datetime.strptime(meta["start_date"] + " 00:00:00", '%B %d, %Y %H:%M:%S')
    start_datetime += timedelta(seconds=step * sec_per_step)
    start_datetime = start_datetime.strftime("%Y-%m-%dT%H:%M:%S")

    map_data = getMapData(maze_name)
    with open(pen_files["maze"]["visuals"] % (maze_name, maze_name)) as json_file:
        tile_width = int(json.load(json_file)["tilewidth"])

    if mode == "forkable":
        all_movement = {}
        persona_init_pos = dict()
        curr_json = (pen_files["forkable"]["env"] % (pen_code, step))
        with open(curr_json) as json_file:
            persona_init_pos_dict = json.load(json_file)
            for key, val in persona_init_pos_dict.items():
                if key in persona_names:
                    persona_init_pos[key.replace(" ", "_")] = [val["x"], val["y"]]
    else: # mode == "compressed"
        # Loading the movement file
        move_file = pen_files["compressed"]["move"] % pen_code
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
        "payloads": payloads,
        "pen_code": pen_code,
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
        "map": map_data,
        "maze_name": maze_name,
        "mode": mode,
    }
    template = "pages/pen_test_play.html"
    return render(request, template, context)



@require_http_methods(["GET"])
def replay_persona_state(request, pen_code, step, persona_name):
    pen_code = pen_code
    step = int(step)

    persona_name_underscore = persona_name
    persona_name = " ".join(persona_name.split("_"))
    memory = f"compressed_storage/{pen_code}/personas/{persona_name}/bootstrap_memory"
    if not exists(memory):
        memory = f"storage/{pen_code}/personas/{persona_name}/bootstrap_memory"

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

    context = {"pen_code": pen_code,
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



@require_http_methods(["POST"])
def compress_pen_test(request):
    if not request.user.is_staff:
        return HttpResponse(status=404)

    pen_code = json.loads(request.body).get("pen_code").strip()
    if not pen_code:
        return HttpResponse(status=400)

    try:
        compress(pen_code)
    except FileNotFoundError as e:
        return HttpResponse(f"Not found", status=404)
    except FileExistsError as e:
        return HttpResponse(f"Already Compressed", status=400)
    except ValueError as e:
        return HttpResponse(f"This is base Environment", status=400)
    except:
        return HttpResponse("Unknown Error", status=500)
    return HttpResponse()

@require_http_methods(["POST"])
def delete_pen_test(request):
    if not request.user.is_staff:
        return HttpResponse(status=404)

    data = json.loads(request.body)
    pen_code = data.get("pen_code").strip()
    mode = data.get("mode").strip()

    if not pen_code:
        return HttpResponse("Bad Request", status=400)

    try:
        pen_root = pen_files[mode]["root"] % pen_code
        n = 0
        while True:
            filepath = pen_files["delete"]["name"] % (pen_code, f"{mode}{"" if n == 0 else f"-{n}"}")
            if not exists(filepath + ".zip"): break
            n += 1
        shutil.make_archive(filepath, "zip", pen_root)
        shutil.rmtree(pen_root)
    except:
        return HttpResponse("Unknown Error", status=500)
    return HttpResponse()

@require_http_methods(["GET", "POST"])
def trash(request):
    if not request.user.is_staff:
        return HttpResponse(status=404)

    if request.method == "GET":
        context = {"pen_codes": {}}
        for file in listdir(pen_files["delete"]["root"]):
            file, ext = splitext(file)
            file = file.split("-")
            pen_code, mode = "-".join(file[:-1]), file[-1]
            if pen_code not in context["pen_codes"]:
                context["pen_codes"][pen_code] = dict()
            context["pen_codes"][pen_code][mode] = True
        template = "pages/trash.html"
        return render(request, template, context)

    data = json.loads(request.body)
    try:
        pen_code = data["pen_code"].strip()
        mode = data["mode"].strip()
        action = data["action"].strip()
        new_pen_code = data.get("new_pen_code", "").strip() or pen_code
    except:
        return HttpResponse(status=400)
    
    file = (pen_files["delete"]["name"] % (pen_code, mode)) + ".zip"
    if not exists(file):
        return HttpResponse(status=400)
    elif action not in ["restore", "delete"]:
        return HttpResponse(status=400)
    else:
        if action == "restore":
            directory = pen_files[mode]["root"] % new_pen_code
            if exists(directory):
                return HttpResponse(f"Already exists: {mode}/{new_pen_code}", status=409)
            with TemporaryDirectory() as dir:
                try:
                    shutil.unpack_archive(file, dir, "zip")
                except:
                    return HttpResponse("Problems during recovery", status=500)
                shutil.move(dir, directory)
        try:
            remove(file)
        except:
            pass

    return HttpResponse()



@require_http_methods(["POST"])
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
    # f_curr_pen_code = pen_files["temp"]["code"]
    # with open(f_curr_sim_code) as json_file:
    #   pen_code = json.load(json_file)["pen_code"]

    data = json.loads(request.body)
    step = data["step"]
    pen_code = data["pen_code"]
    environment = data["environment"]

    with open(pen_files["forkable"]["env"] % (pen_code, step), "w") as outfile:
        outfile.write(json.dumps(environment, indent=2))

    return HttpResponse("received")

@require_http_methods(["POST"])
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
    pen_code = data["pen_code"]

    response_data = {"<step>": -1}
    stepFile = pen_files["forkable"]["move"] % (pen_code, step)
    if exists(stepFile):
        with open(stepFile) as json_file:
            response_data = json.load(json_file)
            response_data["<step>"] = step
    return JsonResponse(response_data)

@require_http_methods(["POST"])
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

    with open(pen_files["temp"]["env"], "w") as outfile:
        outfile.write(json.dumps(camera, indent=2))

    return HttpResponse("received")
