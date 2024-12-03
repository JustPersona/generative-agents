"""
Author: Joon Sung Park (joonspk@stanford.edu)
Modified by: Joon Hee Kim (rlawnsgl191@gmail.com)
File: views.py
"""

import sys, json, shutil
from os import listdir, remove
from os.path import exists, splitext
from datetime import datetime, timedelta
from tempfile import TemporaryDirectory

from django.http import HttpResponse, JsonResponse
from django.shortcuts import render
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required
from django.conf import settings

from channels.generic.websocket import AsyncWebsocketConsumer

sys.path.append("..")
from compress_pen_storage import compress
from api.views import *
from utils import *



# Functions

def backendIsRunning():
    return exists(pen_files["temp"]["code"])

def backendStep():
    step = None
    if backendIsRunning() and exists(pen_files["temp"]["step"]):
        with open(pen_files["temp"]["step"]) as f:
            step = json.load(f).get("step")
    return step

def backendCode():
    pen_code = None
    if backendIsRunning():
        with open(pen_files["temp"]["code"]) as f:
            pen_code = json.load(f).get("sim_code")
    return pen_code

def getBackendInfo():
    return {
        "pen_code": backendCode(),
        "step": backendStep(),
    }



def getMapData(maze_name="hacker_ville"):
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

def getPayloadInfo(mode, pen_code):
    data = {
        "count": {
            "vulnerabilities": 0,
            "payloads": 0
        },
        "data": {},
    }

    for p_name in black_hats:
        payload_file = (pen_files[mode]["root"] % pen_code) + (pen_files["memory"]["payload"] % p_name)
        if not exists(payload_file): continue
        with open(payload_file) as f:
            payload_data = json.load(f)
        for url, items in payload_data.items():
            data["count"]["payloads"] += len(items["basic"])
            for idx, payload in enumerate(items["basic"]):
                step = payload["timestamp"]
                if payload["observations"] == "exploit_successful":
                    data["count"]["vulnerabilities"] += 1
                items["basic"][idx] = json.loads(json.dumps(items["basic"][idx]).replace("<", "&lt;").replace(">", "&gt;"))
                items["basic"][idx]["url"] = url
                if step not in data["data"]: data["data"][step] = {}
                data["data"][step][p_name] = items["basic"][idx]
    return data

def getPatches(mode, pen_code):
    best = dict()
    for owner in server_owners:
        payload_file = (pen_files[mode]["root"] % pen_code) + (pen_files["memory"]["payload"] % owner)
        if not exists(payload_file): continue
        with open(payload_file) as f:
            patch_data = json.load(f)
        for items in patch_data.values():
            p_name = items["best_patch"]["proposer"]
            step = items["best_patch"]["timestamp"]
            reason = items["reason"]
            if step not in best: best[step] = dict()
            if p_name not in best[step]: best[step][p_name] = list()
            best[step][p_name] += [reason]

    data = {
        "count": {
            "vulnerable_files": [],
            "patch_suggestion": 0,
            "best_suggestion": len(set([(step, p_name) for step, x in best.items() for p_name in x.keys()])),
        },
        "data": {},
    }
    for p_name in white_hats:
        payload_file = (pen_files[mode]["root"] % pen_code) + (pen_files["memory"]["payload"] % p_name)
        if not exists(payload_file): continue
        with open(payload_file) as f:
            patch_data = json.load(f)
        data["count"]["patch_suggestion"] += len(patch_data)
        for items in patch_data.values():
            step = items["timestamp"]
            data["count"]["vulnerable_files"].extend([x["file_path"] for x in items["patch_suggestion"]])
            if step not in data["data"]: data["data"][step] = {}
            data["data"][step][p_name] = {
                "urls": list(items["successful_data"].keys()),
                "attack": list(set([y["attack_name"] for x in items["successful_data"].values() for y in x])),
                "best": best.get(step, {}).get(p_name, []),
                "suggestion": items["patch_suggestion"],
            }

    data["count"]["vulnerable_files"] = len(set(data["count"]["vulnerable_files"]))
    return data

def getMode(pen_code, *, mode=None, all=False):
    ls = list()
    for x in ["compressed", "forkable"]:
        if exists(pen_files[x]["meta"] % pen_code):
            if mode is None and all is False: return x
            ls += [x]
    if all is True:
        return ls
    if mode is not None:
        return mode in ls


def isBase(pen_code):
    mode = getMode(pen_code)
    with open(pen_files[mode]["meta"] % pen_code) as f:
        meta = json.load(f)
    if mode == "forkable" and meta["step"] == 0 and meta["fork_sim_code"] == pen_code:
        return True
    return False

