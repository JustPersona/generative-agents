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
from itertools import count

from django.http import HttpResponse, JsonResponse, Http404
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

def get_map_data(maze_name="hacker_ville"):
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



# Views

def robots(request):
    lines = [
        "User-agent: *",
        "Disallow: /",
    ]
    return HttpResponse("\n".join(lines), content_type="text/plain")



@require_http_methods(["GET"])
def dashboard(request):
    return render(request, "pages/dashboard.html")



@require_http_methods(["PATCH"])
def pen_info_update(request):
    if not request.user.is_staff:
        return HttpResponse(status=404)

    try:
        data = json.loads(request.body)
        pen_code = data["pen_code"].strip()
        new_pen_code = data["new_pen_code"].strip()
        patches_applied = int(data["patches_applied"])
        pen_codes = get_pens()["pen_codes"]
    except Error as e:
        return HttpResponse(status=e.args[1])
    except:
        return HttpResponse(status=400)
    if pen_code != new_pen_code and new_pen_code in [x["pen_code"] for x in pen_codes]:
        return HttpResponse(status=409)

    for info in pen_codes:
        curr_modes = info["modes"]
        curr_pen_code = info["pen_code"]
        for mode in curr_modes:
            with open(pen_files[mode]["meta"] % curr_pen_code) as f:
                meta = json.load(f)
                meta_bak = meta.copy()
            if meta["fork_sim_code"] == pen_code:
                meta["fork_sim_code"] = new_pen_code
            if curr_pen_code == pen_code:
                meta["patches_applied"] = patches_applied
            if meta != meta_bak:
                with open(pen_files[mode]["meta"] % curr_pen_code, "w") as f:
                    json.dump(meta, f, indent=2)
            if curr_pen_code == pen_code and pen_code != new_pen_code:
                shutil.move(pen_files[mode]["root"] % pen_code, pen_files[mode]["root"] % new_pen_code)
    return HttpResponse(status=204)



@require_http_methods(["GET"])
def pen_test(request, pen_code=None, step=0, speed=2):
    if pen_code is None:
        context = {
            "search": request.GET.get("search", ""),
            "pen_codes": reversed(get_pens()["pen_codes"]),
        }
        return render(request, "pages/pen_test_details.html", context)

    try:
        info = get_pen(pen_code)
        mode = "preview" if info["base"] else info["modes"][0]
        step = int(step)
        speed = 6 if mode == "forkable" else min(6, int(speed) or 2)
        play_speed = 32 if mode == "forkable" else 2 ** (speed - 1)
    except Error:
        raise Http404()
    except:
        return HttpResponse(status=400)

    meta = info["meta"]
    max_step = meta["step"]
    maze_name = meta["maze_name"]
    persona_names = meta["persona_names"]
    step = min(step, max_step)

    map_data = get_map_data(maze_name)
    with open(pen_files["maze"]["visuals"] % (maze_name, maze_name)) as json_file:
        tile_width = int(json.load(json_file)["tilewidth"])

    persona_names = [{
        "original": x,
        "underscore": x.replace(" ", "_"),
        # "initial": x[0] + x.split(" ")[-1][0],
        "initial": x[0] + x.split(" ")[1][0],
    } for x in persona_names]

    context = {
        "running": get_running_info()["pen_code"] == pen_code,
        "pen_code": pen_code,
        "step": step,
        "max_step": max_step,
        "persona_names": persona_names,
        "tile_width": tile_width,
        "play_speed": play_speed,
        "speed": speed,
        "map": map_data,
        "maze_name": maze_name,
        "mode": mode,
    }
    template = "pages/pen_test_play.html"
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
    return HttpResponse(status=201)

@require_http_methods(["DELETE"])
def delete_pen_test(request):
    if not request.user.is_staff:
        return HttpResponse(status=404)

    try:
        data = json.loads(request.body)
        pen_code = data["pen_code"].strip()
        mode = data["mode"].strip()
    except:
        return HttpResponse("Bad Request", status=400)

    try:
        pen_root = pen_files[mode]["root"] % pen_code
        filepath, ext = splitext(pen_files["delete"]["name"] % (pen_code, mode))
        if exists(filepath + ext):
            for n in count(start=1, step=1):
                f = f"{filepath}-{n}"
                if not exists(f + ext): break
        shutil.make_archive(filepath, ext[1:], pen_root)
        shutil.rmtree(pen_root)
    except:
        return HttpResponse("Unknown Error", status=500)
    return HttpResponse()

@login_required(login_url=settings.LOGIN_URL)
@require_http_methods(["GET", "POST", "DELETE"])
def trash(request):
    if not request.user.is_staff:
        raise Http404()

    method = request.method
    if method == "GET":
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

    try:
        data = json.loads(request.body)
        pen_code = data["pen_code"].strip()
        mode = data["mode"].strip()
        new_pen_code = data.get("new_pen_code", "").strip() or pen_code
    except:
        return HttpResponse(status=400)

    file = pen_files["delete"]["name"] % (pen_code, mode)
    if not exists(file):
        return HttpResponse(status=404)

    if method == "POST":
        pen_path = pen_files[mode]["root"] % new_pen_code
        if exists(pen_path):
            return HttpResponse(f"Already exists: {mode}/{new_pen_code}", status=409)
        with TemporaryDirectory() as temp_dir:
            try:
                shutil.unpack_archive(file, temp_dir, "zip")
            except:
                return HttpResponse("Problems during recovery", status=500)
            shutil.move(temp_dir, pen_path)
    try:
        remove(file)
    except:
        pass

    return HttpResponse(status=204)



@require_http_methods(["GET"])
def persona_state(request, pen_code):
    try:
        mode = get_modes(pen_code)[0]
    except:
        raise Http404()

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
        "persona_name": request.GET.get("p"),
        "step": step,
        "states": states,
    }
    template = "pages/persona_state.html"
    return render(request, template, context)



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
        if path == "update_movement":
            response_data = self.update_movement(data)

        response_data["path"] = path
        await self.send_message(response_data)

    async def send_message(self, message):
        await self.send(text_data=json.dumps(message))

    def update_movement(self, data):
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

        response_data = get_all_datas(pen_code)
        running = get_running_info()

        return {
            "data": response_data,
            "running": running,
        }
