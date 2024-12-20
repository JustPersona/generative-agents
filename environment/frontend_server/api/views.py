import json
import traceback
from os import listdir
from os.path import exists
from collections import Counter
from datetime import datetime, timedelta
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
        ["/api/pens", "List of pen_codes with meta info"],
        ["/api/pens/:pen_code", "Metadata of :pen_code"],
        ["/api/pens/:pen_code/spawn", "Spawn position of all personas of :pen_code"],
        ["/api/pens/:pen_code/:step", "What to do when :step. All steps If :step is -1"],
        ["/api/pens/:pen_code/datas/:step", "Generated datas when :step of :pen_code. All datas if step is skip"],
        ["/api/pens/:pen_code/movements/:step", "Movements when :step of :pen_code. All movements if step is skip"],
        ["/api/pens/:pen_code/pronunciation/:step", "Pronunciation when :step of :pen_code. All pronunciation if step is skip"],
        ["/api/pens/:pen_code/descriptions/:step", "Descriptions when :step of :pen_code. All descriptions if step is skip"],
        ["/api/pens/:pen_code/chats/:step", "Chats when :step of :pen_code. All chats if step is skip"],
        ["/api/pens/:pen_code/payloads/:step", "Payloads when :step of :pen_code. All payloads if step is skip"],
        ["/api/pens/:pen_code/vulnerabilities/:step", "Vulnerabilities when :step of :pen_code. All vulnerabilities if step is skip"],
        ["/api/pens/:pen_code/patches/:step", "Patches when :step of :pen_code. All patches if step is skip"],
        ["/api/pens/:pen_code/best/:step", "Selection patches when :step of :pen_code. All selection patches if step is skip"],
        ["/api/pens/:pen_code/files", "List of vulnerable files of :pen_code."],
        ["/api/charts", "All Charts"],
        ["/api/charts/pens", "Chart data by pen_codes"],
        ["/api/charts/pens/:pen_code", "chart data of :pen_code"],
        ["/api/charts/urls", "Chart data by URLs"],
        ["/api/charts/attack", "Chart data by Attacks"],
        ["/api/charts/attack/:attack_name", "Chart data of :attack_name"],
    ]
    data["help"] = [{"path": p, "response": d} for p, d in paths]
    return JsonResponse(data)

class Error(Exception):
    def __init__(self, message, status):
        super().__init__({
            "message": message,
            "status": status,
        }, status)

def get_json(fn, *args, **kwargs):
    data = dict()
    status = kwargs.get("status", 200)
    try:
        data = fn(*args, **kwargs)
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
    return data, status, 200 <= status < 300

def get_response(*args, **kwargs):
    data, status, ok = get_json(*args, **kwargs)
    return JsonResponse(data, status=status)



# Pen Info Functions

def get_laststep(pen_code):
    step = None

    mode = get_modes(pen_code)[0]
    if mode == "compressed":
        with open(pen_files[mode]["meta"] % pen_code) as f:
            step = json.load(f)["step"]
    else:
        step = sorted(map(lambda x: int(x.split(".json")[0]), listdir(f"{pen_files[mode]["root"]}/environment/" % pen_code)))[-1]
    return step

def get_running_info():
    data = {
        "running": False,
        "pen_code": None,
        "start_step": None,
        "current_step": None,
    }

    pen_code = None
    start_step = None
    if exists(pen_files["temp"]["code"]):
        with open(pen_files["temp"]["code"]) as f:
            pen_code = json.load(f).get("sim_code")
    if exists(pen_files["temp"]["step"]):
        with open(pen_files["temp"]["step"]) as f:
            start_step = json.load(f).get("step")

    if pen_code and start_step:
        data["running"] = True
        data["pen_code"] = pen_code
        data["start_step"] = start_step
        data["current_step"] = get_laststep(pen_code)
    return data

def get_mode(pen_code):
    return get_modes(pen_code)[0]

def get_modes(pen_code):
    data = list()
    for x in ["compressed", "forkable"]:
        if exists(pen_files[x]["meta"] % pen_code):
            data += [x]
    if len(data) == 0:
        raise Error(f"Not found: pen_code: {pen_code}", 404)
    return data

def pen_list():
    return [p["pen_code"] for p in get_pens()["pen_codes"]]

def get_pens():
    data = {
        "count": 0,
        "pen_codes": list(),
    }

    pen_codes = [x for x in listdir("compressed_storage") if exists(pen_files["compressed"]["meta"] % x)]
    pen_codes += [x for x in listdir("storage") if exists(pen_files["forkable"]["meta"] % x)]
    pen_codes = map(lambda pen_code: get_pen(pen_code), set(pen_codes))

    data["pen_codes"] = sorted(pen_codes, key=lambda x: datetime.strptime(x["meta"].get("created_at", x["meta"]["curr_time"]), "%B %d, %Y, %H:%M:%S").timestamp())
    data["count"] = len(data["pen_codes"])
    return data

