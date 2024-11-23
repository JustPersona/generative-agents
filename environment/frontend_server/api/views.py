import json
import traceback
from os import listdir
from os.path import exists
from collections import Counter
from datetime import datetime
from django.http import JsonResponse

from utils import *



def not_found(request):
    return JsonResponse({
        "message": "404 Not found",
        "status": 404,
    }, status=404)

def help(request):
    data = {"help": list()}

    paths = [
        ["/api/running", "Backend Running Status"],
        ["/api/pens", "list of pen_codes with meta info"],
        ["/api/pens/<pen_code>", "<pen_code>'s meta info"],
        ["/api/pens/<pen_code>/<step>", "What to do when <step>. If <step> is -1, all steps"],
        ["/api/pens/<pen_code>/payloads", "list of pen_codes with meta info"],
        ["/api/pens/<pen_code>/patches", "<pen_code>'s all patches"],
        ["/api/pens/<pen_code>/best", "<pen_code>'s best patches"],
        ["/api/charts", "All Charts"],
        ["/api/charts/pens", "Chart data by pen_codes"],
        ["/api/charts/pens/<pen_code>", "chart data for <pen_code>"],
        ["/api/charts/urls", "Chart data by URLs"],
        ["/api/charts/attack", "Chart data by Attacks"],
        ["/api/charts/attack/<attack_name>", "Chart data for <attack_name>"],
    ]
    data["help"] = [{"path": p, "response": d} for p, d in paths]

    return JsonResponse(data)

class Error(Exception):
    def __init__(self, message, status):
        super().__init__({
            "message": message,
            "status": status,
        }, status)

def get_response(fn, *args, **kwargs):
    data = dict()
    status = kwargs.get("status", 200)
    try:
        x = fn(*args, **kwargs)
        if type(x) == tuple:
            data, status = x
        else:
            data = x
    except Error as e:
        data, status = e.args
    except Exception as e:
        print("########## Error TraceBack:", flush=True)
        print(traceback.format_exc(), flush=True)
        print("########## Error End", flush=True)
        status = 500
        data = {
            "message": "Server Error",
            "status": status,
        }
    return JsonResponse(data, status=status)



# Pen Info Functions

def running_info():
    data = {
        "running": bool(),
        "pen_code": None,
        "step": None,
    }

    if exists(pen_files["temp"]["code"]):
        with open(pen_files["temp"]["code"]) as f:
            data["pen_code"] = json.load(f).get("sim_code")
    if exists(pen_files["temp"]["step"]):
        with open(pen_files["temp"]["step"]) as f:
            data["step"] = json.load(f).get("step")

    data["running"] = data["pen_code"] is not None and data["step"] is not None
    return data

def get_modes(pen_code):
    data = list()
    for x in ["compressed", "forkable"]:
        if exists(pen_files[x]["meta"] % pen_code):
            data += [x]
    if len(data) == 0:
        raise Error(f"Not found: pen_code: {pen_code}", 404)
    return data

def pen_list():
    return [p["pen_code"] for p in pen_infos()["pen_codes"]]

def pen_infos():
    data = {
        "count": 0,
        "pen_codes": list(),
    }

    pen_codes = [x for x in listdir("compressed_storage") if exists(pen_files["compressed"]["meta"] % x)]
    pen_codes += [x for x in listdir("storage") if exists(pen_files["forkable"]["meta"] % x)]
    pen_codes = list(set(pen_codes))
    for pen_code in pen_codes:
        data["pen_codes"] += [pen_info(pen_code)]

    data["count"] = len(data["pen_codes"])
    data["pen_codes"] = sorted(data["pen_codes"], key=lambda x: datetime.strptime(x["meta"].get("created_at", x["meta"]["curr_time"]), "%B %d, %Y, %H:%M:%S").timestamp())
    return data

def pen_info(pen_code):
    data = {
        "pen_code": pen_code,
        "modes": get_modes(pen_code),
        "base": bool(),
        "meta": dict(),
    }
    with open(pen_files[data["modes"][0]]["meta"] % pen_code) as f:
        meta = json.load(f)
    data["meta"] = meta
    data["base"] = meta["step"] == 0 and meta["fork_sim_code"] == pen_code
    return data