def getPen(pen_code, mode=None):
    modes = getMode(pen_code, all=True)
    if len(modes) == 0: return
    mode = mode or modes[0]

    with open(pen_files[mode]["meta"] % pen_code) as f:
        data = json.load(f)
    data["mode"] = mode
    data["isBase"] = isBase(pen_code)
    for x in modes: data[x] = True

    data["payloads"] = getPayloadInfo(mode, pen_code)
    data["patches"] = getPatches(mode, pen_code)
    return data

def getPens():
    data = {}
    all_pen_codes = penList()
    for mode, pen_codes in all_pen_codes.items():
        for pen_code in pen_codes:
            if pen_code in data: continue
            pen_data = getPen(pen_code, mode)
            if pen_data: data[pen_code] = pen_data
    return [{"pen_code": k, **v} for k, v in sorted(data.items(), key=lambda x: datetime.strptime(x[1].get("created_at", x[1]["curr_time"]), "%B %d, %Y, %H:%M:%S").timestamp())]

def penList(mode=None):
    data = {}
    if mode is None or mode == "compressed":
        data["compressed"] = [x for x in listdir("compressed_storage") if exists(pen_files["compressed"]["meta"] % x)]
    if mode is None or mode == "forkable":
        data["forkable"] = [x for x in listdir("storage") if exists(pen_files["forkable"]["meta"] % x)]
    return data

def getChatting(pen_code, *, start_datetime=None, sec_per_step=10, first_step=0, last_step=None):
    chats = dict()
    last_chats = dict()

    mode = getMode(pen_code)
    if mode is None:
        return {}
    
    if start_datetime is None:
        with open(pen_files[mode]["meta"] % pen_code) as f:
            start_datetime = json.load(f)["start_date"]
        start_datetime = datetime.strptime(start_datetime + " 00:00:00", '%B %d, %Y %H:%M:%S')

    if last_step is None:
        with open(pen_files[mode]["meta"] % pen_code) as f:
            last_step = json.load(f)["step"]

    curr_datetime = start_datetime
    if mode == "compressed":
        with open(pen_files[mode]["move"] % pen_code) as f:
            data = json.load(f)
        for step in range(first_step, last_step+1):
            try:
                personas = data[str(step)]
            except:
                break
            x = parseChat(personas, curr_datetime, last_chats)
            curr_datetime += timedelta(seconds=sec_per_step)
            if x: chats[step] = x
    else:
        for step in range(first_step, last_step+1):
            try:
                with open(pen_files["forkable"]["move"] % (pen_code, step)) as f:
                    personas = json.load(f)["persona"]
            except:
                break
            x = parseChat(personas, curr_datetime, last_chats)
            curr_datetime += timedelta(seconds=sec_per_step)
            if x: chats[step] = x
    return chats

def parseChat(personas, curr_datetime, last_chats={}):
    data = list()
    for p_name, p_data in personas.items():
        chat = p_data["chat"]
        if chat is None: continue
        for c in chat:
            if c[0] != p_name: continue
            if last_chats.get(p_name) == c[1]: continue
            last_chats[p_name] = c[1]
            data += [{
                "name": p_name,
                "chat": c[1],
                "datetime": curr_datetime.strftime("%Y-%m-%dT%H:%M:%S"),
            }]
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
    template = "pages/dashboard.html"
    return render(request, template, context)

@require_http_methods(["POST"])
def pen_info(request):
    pen_code = json.loads(request.body).get("pen_code").strip()
    data = getPen(pen_code)
    if not data:
        return HttpResponse("Not found", status=404)
    data["chats"] = getChatting(pen_code)
    return JsonResponse(data)