def get_pen(pen_code):
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

def get_persona_names(pen_code):
    return get_pen(pen_code)["meta"]["persona_names"]

def get_all_spawns(pen_code):
    data = dict()
    mode = get_modes(pen_code)[0]
    if mode == "compressed":
        with open(pen_files[mode]["move"] % pen_code) as f:
            data = json.load(f)["0"]
        data = {p_name: items["movement"] for p_name, items in data.items()}
    else:
        with open(pen_files[mode]["env"] % (pen_code, 0)) as f:
            data = json.load(f)
        for p_name, items in data.items():
            data[p_name] = [items["x"], items["y"]]
    return data

def get_all_steps(pen_code):
    data = dict()
    mode = get_modes(pen_code)[0]
    if mode == "compressed":
        with open(pen_files[mode]["move"] % pen_code) as f:
            data = json.load(f)
    else:
        step = -1
        while True:
            step += 1
            try:
                x = get_next_step(pen_code, step, mode=mode)
                data[str(step)] = x
            except:
                break
        data = drop_duplication(data)
    return data

def get_next_step(pen_code, step, *, mode=None):
    data = dict()
    mode = mode or get_modes(pen_code)[0]
    try:
        if mode == "compressed":
            data = fill_all_steps(get_all_steps(pen_code))[str(step)]
        else:  # mode == "forkable":
            with open(pen_files[mode]["move"] % (pen_code, step)) as f:
                data = json.load(f)["persona"]
    except:
        raise Error(f"Step exceeded: {step}", 404)
    return data

def drop_duplication(data):
    last_data = dict()
    for step, items in data.items():
        tmp = items.copy()
        for p_name, item in tmp.items():
            if p_name in last_data and last_data[p_name] == item:
                del data[step][p_name]
            else:
                last_data[p_name] = item
    return data

def fill_all_steps(data):
    last_data = dict()
    personas = list(data.values())[0].keys()
    for step, items in data.items():
        for p_name in personas:
            item = items.get(p_name) or last_data.get(p_name)
            data[step][p_name] = item
            last_data[p_name] = item
    return data

def filter_movement(data, key):
    return drop_duplication({k: {p_name: v2[key] for p_name, v2 in v.items()} for k, v in data.items()})

def init_all_step(pen_code):
    data = dict()
    meta = get_pen(pen_code)
    last_step = meta["meta"]["step"]
    personas = get_persona_names(pen_code)

    data = {str(step): dict() for step in range(last_step)}
    if data:
        data["0"] = {p_name: None for p_name in personas}
    return data

def fill_persona_data(pen_code, data):
    personas = get_persona_names(pen_code)
    for step, items in data.items():
        for p_name in personas:
            if p_name not in items:
                data[step][p_name] = None
    return data

def get_datas(pen_code, step):
    if step is None:
        return get_all_datas(pen_code)
    else:
        return get_next_datas(pen_code, step)

def get_movements(pen_code, step=None):
    if step is None:
        return get_all_movements(pen_code)
    else:
        return get_next_movements(pen_code, step)

def get_pronunciation(pen_code, step=None):
    if step is None:
        return get_all_pronunciation(pen_code)
    else:
        return get_next_pronunciation(pen_code, step)

def get_description(pen_code, step=None):
    if step is None:
        return get_all_description(pen_code)
    else:
        return get_next_description(pen_code, step)

def get_chats(pen_code, step=None):
    if step is None:
        return get_all_chats(pen_code)
    else:
        return get_next_chats(pen_code, step)

def get_payloads(pen_code, step=None):
    if step is None:
        return get_all_payloads(pen_code)
    else:
        return get_next_payloads(pen_code, step)

def get_vulnerabilities(pen_code, step=None):
    if step is None:
        return get_all_vulnerabilities(pen_code)
    else:
        return get_next_vulnerabilities(pen_code, step)

def get_patches(pen_code, step=None):
    if step is None:
        return get_all_patches(pen_code)
    else:
        return get_next_patches(pen_code, step)

def get_best(pen_code, step=None):
    if step is None:
        return get_all_best(pen_code)
    else:
        return get_next_best(pen_code, step)

def get_all_movements(pen_code):
    data = get_all_steps(pen_code)
    return filter_movement(data, "movement")

def get_next_movements(pen_code, step):
    data = get_next_step(pen_code, step)
    return filter_movement({"data": data}, "movement")["data"]

def get_all_pronunciation(pen_code):
    data = get_all_steps(pen_code)
    return filter_movement(data, "pronunciatio")

def get_next_pronunciation(pen_code, step):
    data = get_next_step(pen_code, step)
    return filter_movement({"data": data}, "pronunciatio")["data"]