def all_payloads(pen_code):
    data = dict()
    mode = get_modes(pen_code)[0]
    for p_name in black_hats:
        payload_file = (pen_files[mode]["root"] % pen_code) + (pen_files["memory"]["payload"] % p_name)
        if not exists(payload_file): continue
        with open(payload_file) as f:
            payload_data = json.load(f)
        for url, items in payload_data.items():
            for idx, payload in enumerate(items["basic"]):
                step = payload["timestamp"]
                items["basic"][idx]["url"] = url
                if step not in data: data[step] = {}
                del items["basic"][idx]["timestamp"]
                data[step][p_name] = items["basic"][idx]
    return data

def next_payload(pen_code, step):
    data = all_payloads(pen_code).get(int(step), dict())
    return data

def all_patches(pen_code):
    data = dict()

    best = dict()
    mode = get_modes(pen_code)[0]
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

    mode = get_modes(pen_code)[0]
    for p_name in white_hats:
        payload_file = (pen_files[mode]["root"] % pen_code) + (pen_files["memory"]["payload"] % p_name)
        if not exists(payload_file): continue
        with open(payload_file) as f:
            patch_data = json.load(f)
        for items in patch_data.values():
            step = items["timestamp"]
            if step not in data: data[step] = {}
            data[step][p_name] = {
                "urls": list(items["successful_data"].keys()),
                "attack_name": list(set([y["attack_name"] for x in items["successful_data"].values() for y in x])),
                "suggestion": items["patch_suggestion"],
                "best": best.get(step, {}).get(p_name, []) != [],
            }
    return data

def all_best_patches(pen_code):
    data = dict()

    for step, items in all_patches(pen_code).items():
        for p_name, patch in items.items():
            if patch["best"] is True:
                if step not in data: data[step] = dict()
                data[step][p_name] = patch

    return data

def next_patch(pen_code, step):
    data = all_patches(pen_code).get(int(step), dict())
    return data

def all_steps(pen_code):
    data = dict()
    mode = get_modes(pen_code)[0]
    if mode == "compressed":
        with open(pen_files[mode]["move"] % pen_code) as f:
            data = json.load(f)
        for step, item in all_payloads(pen_code).items():
            step = str(step)
            for p_name, payload in item.items():
                if p_name not in data[step]: data[step][p_name] = dict()
                data[step][p_name]["payload"] = payload
        for step, item in all_patches(pen_code).items():
            step = str(step)
            for p_name, patch in item.items():
                if p_name not in data[step]: data[step][p_name] = dict()
                data[step][p_name]["patch"] = patch
    else:
        step = 0
        while True:
            step += 1
            try:
                x = next_step(pen_code, step, mode=mode)
                data[str(step)] = x
            except:
                break
    return data

def next_step(pen_code, step, *, mode=None):
    data = dict()
    mode = mode or get_modes(pen_code)[0]
    try:
        if mode == "compressed":
            data = all_steps(pen_code)[str(step)]
        else:  # mode == "forkable":
            with open(pen_files[mode]["move"] % (pen_code, step)) as f:
                data = json.load(f)["persona"]
    except:
        raise Error(f"Step exceeded: {step}", 404)

    for p_name, item in next_payload(pen_code, step).items():
        if p_name not in data: data[p_name] = dict()
        data[p_name]["payload"] = item
    for p_name, item in next_patch(pen_code, step).items():
        if p_name not in data: data[p_name] = dict()
        data[p_name]["patch"] = item
    return data



# Chart Data Functions

def get_charts():
    data = {
        "total": Counter(),
        "pens": get_pen_charts()["data"],
        "urls": get_url_charts()["data"],
        "attacks": get_attack_charts()["data"],
    }

    for x in data["pens"]:
        data["total"] += Counter(x["chart"])

    return data

def get_pen_charts():
    data = {
        "count": 0,
        "data": list(),
    }

    charts = [{"pen_code": p, "chart": get_pen_chart(p)} for p in pen_list()]
    data["data"] = charts
    data["count"] = len(charts)

    return data

