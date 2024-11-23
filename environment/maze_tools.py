#!/usr/bin/env python3

import os, json, csv, pydoc


# Custom Functions
class Ville:
    def __init__(self, maze_name=None):
        self.maze_name = maze_name
        if self.maze_name is None:
            self.maze_name = input("maze_name (Default: the_ville) : ") or "the_ville"
        self.frontend_dir = os.path.abspath(os.path.join(__file__, "..", "frontend_server"))
        self.map_dir = os.path.join(self.frontend_dir, "static_dirs", "assets", self.maze_name)
        self.matrix_dir = os.path.join(self.map_dir, "matrix")
        self.json_file = os.path.join(self.map_dir, "visuals", self.maze_name + ".json")

        if not os.path.isfile(self.json_file):
            raise FileNotFoundError(f"{maze_name}.json file not found")
        with open(self.json_file, "r") as f:
            self.meta = json.load(f)
        self.layers = self.meta["layers"]
        self.height = int(self.meta["height"])
        self.width = int(self.meta["width"])
        self.tile_size = int(self.meta["tilewidth"])

    # Select and run a function
    def run(self, key="", *args, **kwargs):
        keys = sorted(filter(lambda x: not x.startswith("_"), self.__dir__() - self.__dict__.keys() - {"run"}))
        if not key:
            print("List of Functions:")
            for i, val in enumerate(keys):
                print(f"{i+1:>4}. {val}")
                for line in pydoc.render_doc(self.__getattribute__(val), 'Help on %s').split("\n"):
                    if line.startswith("    "):
                        print(f"        {line.strip()}")
                print()
            print("   0. Exit")
            while not key.strip():
                key = input("Select: ").strip()
                if key.lower() in ["0", "exit"]:
                    print("Bye")
                    return
            try:
                num = int(key)
                if num < 1 or len(keys) < num:
                    raise ValueError(f"{num} is Nonexistent number")
                key = keys[num-1]
            except:
                pass

        if key not in keys:
            raise AttributeError(f"{key} function not found")
        self.__getattribute__(key)()



    def maze_save(self):
        """
        Create maze_meta_info.json, maze/*.csv files in
        environment/frontend_server/static_dirs/assets/maze_name/matrix
        using file maze_name/visual/maze_name.json

        maze_name.json file can be obtained by export from application "Tiled"
        """
        save_dir = os.path.join(self.matrix_dir, "maze")
        save_files = {
            "Collisions": "collision_maze.csv",
            "Object Interaction Blocks": "game_object_maze.csv",
            "Arena Blocks": "arena_maze.csv",
            "Sector Blocks": "sector_maze.csv",
            "Spawning Blocks": "spawning_location_maze.csv",
        }

        with open(f"{self.matrix_dir}/maze_meta_info.json", "w") as f:
            f.write(json.dumps({
                "world_name": self.maze_name.replace("_", " "),
                "maze_width": self.width,
                "maze_height": self.height,
                "sq_tile_size": self.tile_size,
                "special_constraint": "",
            }, indent=2))

        for layer in self.layers:
            layer_name = layer["name"]
            if layer_name not in save_files.keys():
                continue
            save_file = save_files[layer_name]
            layer_data = layer["data"]
            data = str(layer_data)[1:-1]
            with open(f"{save_dir}/{save_file}", 'w') as f:
                f.write(data)



    def find_spawn_pos(self):
        """
        Find and display the spawn position in file
        environment/frontend_server/static_dirs/assets/maze_name/visual/maze_name.json
        The description of the tile laid at that position is get
        from the maze_name/matrix/maze/spawning_location_maze.csv file and display it.
        """
        csv_file = os.path.join(self.matrix_dir, "special_blocks", "spawning_location_blocks.csv")
        with open(csv_file, "r") as f:
            csv_data = csv.reader(f, delimiter=",")
            data = {int(x[0]): x for x in csv_data}

        for layer in self.layers:
            if layer["name"] != "Spawning Blocks": continue
            for i, tile in enumerate(layer["data"]):
                if tile != 0:
                    y, x = divmod(i, self.width)
                    print(f"{x:>3}, {y:<3}: {','.join(data.get(tile))}")



    def all_spatial_save(self):
        """
        Find all game objects and save them to spatial_memory.json through the file
        environment/frontend_server/static_dirs/assets/maze_name/visual/maze_name.json
        """
        block_dir = os.path.join(self.matrix_dir, "special_blocks")
        blocks = {
            "Object Interaction Blocks": "game_object_blocks.csv",
            "Arena Blocks": "arena_blocks.csv",
            "Sector Blocks": "sector_blocks.csv",
        }
        for key, block in blocks.items():
            with open(f"{block_dir}/{block}") as f:
                data = list(map(lambda x: x.strip().split(","), f.readlines()))
                data = {d[0]: list(map(lambda x: x.strip(), d[1:])) for d in data}
            blocks[key] = data
        layers = {layer["name"]: layer["data"] for layer in self.layers if layer["name"] in blocks}

        output = {}
        ville_name = list(blocks["Sector Blocks"].values())[0][0]
        for idx, tile_id in enumerate(layers["Object Interaction Blocks"]):
            if not tile_id: continue
            ls = [blocks["Sector Blocks"][str(layers["Sector Blocks"][idx])][-1]]
            ls += [blocks["Arena Blocks"][str(layers["Arena Blocks"][idx])][-1]]
            ls += [blocks["Object Interaction Blocks"][str(tile_id)][-1]]
            if ls[0] not in output: output[ls[0]] = {}
            if ls[1] not in output[ls[0]]: output[ls[0]][ls[1]] = []
            if ls[2] not in output[ls[0]][ls[1]]: output[ls[0]][ls[1]] += [ls[2]]
        output = {ville_name: output}
        with open("./spatial_memory.json", "w") as f:
            json.dump(output, f, indent=2)



if __name__ == "__main__":
    import sys
    ville = Ville(None if len(sys.argv) == 1 else sys.argv[1])
    ville.run(*sys.argv[2:])