def get_all_description(pen_code):
    data = get_all_steps(pen_code)
    return filter_movement(data, "description")

def get_next_description(pen_code, step):
    data = get_next_step(pen_code, step)
    return filter_movement({"data": data}, "description")["data"]

def get_all_chats(pen_code):
    data = get_all_steps(pen_code)
    return filter_movement(data, "chat")

def get_next_chats(pen_code, step):
    data = get_next_step(pen_code, step)
    return filter_movement({"data": data}, "chat")["data"]

def get_all_payloads(pen_code):
    data = init_all_step(pen_code)
    mode = get_modes(pen_code)[0]

    for p_name in black_hats:
        payload_file = (pen_files[mode]["root"] % pen_code) + (pen_files["memory"]["payload"] % p_name)
        if not exists(payload_file): continue
        with open(payload_file) as f:
            payload_data = json.load(f)
        for url, items in payload_data.items():
            for idx, payload in enumerate(items["basic"]):
                step = str(payload["timestamp"])
                items["basic"][idx]["url"] = url
                del items["basic"][idx]["timestamp"]
                data[step][p_name] = items["basic"][idx]
    data = {key: value for key, value in sorted(data.items(), key=lambda x: int(x[0])) }
    return data

def get_all_datas(pen_code):
    data = get_all_steps(pen_code)
    payloads = get_all_payloads(pen_code)
    patches = get_all_patches(pen_code)
    personas = get_persona_names(pen_code)

    last_data = dict()
    for step, items in data.items():
        for p_name in personas:
            if p_name in items or p_name in payloads[step] or p_name in patches[step]:
                tmp = items.get(p_name) or last_data[p_name].copy()
                tmp["payload"] = payloads[step].get(p_name)
                tmp["patch"] = patches[step].get(p_name)
                last_data[p_name] = tmp
                data[step][p_name] = tmp
    return data

def get_next_datas(pen_code, step):
    data = dict()
    all_data = get_all_datas(pen_code)
    personas = get_persona_names(pen_code)
    if step not in all_data:
        raise Error(f"Step exceeded: {step}", 404)
    for idx in range(int(step), -1, -1):
        if len(data) == len(personas): break
        idx = str(idx)
        for p_name in personas:
            if p_name in data: continue
            if p_name not in all_data[idx]: continue
            data[p_name] = all_data[idx][p_name]
            data[p_name]["payload"] = None
            data[p_name]["patch"] = None
    return data

def get_next_data(pen_code, step, type):
    match type:
        case "payloads":
            data = get_all_payloads(pen_code)
        case "vulnerabilities":
            data = get_all_vulnerabilities(pen_code)
        case "patches":
            data = get_all_patches(pen_code)
        case "best":
            data = get_all_best(pen_code)
    if step not in data:
        raise Error(f"Step exceeded: {step}", 404)
    return data.get(step, {})

def get_next_payloads(pen_code, step):
    data = get_next_data(pen_code, step, "payloads")
    return fill_persona_data(pen_code, {"data": data})["data"]

def get_all_vulnerabilities(pen_code):
    data = init_all_step(pen_code)
    payload_data = get_all_payloads(pen_code)
    for step, items in payload_data.items():
        for p_name, payload in items.items():
            if payload and payload["observations"] == "exploit_successful":
                data[str(step)][p_name] = payload
    return data

def get_next_vulnerabilities(pen_code, step):
    data = get_next_data(pen_code, step, "vulnerabilities")
    return fill_persona_data(pen_code, {"data": data})["data"]

def get_all_patches(pen_code):
    data = init_all_step(pen_code)
    best = dict()

    mode = get_modes(pen_code)[0]
    for best_data in get_all_best(pen_code).values():
        for item in best_data.values():
            if not item: continue
            step = str(item["best_patch"]["step"])
            p_name = item["best_patch"]["proposer"]
            if step not in best: best[step] = dict()
            if p_name not in best[step]: best[step][p_name] = list()
            best[step][p_name] += [item["reason"]]
    for p_name in white_hats:
        payload_file = (pen_files[mode]["root"] % pen_code) + (pen_files["memory"]["payload"] % p_name)
        if not exists(payload_file): continue
        with open(payload_file) as f:
            patch_data = json.load(f)
        for items in patch_data.values():
            step = str(items["timestamp"])
            best_reason = best.get(step, {}).get(p_name, [])
            data[step][p_name] = {
                "urls": list(items["successful_data"].keys()),
                "attack_name": list(set([y["attack_name"] for x in items["successful_data"].values() for y in x])),
                "suggestion": items["patch_suggestion"],
                "best": best_reason != [],
                "best_reason": best_reason,
            }
    data = {key: value for key, value in sorted(data.items(), key=lambda x: int(x[0])) }
    return data

def get_next_patches(pen_code, step):
    data = get_next_data(pen_code, step, "patches")
    return fill_persona_data(pen_code, {"data": data})["data"]