@require_http_methods(["POST"])
def pen_info_update(request):
    if not request.user.is_staff:
        return HttpResponse(status=404)

    data = json.loads(request.body)
    pen_code = data.get("pen_code", "").strip()
    new_pen_code = data.get("new_pen_code", "").strip()
    description = data.get("description", "").strip()

    if not pen_code and not new_pen_code and not description:
        return HttpResponse("Bad Request", status=400)
    
    for mode in getMode(pen_code, all=True):
        with open(pen_files[mode]["meta"] % pen_code, "r+") as f:
            meta = json.load(f)
            meta["description"] = description
            f.seek(0)
            json.dump(meta, f, indent=2)
            f.truncate()

    if pen_code == new_pen_code:
        return HttpResponse()

    if pen_code != new_pen_code:
        all_pen_codes = penList()
        for pen_codes in all_pen_codes.values():
            for curr_pen_code in pen_codes:
                modes = getMode(curr_pen_code, all=True)
                for mode in modes:
                    with open(pen_files[mode]["meta"] % curr_pen_code) as f:
                        meta = json.load(f)
                    fork_pen_code = meta["fork_sim_code"]
                    if fork_pen_code == pen_code:
                        meta["fork_sim_code"] = new_pen_code
                        with open(pen_files[mode]["meta"] % curr_pen_code, "w") as f:
                            json.dump(meta, f, indent=2)
                    if curr_pen_code == pen_code:
                        shutil.move(pen_files[mode]["root"] % pen_code, pen_files[mode]["root"] % new_pen_code)
    return HttpResponse()



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

    mode = getMode(pen_code)
    if mode is None:
        return HttpResponse(status=404)
    elif mode == "forkable":
        speed = 6
        play_speed = 32


    with open(pen_files[mode]["meta"] % pen_code) as json_file:
        meta = json.load(json_file)
    max_step = meta["step"]
    maze_name = meta["maze_name"]
    sec_per_step = meta["sec_per_step"]
    persona_names = meta["persona_names"]
    if isBase(pen_code):
        mode = "preview"
    step = min(step, max_step)

    start_datetime = datetime.strptime(meta["start_date"] + " 00:00:00", '%B %d, %Y %H:%M:%S')
    chats = getChatting(pen_code, last_step=[step, None][mode == "compressed"])
    start_datetime += timedelta(seconds=step * sec_per_step)
    start_datetime = start_datetime.strftime("%Y-%m-%dT%H:%M:%S")

    map_data = getMapData(maze_name)
    with open(pen_files["maze"]["visuals"] % (maze_name, maze_name)) as json_file:
        tile_width = int(json.load(json_file)["tilewidth"])

    if mode in ["forkable", "preview"]:
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
        move_file = pen_files[mode]["move"] % pen_code
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
        # "initial": x[0] + x.split(" ")[-1][0],
        "initial": x[0] + x.split(" ")[1][0],
    } for x in persona_names]

    context = {
        "running": getBackendInfo().get("pen_code") == pen_code,
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
        "chats": json.dumps(chats),
        "mode": mode,
    }
    template = "pages/pen_test_play.html"
    return render(request, template, context)



@require_http_methods(["GET"])
def persona_state(request, pen_code):
    persona_name = request.GET.get("p")
    mode = getMode(pen_code)
    if mode is None:
        return HttpResponse(status=404)

    with open(pen_files[mode]["meta"] % pen_code) as f:
        meta = json.load(f)
    step = int(meta["step"])
    persona_names = meta["persona_names"]

    states = list()
    storage = pen_files[mode]["root"] % pen_code
    for p_name in persona_names:
        p_name_os = p_name.replace(" ", "_")
        with open(storage + pen_files["memory"]["scratch"] % p_name) as json_file:
            scratch = json.load(json_file)
        with open(storage + pen_files["memory"]["spatial"] % p_name) as json_file:
            spatial = json.load(json_file)
        with open(storage + pen_files["memory"]["associative"] % p_name) as json_file:
            associative = json.load(json_file)

        a_mem_event = []
        a_mem_chat = []
        a_mem_thought = []
        for count in range(len(associative.keys()), 0, -1):
            node_id = f"node_{count}"
            node_details = associative[node_id]

            if node_details["type"] == "event":
                a_mem_event += [node_details]
            elif node_details["type"] == "chat":
                a_mem_chat += [node_details]
            elif node_details["type"] == "thought":
                a_mem_thought += [node_details]
        states += [{
            "p_name": p_name,
            "p_name_os": p_name_os,
            "scratch": scratch,
            "spatial": spatial,
            "a_mem_event": a_mem_event,
            "a_mem_chat": a_mem_chat,
            "a_mem_thought": a_mem_thought,
        }]

    context = {
        "pen_code": pen_code,
        "persona_name": persona_name,
        "step": step,
        "states": states,
    }
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

@login_required(login_url=settings.LOGIN_URL)
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



# Web Socket

class ReverieConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        await self.accept()

    async def disconnect(self, code):
        return super().disconnect(code)

    async def receive(self, text_data):
        data = json.loads(text_data)
        path = data["path"]

        response_data = dict()
        if path == "update_environment":
            response_data = self.update_environment(data)

        response_data["path"] = path
        await self.send_message(response_data)

    async def send_message(self, message):
        await self.send(text_data=json.dumps(message))

    def update_environment(self, data):
        """
        <BACKEND to FRONTEND>
        This sends the backend computation of the persona behavior to the frontend
        visual server.
        It does this by reading the new movement information from
        "storage/movement.json" file.

        ARGS:
            Dict parsed from WebSocket
        RETURNS:
            movement.json to Dict
        """
        step = data["step"]
        pen_code = data["pen_code"]
        running = data.get("running")

        response_data = {"step": -1}
        stepFile = pen_files["forkable"]["move"] % (pen_code, step)
        if exists(stepFile):
            with open(stepFile) as json_file:
                response_data = json.load(json_file)
            response_data["step"] = step
            response_data["chats"] = getChatting(pen_code, first_step=step, last_step=step).get(step)
            response_data["payload"] = getPayloadInfo("forkable", pen_code)["data"].get(step)
            response_data["patch"] = getPatches("forkable", pen_code)["data"].get(step)
        if running:
            response_data["running"] = backendIsRunning()
        return response_data
