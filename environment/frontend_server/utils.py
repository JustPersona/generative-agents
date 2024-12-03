black_hats = ["Beom Jun Choi", "Bo Ram Jung"]
white_hats = ["Won Hee Park", "Woo Jin Lee"]
server_owners = ["Seo Yeon Kim"]
work_areas = ["computer desk", "control screen"]

pen_files = {
    "memory": {
        "root": "/personas/%s/bootstrap_memory",
        "payload": "/personas/%s/bootstrap_memory/payload.json",
        "scratch": "/personas/%s/bootstrap_memory/scratch.json",
        "spatial": "/personas/%s/bootstrap_memory/spatial_memory.json",
        "associative": "/personas/%s/bootstrap_memory/associative_memory/nodes.json",
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
        "root": "static/assets/%s/maze",
        "visuals": "static/assets/%s/visuals/%s.json",
    },
}