def get_all_best(pen_code):
    data = init_all_step(pen_code)
    mode = get_modes(pen_code)[0]
    for p_name in server_owners:
        payload_file = (pen_files[mode]["root"] % pen_code) + (pen_files["memory"]["payload"] % p_name)
        if not exists(payload_file): continue
        with open(payload_file) as f:
            patch_data = json.load(f)
        for items in patch_data.values():
            step = str(items["timestamp"])
            items["best_patch"]["step"] = items["best_patch"]["timestamp"]
            del items["best_patch"]["timestamp"]
            data[step][p_name] = {
                "best_patch": items["best_patch"],
                "reason": items["reason"],
            }
    return data

def get_next_best(pen_code, step):
    data = get_next_data(pen_code, step, "best")
    return fill_persona_data(pen_code, {"data": data})["data"]

def get_vulnerable_files(pen_code):
    data = {
        "count": 0,
        "files": list(),
    }
    tmp = {item["file_path"]: item["vulnerable_file_code"] for x in get_all_patches(pen_code).values() for y in x.values() if y for item in y["suggestion"]}
    for k, v in tmp.items():
        data["count"] += 1
        data["files"] += [{
            "file_path": k,
            "vulnerable_file_code": v,
        }]
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

    for pen in pen_list():
        try:
            x = get_pen_chart(pen)
            data["data"] += [{
                "pen_code": pen,
                "chart": x,
            }]
        except:
            pass
    data["count"] = len(data["data"])

    return data

def get_pen_chart(pen_code):
    meta = get_pen(pen_code)["meta"]
    data = {
        "step": meta["step"],
        "payloads": 0,
        "vulnerabilities": 0,
        "vulnerable_files": 0,
        "patch_suggestion": 0,
        "best_suggestion": 0,
        "patches_applied": meta.get("patches_applied", 0),
    }

    data["payloads"] = len([y for x in get_all_payloads(pen_code).values() for y in x.values() if y])
    data["vulnerabilities"] = len([y for x in get_all_vulnerabilities(pen_code).values() for y in x.values() if y])
    data["patch_suggestion"] = len([y for x in get_all_patches(pen_code).values() for y in x.values() if y])
    data["best_suggestion"] = len([y for x in get_all_best(pen_code).values() for y in x.values() if y])
    data["vulnerable_files"] = get_vulnerable_files(pen_code)["count"]

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
        if get_pen(pen_code)["base"]: continue
        payloads = get_all_payloads(pen_code)
        patches = get_all_patches(pen_code)
        for payload in payloads.values():
            for item in payload.values():
                if not item: continue
                url = item["url"]
                if url not in tmp: tmp[url] = init.copy()
                tmp[url]["payloads"] += 1
                tmp[url]["vulnerabilities"] += item["observations"] == "exploit_successful"
        for patch in patches.values():
            for item in patch.values():
                if not item: continue
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
        payloads = get_all_payloads(pen_code)
        patches = get_all_patches(pen_code)
        for payload in payloads.values():
            for item in payload.values():
                if not item: continue
                attack = item["attack_name"]
                if attack not in tmp: tmp[attack] = init.copy()
                tmp[attack]["payloads"] += 1
                tmp[attack]["vulnerabilities"] += item["observations"] == "exploit_successful"
        for patch in patches.values():
            for item in patch.values():
                if not item: continue
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
    return get_response(get_running_info)

def getPens(request):
    return get_response(get_pens)

def getPen(request, pen_code):
    return get_response(get_pen, pen_code)

def getDatas(request, pen_code, step=None):
    return get_response(get_datas, pen_code, step)

def getAllSpawns(request, pen_code):
    return get_response(get_all_spawns, pen_code)

def getAllSteps(request, pen_code):
    return get_response(get_all_steps, pen_code)

def getNextStep(request, pen_code, step):
    return get_response(get_next_step, pen_code, step)

def getMovements(request, pen_code, step=None):
    return get_response(get_movements, pen_code, step)

def getPronunciation(request, pen_code, step=None):
    return get_response(get_pronunciation, pen_code, step)

def getDescriptions(request, pen_code, step=None):
    return get_response(get_description, pen_code, step)

def getChats(request, pen_code, step=None):
    return get_response(get_chats, pen_code, step)

def getPayloads(request, pen_code, step=None):
    return get_response(get_payloads, pen_code, step)

def getVulnerabilities(request, pen_code, step=None):
    return get_response(get_vulnerabilities, pen_code, step)

def getPatches(request, pen_code, step=None):
    return get_response(get_patches, pen_code, step)

def getBest(request, pen_code, step=None):
    return get_response(get_best, pen_code, step)

def getVulnerableFiles(request, pen_code):
    return get_response(get_vulnerable_files, pen_code)

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