def get_pen_chart(pen_code):
    data = {
        "step": pen_info(pen_code)["meta"]["step"],
        "payloads": 0,
        "vulnerabilities": 0,
        "vulnerable_files": 0,
        "patch_suggestion": 0,
        "best_suggestion": 0,
    }

    payloads = all_payloads(pen_code)
    patches = all_patches(pen_code)
    best_patches = all_best_patches(pen_code)

    data["payloads"] = len([x for x in payloads.values()])
    data["vulnerabilities"] = len([x for payload in payloads.values() for x in payload.values() if x["observations"] == "exploit_successful"])
    data["vulnerable_files"] = len(set([y["file_path"] for patch in patches.values() for x in patch.values() for y in x["suggestion"]]))
    data["patch_suggestion"] = len([x for x in patches.values()])
    data["best_suggestion"] = len([x for x in best_patches.values()])

    return data

def get_url_charts():
    data = {
        "count": 0,
        "data": list(),
    }

    init = {
        "payloads": 0,
        "vulnerabilities": 0,
        "patch_suggestion": 0,
        "best_suggestion": 0,
    }

    tmp = dict()
    pen_codes = pen_list()
    for pen_code in pen_codes:
        payloads = all_payloads(pen_code)
        patches = all_patches(pen_code)
        for payload in payloads.values():
            for item in payload.values():
                url = item["url"]
                if url not in tmp: tmp[url] = init.copy()
                tmp[url]["payloads"] += 1
                tmp[url]["vulnerabilities"] += item["observations"] == "exploit_successful"
        for patch in patches.values():
            for item in patch.values():
                for url in item["urls"]:
                    if url not in tmp: tmp[url] = init.copy()
                    tmp[url]["patch_suggestion"] += 1
                    tmp[url]["best_suggestion"] += item["best"]

    data["count"] = len(tmp)
    for url, item in tmp.items():
        data["data"] += [{"url": url, **item}]

    return data

def get_attack_charts():
    data = {
        "count": 0,
        "data": list(),
    }

    init = {
        "payloads": 0,
        "vulnerabilities": 0,
        "patch_suggestion": 0,
        "best_suggestion": 0,
    }

    tmp = dict()
    pen_codes = pen_list()
    for pen_code in pen_codes:
        payloads = all_payloads(pen_code)
        patches = all_patches(pen_code)
        for payload in payloads.values():
            for item in payload.values():
                attack = item["attack_name"]
                if attack not in tmp: tmp[attack] = init.copy()
                tmp[attack]["payloads"] += 1
                tmp[attack]["vulnerabilities"] += item["observations"] == "exploit_successful"
        for patch in patches.values():
            for item in patch.values():
                for attack in item["attack_name"]:
                    if attack not in tmp: tmp[attack] = init.copy()
                    tmp[attack]["patch_suggestion"] += 1
                    tmp[attack]["best_suggestion"] += item["best"]

    data["count"] = len(tmp)
    for attack, item in tmp.items():
        data["data"] += [{"attack_name": attack, **item}]

    return data

def get_attack_chart(attack):
    data = dict()

    attack = attack.replace("_", " ").replace("-", " ")
    for x in get_attack_charts()["data"]:
        if x["attack_name"].lower() == attack.lower():
            del x["attack_name"]
            data = x
            break
    if not data:
        raise Error(f"Not found: attack_name: {attack}", 404)

    return data



# API

def getRunningInfo(request):
    return get_response(running_info)

def getPens(request):
    return get_response(pen_infos)

def getPen(request, pen_code):
    return get_response(pen_info, pen_code)

def getAllSteps(request, pen_code):
    return get_response(all_steps, pen_code)

def getNextStep(request, pen_code, step):
    return get_response(next_step, pen_code, step)

def getAllPayloads(request, pen_code):
    return get_response(all_payloads, pen_code)

def getAllPatches(request, pen_code):
    return get_response(all_patches, pen_code)

def getAllBestPatches(request, pen_code):
    return get_response(all_best_patches, pen_code)

def getCharts(request):
    return get_response(get_charts)

def getPenCharts(request):
    return get_response(get_pen_charts)

def getPenChart(request, pen_code):
    return get_response(get_pen_chart, pen_code)

def getUrlCharts(request):
    return get_response(get_url_charts)

def getAttackCharts(requests):
    return get_response(get_attack_charts)

def getAttackChart(request, attack):
    return get_response(get_attack_chart, attack)
