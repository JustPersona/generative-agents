{% load static %}

let debug = false;
let pause = false;

const fullScreen = false;
const mode = ["forkable", "compressed"].includes("{{ mode }}") ? "{{ mode }}" : "tester";
const canvas_ratio = 8/15;
const tile_width = "{{ tile_width }}" * 1;
const timebox = document.getElementById("game-time-content");
const datetime_options = { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' };
let camera_zoom = 1;
let movement_speed;
let execute_count_max;
let execute_count;

{% if mode != "tester" %}
	const apply_speed = function(speed=2, min=1, max=6) {
		if (!speed || speed < min) speed = min;
		if (speed > max) speed = max;
		if (mode != "compressed") speed = 6;
		const elem = document.querySelector("#speed");
		elem.setAttribute("placeholder", speed);
		elem.value = speed;

		speed = 2 ** (speed - 1);
		execute_count_max = tile_width / speed;
		execute_count = execute_count / (speed / movement_speed);
		movement_speed = speed;
	}

	const formSubmit = function(e) {
		e.preventDefault();
		const form = e.target;
		const step = form.step?.value?.trim();
		const speed = form.speed?.value?.trim() || "";
		location.replace(`{% url 'pen_test' pen_code %}${step}/${speed}`);
	}

	const stepChange = function(elem) {
		let value = elem.value.replace(/[^0-9]/g, '');
		value = Math.min(value, elem.getAttribute("max")*1);
		elem.value = value;
		if (!pause) return;
		document.querySelector(`input#${elem.id == "step_range" ? "curr_step" : "step_range"}`).value = value;

		apply_btn.classList.toggle('d-none', value == elem.placeholder);
		const currStep = elem.placeholder;
		const newStep = value;

		const curr_datetime =  new Date( Date.parse(timebox.placeholder.replace(" at", ",")) + 10000*(newStep - currStep) );
		timebox.value = curr_datetime.toLocaleTimeString("en-US", datetime_options);
	}
{% endif %}

const personaFocus = function(radio) {
	let p_name = radio.id.split("-");
	p_name = p_name[p_name.length-1];
	radio.blur();

	const box = document.querySelector(`#on_screen_det_content-${p_name}`);
	const isActive = !box.classList.contains("d-none");
	document.getElementById("temp_focus").innerHTML = isActive ? "" : p_name;
	document.querySelector("#on_screen_det_content-init").classList.toggle("d-none", !isActive);
	for (let x of box.parentNode.children) x.classList.toggle("d-none", x !== box || isActive);
	radio.checked = !isActive;
}



const pen_test_play = function(container) {
	const static = "{% static '' %}";
	const maze_name = "{{ maze_name }}";

	const map_width = "{{ map.width }}" * 1;
	const map_height = "{{ map.height }}" * 1;
	const sec_per_step = "{{ sec_per_step }}" * 1;

	let max_step = "{{ max_step }}" * 1;
	const player_width = 40;
	const playerDepth = mode === "tester" ? 1 : -1;

	const payloads = {% if mode == "tester" or not payloads %}{}{% else %}{{ payloads | safe }}{% endif %};
	const vuln_imoji = "\u2757\u2757";
	let imoji_bak = "";
	let vuln_imoji_count = 0;
	const vuln_imoji_count_max = 10;



	/*
	  Main resources:
	  https://www.youtube.com/watch?v=cKIG1lKwLeo&t=401s&ab_channel=HongLy
	  For the ground zero code, see the exported files from here:
	  https://codepen.io/mikewesthad/pen/BVeoYP?editors=1111

	  Also worth taking a look:
	  https://www.youtube.com/watch?v=fdXcD9X4NrQ&ab_channel=MorganPage
	  and
	  https://www.youtube.com/watch?v=MR2CvWxOEsw&ab_channel=MattWilber
	 */

	// ###########################################################################
	// PREAMBLE
	// ###########################################################################

	// <step> -- one full loop around all three phases determined by <phase> is
	// a step. We use this to link the steps in the backend.
	let step = "{{ step }}" * 1;
	const pen_code = "{{ pen_code }}";
	const step_size = (sec_per_step || 10) * 1000; // 10 seconds = 10000



	// Phaser 3.0 global settings.
	// Configuration meant to be passed to the main Phaser game instance.
	const canvas_width = fullScreen ? map_width * 32 : Math.max(1100, container.clientWidth);
	const canvas_height = fullScreen ? map_height * 32 : canvas_width * canvas_ratio;
	const config = {
		type: Phaser.AUTO,
		width: canvas_width,
		height: canvas_height,
		parent: container.id,
		pixelArt: true,
		physics: {
			default: "arcade",
			arcade: {
				gravity: {
					y: 0,
				},
			},
		},
		scene: {
			preload: preload,
			create: create,
			update: update,
		},
		scale: {
			// mode: Phaser.Scale.FIT,
		},
	};


	// Creating the game instance and setting up the main Phaser variables that
	// will be used in it.
	const game = new Phaser.Game(config);
	let cursors;
	let player;


	{% if mode == "tester" %}
		const spawn_tile_loc = {};
	{% else %}
		// Persona related variables. This should have the name of the persona as its
		// keys, and the instances of the Persona class as the values.
		// let spawn_tile_loc = {};
		// for (let key in persona_names) {
		// 	spawn_tile_loc[key] = persona_names[key];
		// }
		const spawn_tile_loc = {{ persona_init_pos | safe }};

		let personas = {};
		let speech_bubbles = {};
		let pronunciatios = {};
		let anims_direction;
		let pre_anims_direction_dict = {};

		// <tile_width> is the width of one individual tile (tiles are square)
		// const tile_width = "{{ tile_width }}" * 1;
		// Important: tile_width % movement_speed has to be 0.
		// <movement_speed> determines how fast we move at each upate cylce.
		// const movement_speed = "{{ play_speed }}" * 1;
		apply_speed("{{ speed }}" * 1);

		// <timer_max> determines how frequently our update function will query the
		// frontend server. If it's higher, we wait longer cycles.
		let timer_max = 0;
		let timer = timer_max;

		// <phase> -- there are three phases: "process," "update," and "execute."
		let phase = "update"; // or "update" or "execute"

		// Variables for storing movements that are sent from the backend server.
		let execute_movement;
		// let execute_count_max = tile_width / movement_speed;
		// let execute_count = execute_count_max;
		execute_count = execute_count_max;
		let movement_target = {};
		const all_movement = {{ all_movement | safe }};

		let start_datetime = new Date(Date.parse("{{ start_datetime }}"));
		if (mode != "tester" && start_datetime) {
			timebox.value = start_datetime.toLocaleTimeString("en-US", datetime_options);
		}
	{% endif %}



	const tilesets = {{ map.tilesets | safe }};
	const layers = {{ map.layers | safe }};
	const offsets = {
		"persona": [
			0,
			tile_width/2 - 8,
		],
		"speech_bubble": [
			80,
			-39,
		],
		"pronunciatio": [
			0,
			-1,
		],
	};



	// ###########################################################################
	// ENGINE
	// ###########################################################################

	// Joon: Phaser 3.0 is oriented around "scenes" -- recall how Pokemon plays:
	//       there is the outdoor space, and then there is the indoor space; when
	//       you go inside, you transition to a new "scene" and the outdoor space
	//       basically disappears.
	//       A scene in Phaser has four key methods that are called at different
	//       stages of rendering for different purposes. They are:
	//       init() -> preload() -> create() -> update()
	//           init() is called only once at the very beginning. This is the
	//               initialization function in case that is needed.
	//           preload() is called once and preloads any of the assets
	//           create() is also called once after preloading... creates sprites
	//               and actually displays stuff
	//           update() is called on each frame during the game play

	function preload() {
		// For managing cross origin errors. We need to set this, change AWS
		// CORS settings, and django AWS settings.
		this.load.crossOrigin = '';

		// Loading the necessary images (e.g., the background image, character
		// sprites).
		// Joon: for load.image, the first parameter is simply the key value that
		//       you are passing in. The second parameter should be pointed to the
		//       png file that contains the tileset.
		//       Also IMPORTANT: when you create a tileset in Tiled, always be
		//       sure to check the "embedded" option.
		for (let tileset of tilesets) {
			this.load.image(tileset.name, static + "assets/{{ maze_name }}/visuals/" + tileset.path);
		}


		// Joon: This is the export json file you get from Tiled.
		this.load.tilemapTiledJSON("map", static + "assets/{{ maze_name }}/visuals/{{ maze_name }}.json");

		// An atlas is a way to pack multiple images together into one texture. I'm
		// using it to load all the player animations (walking left, walking right,
		// etc.) in one image. For more info see:
		// https://labs.phaser.io/view.html?src=src/animation/texture%20atlas%20animation.js
		// If you don't use an atlas, you can do the same thing with a spritesheet,
		// see: https://labs.phaser.io/view.html?src=src/animation/single%20sprite%20sheet.js
		// Joon: Technically, I think this guy had the best tutorial for atlas:
		//       https://www.youtube.com/watch?v=fdXcD9X4NrQ&ab_channel=MorganPage
		this.load.atlas(
			"atlas",
			"https://mikewesthad.github.io/phaser-3-tilemap-blog-posts/post-1/assets/atlas/atlas.png",
			"https://mikewesthad.github.io/phaser-3-tilemap-blog-posts/post-1/assets/atlas/atlas.json",
		);

		for (let p_name in spawn_tile_loc) {
			this.load.atlas(
				p_name,
				static + `assets/characters/${p_name}.png`,
				static + "assets/characters/atlas.json",
			);
		}

		this.load.image('speech_bubble', static + "assets/speech_bubble/v3.png");
	}


	function create() {
		const map = this.make.tilemap({ key: "map" });
		// Joon: Logging map is really helpful for debugging here:
		//       console.log(map);

		// The first parameter is the name you gave to the tileset in Tiled and then
		// the key of the tileset image in Phaser's cache (i.e. the name you used in
		// preload)
		// Joon: for the first parameter here, really take a look at the
		//       console.log(map) output. You need to make sure that the name
		//       matches.
		let tileset_group = [];
		for (let tileset of tilesets) {
			tileset_group.push(map.addTilesetImage(tileset.name, tileset.name));
		}

		let layer_group = []
		for (let layer of layers) {
			// The first parameter is the layer name (or index) taken from Tiled, the
			// second parameter is the tileset you set above, and the final two
			// parameters are the x, y coordinate.
			// Joon: The "layer name" that comes as the first parameter value
			//       literally is taken from our Tiled layer name. So to find out what
			//       they are; you actually need to open up tiled and see how you
			//       named things there.
			const layerObj = map.createLayer(layer.name, tileset_group, 0, 0);
			layer_group.push(layerObj);

			// Joon: This is where you want to create a custom field for the tileset
			//       in Tiled. Take a look at this guy's tutorial:
			//       https://www.youtube.com/watch?v=MR2CvWxOEsw&ab_channel=MattWilber
			// collisionsLayer.setCollisionByProperty({ collide: true });
			// By default, everything gets depth sorted on the screen in the order we
			// created things. Here, we want the "Above Player" layer to sit on top of
			// the player, so we explicitly give it a depth. Higher depths will sit on
			// top of lower depth objects.
			// Collisions layer should get a negative depth since we do not want to see
			// it.
			layerObj.visible = layer.visible;
			if (layer.name == "Collisions") {
				layerObj.setCollisionByProperty({ collide: true });
				layerObj.setDepth(playerDepth);
			} else if (layer.name.toLowerCase().startsWith("foreground")) {
				layerObj.setDepth(2);
			}
		}

		// *** SET UP CAMERA ***
		// "player" is to be set as the center of mass for our "camera." We
		// basically create a game character sprite as we would for our personas
		// but we move it to depth -1 and let it pass through the collision map;
		// that is, do not have the following line:
		// this.physics.add.collider(player, collisionsLayer);
		// OLD NOTE: Create a sprite with physics enabled via the physics system.
		// The image  used for the sprite has a bit of whitespace, so I'm using
		// setSize & setOffset to control the size of the player's body.
		// player = this.physics.add.sprite(85*32, 20*32, "atlas", "misa-front");
		player = this.physics.add.sprite(map_width*32/2, map_height*32/2, "atlas", "misa-front"); // center
		player.setDepth(playerDepth);

		// Setting up the camera.
		const camera = this.cameras.main;
		camera.startFollow(player);
		camera.setBounds(0, 0, map.widthInPixels, map.heightInPixels);
		cursors = this.input.keyboard.createCursorKeys();

		// camera zoom minimum
		camera.setZoom(camera_zoom);
		const zoomMin = Math.ceil(Math.max(canvas_width / map.widthInPixels, canvas_height / map.heightInPixels) * 10) / 10;
		document.querySelector("#zoom")?.setAttribute("min", zoomMin);


		// *** SET UP PERSONAS ***
		// We start by creating the game sprite objects.
		for (let i=0; i<Object.keys(spawn_tile_loc).length; i++) {
			let persona_name = Object.keys(spawn_tile_loc)[i];
			let start_pos = [
				spawn_tile_loc[persona_name][0] * tile_width,
				spawn_tile_loc[persona_name][1] * tile_width,
			];

			let new_sprite = this.physics.add.sprite(start_pos[0], start_pos[1], persona_name, "down").setOffset(offsets["persona"][0], offsets["persona"][1]);
			// Scale up the sprite
			new_sprite.displayWidth = player_width;
			new_sprite.scaleY = new_sprite.scaleX;

			// Here, we are creating the persona and its pronunciatio sprites.
			let new_speech_bubble = this.add.image(new_sprite.body.x + offsets["speech_bubble"][0], new_sprite.body.y + offsets["speech_bubble"][1], 'speech_bubble').setDepth(3);
			new_speech_bubble.displayWidth = 140;
			new_speech_bubble.displayHeight = 58;

			let pronunciatios_size = parseFloat(getComputedStyle(container).getPropertyValue("font-size")) * 1.5;
			let pronunciatios_padding = (new_speech_bubble.displayHeight/11*8)/2 - pronunciatios_size/2;
			let new_pronunciatios = this.add.text(
				new_speech_bubble.x - new_speech_bubble.displayWidth/2 + offsets["pronunciatio"][0],
				new_speech_bubble.y - new_speech_bubble.displayHeight/2 + offsets["pronunciatio"][1],
				"🦁", {
					font: `${pronunciatios_size}px monospace`,
					fill: "#000000",
					padding: {
						x: pronunciatios_padding,
						y: pronunciatios_padding,
					},
					border: "solid",
					borderRadius: "10px",
				},
			).setDepth(3);

			personas[persona_name] = new_sprite;
			speech_bubbles[persona_name] = new_speech_bubble;
			pronunciatios[persona_name] = new_pronunciatios;
		}

		// Create the player's walking animations from the texture atlas. These are
		// stored in the global animation manager so any sprite can access them.
		const anims = this.anims;
		for (let i=0; i<Object.keys(spawn_tile_loc).length; i++) {
			let persona_name = Object.keys(spawn_tile_loc)[i];
			let left_walk_name = persona_name + "-left-walk";
			let right_walk_name = persona_name + "-right-walk";
			let down_walk_name = persona_name + "-down-walk";
			let up_walk_name = persona_name + "-up-walk";

			// console.log(persona_name, left_walk_name, "DEUBG")
			anims.create({
				key: left_walk_name,
				frames: anims.generateFrameNames(persona_name, { prefix: "left-walk.", start: 0, end: 3, zeroPad: 3 }),
				frameRate: 4,
				repeat: -1,
			});

			anims.create({
				key: right_walk_name,
				frames: anims.generateFrameNames(persona_name, { prefix: "right-walk.", start: 0, end: 3, zeroPad: 3 }),
				frameRate: 4,
				repeat: -1,
			});

			anims.create({
				key: down_walk_name,
				frames: anims.generateFrameNames(persona_name, { prefix: "down-walk.", start: 0, end: 3, zeroPad: 3 }),
				frameRate: 4,
				repeat: -1,
			});

			anims.create({
				key: up_walk_name,
				frames: anims.generateFrameNames(persona_name, { prefix: "up-walk.", start: 0, end: 3, zeroPad: 3 }),
				frameRate: 4,
				repeat: -1,
			});
		}


		// A range of coordinates that can be moved by the camera
		this.minX = camera.width / 2;
		this.maxX = map.widthInPixels - this.minX;
		this.minY = camera.height / 2;
		this.maxY = map.heightInPixels - this.minY;

		// *** MOVE CAMERA WITH POINTER ***
		// Move the "camera" through pointer moving.
		const pointerPos = {};
		this.input.on("pointerup", function() {
			pointerPos.x = 0;
			pointerPos.y = 0;
		});
		this.input.on("pointermove", function(pointer) {
			if (!pointer.isDown || pointer.button != 0) {
				pointerPos.x = 0;
				pointerPos.y = 0;
				return;
			}
			const {x, y, downX, downY} = pointer;

			const move = {
				x: (pointerPos.x || downX) - x,
				y: (pointerPos.y || downY) - y,
			};

			if (document.getElementById("temp_focus").innerHTML == "") {
				player.body.setVelocity(move.x * 125, move.y * 125);
			}

			pointerPos.x = x;
			pointerPos.y = y;
		});
	}


	function update(time, delta) {
		// *** SETUP PLAY AND PAUSE BUTTON ***
		// let play_context = this;
		// function game_resume() {
		// 	play_context.scene.resume();
		// }
		// play_button.onclick = function(){
		// 	game_resume();
		// };
		// function game_pause() {
		// 	play_context.scene.pause();
		// }
		// pause_button.onclick = function(){
		// 	game_pause();
		// };

		// *** MOVE CAMERA ***
		// This is where we finish up the camera setting we started in the create()
		// function. We set the movement speed of the camera and wire up the keys to
		// map to the actual movement.
		const camera_speed = 400;
		// Stop any previous movement from the last frame
		player.body.setVelocity(0);
		if (document.getElementById("temp_focus").innerHTML == "") {
			if (cursors.left.isDown) {
				player.body.setVelocityX(-camera_speed);
			}
			if (cursors.right.isDown) {
				player.body.setVelocityX(camera_speed);
			}
			if (cursors.up.isDown) {
				player.body.setVelocityY(-camera_speed);
			}
			if (cursors.down.isDown) {
				player.body.setVelocityY(camera_speed);
			}
		}

		// Prevent camera from being out of range
		this.cameras.main.setZoom(camera_zoom || 1);
		if (mode != "tester") {
			const minX = this.minX / camera_zoom;
			const minY = this.minY / camera_zoom;
			const maxX = this.maxX + (this.minX - minX);
			const maxY = this.maxY + (this.minY - minY);
			if (player.x < minX) player.x = minX;
			if (player.y < minY) player.y = minY;
			if (player.x > maxX) player.x = maxX;
			if (player.y > maxY) player.y = maxY;
		}

		let curr_focused_persona = document.getElementById("temp_focus").textContent;
		if (curr_focused_persona != "") {
			player.setPosition(personas[curr_focused_persona].body.x, personas[curr_focused_persona].body.y)
			// document.getElementById("temp_focus").innerHTML = "";
		}

		// Run a separate function for each mode
		if (mode in updates) {
			if (pause === false || (mode == "forkable" && phase != "update")) {
				updates[mode]();
			}
		}
	}



	updates = {
		tester: function() {
			// *** MOVE PERSONAS ***
			// Moving personas take place in three distinct phases: "process," "update,"
			// and "execute." These phases are determined by the value of <phase>.
			// Only one of the three phases is incurred in each update cycle.
			let data = {
				"camera": {
					"maze": maze_name,
					"x": player.body.position.x,
					"y": player.body.position.y,
				},
			}
			post("{% url 'path_tester_update' %}", data);
		},


		compressed: function() {
			// *** MOVING PERSONAS ***
			if (execute_count <= 0) start_datetime = new Date(start_datetime.getTime() + step_size);
			action(all_movement[step], start_datetime);
		},


		forkable: function() {
			// *** MOVE PERSONAS ***
			// Moving personas take place in three distinct phases: "process," "update,"
			// and "execute." These phases are determined by the value of <phase>.
			// Only one of the three phases is incurred in each update cycle.
			if (phase == "process") {
				// "process" takes all current locations of the personas and send them to
				// the frontend server in a json form. Here, we first create the json
				// file that records all persona locations:
				let data = {
					"step": step,
					"pen_code": pen_code,
					"environment": {},
				}
				for (let i=0; i<Object.keys(personas).length; i++) {
					let persona_name_os = Object.keys(personas)[i];
					let persona_name = persona_name_os.replace(/_/g, " ");
					data["environment"][persona_name] = {
						"maze": maze_name,
						"x": Math.ceil((personas[persona_name_os].body.position.x) / tile_width),
						"y": Math.ceil((personas[persona_name_os].body.position.y) / tile_width),
					}
				}
				post("{% url 'process_environment' %}", data);

				// Finally, we update the phase variable to start the "udpate" process.
				// Now that we sent all persona locations to the backend server, we need
				// to wait until the backend determines what the personas will do next.
				phase = "update";
			} else if (phase == "update") {
				// Update is where we * wait * for the backend server to finish
				// computing about what the personas will do next given their current
				// situation.
				// We do this by continuously asking the backend server if it is ready.
				// The backend server is ready when it returns a json that has a key-val
				// pair with "<move>": true.
				// Note that we do not want to overburden the backend too much by
				// over-querying; so, we have a timer set so we only query it once every
				// timer_max cycles.
				if (timer <= 0) {
					const data = {
						"step": step,
						"pen_code": pen_code,
					}
					post("{% url 'update_environment' %}", data, function(xhr) {
						if (JSON.parse(xhr.responseText)["<step>"] == step) {
							execute_movement = JSON.parse(xhr.responseText)
							phase = "execute";
						}
						timer = timer_max;
					});
				}
				timer -= 1;
			} else { // phase == execute
				// This is where we actually move the personas in the visual world. Each
				// backend computation in execute_movement moves each persona by one tile
				// (or some personas might not move if they choose not to).
				// The execute_count_max is computed by tile_width/movement_speed, which
				// defines a one step sequence in this world.
				let curr_time = new Date(execute_movement["meta"]["curr_time"]);
				action(execute_movement["persona"], curr_time);
			}
		},
	};



	const setPronunciatio_content = function(curr_persona_name_os, pronunciatio_content) {
		// This is what gives the pronunciatio balloon the name initials. We
		// use regex to extract the initials of the personas.
		// E.g., "Dolores Murphy" -> "DM"
		let rgx = new RegExp(/(\p{L}{1})\p{L}+/, 'gu');
		let initials = [...curr_persona_name_os.matchAll(rgx)] || [];
		initials = (
			(initials.shift()?.[1] || '') + (initials.pop()?.[1] || '')
		).toUpperCase();

		pronunciatios[curr_persona_name_os].setText(initials + ": " + pronunciatio_content);
		document.getElementById("quick_emoji-" + curr_persona_name_os).innerHTML = pronunciatio_content;
	}


	const action = function(movements, curr_time) {
		if (!movements) return;

		if (curr_time) {
			const time = curr_time.toLocaleTimeString("en-US", datetime_options);
			timebox.placeholder = time;
			timebox.value = time;
		}
		for (let i=0; i<Object.keys(personas).length; i++) {
			let curr_persona_name_os = Object.keys(personas)[i];
			let curr_persona_name = curr_persona_name_os.replace(/_/g, " ");
			let curr_persona = personas[curr_persona_name_os];
			let curr_speech_bubble = speech_bubbles[curr_persona_name_os];
			let curr_pronunciatio = pronunciatios[curr_persona_name_os];

			let p_movement = movements[curr_persona_name];
			if (p_movement) {
				if (execute_count == execute_count_max) {
					let curr_x = p_movement["movement"][0];
					let curr_y = p_movement["movement"][1];
					movement_target[curr_persona_name_os] = [curr_x * tile_width, curr_y * tile_width];

					// Updating the status of each personas
					// setText(p_movement, curr_persona_name_os);
					let pronunciatio_content = p_movement["pronunciatio"];
					let description_content = p_movement["description"];
					let chat_content_raw = p_movement["chat"];

					setPronunciatio_content(curr_persona_name_os, pronunciatio_content);

					let chat_content = "";
					if (chat_content_raw != null) {
						for (let j=0; j<chat_content_raw.length; j++) {
							chat_content += chat_content_raw[j][0] + ": " + chat_content_raw[j][1] + "<br>"
						}
					} else {
						chat_content = "<em>None at the moment</em>"
					}

					// Filling in the action description.
					document.getElementById("current_action__" + curr_persona_name_os).innerHTML = description_content.split("@")[0];
					document.getElementById("target_address__" + curr_persona_name_os).innerHTML = description_content.split("@")[1];
					document.getElementById("chat__" + curr_persona_name_os).innerHTML = chat_content;
				}

				if (execute_count > 0) {
					if (!animation.start(curr_persona, curr_speech_bubble, curr_pronunciatio, curr_persona_name_os) && mode != "compressed") {
						animation.stop(curr_persona, curr_persona_name_os);
					};
				} else if (mode != "compressed") {
					move_personas();
					phase = "process";
				}
			} else {
				animation.stop(curr_persona, curr_persona_name_os);
			}
		}

		if (execute_count <= 0) {
			setPayloadByStep(movements["Black Hacker"]?.["pronunciatio"]);
		}

		if (mode == "compressed" && execute_count <= 0) {
			move_personas();
		}

		execute_count -= 1;
	}


	const move_personas = function() {
		// Once we are done moving the personas, we move on to the "process"
		// stage where we will send the current locations of all personas at the
		// end of the movemments to the frontend server, and then the backend.
		if (debug) console.log(step, personas)
		for (let i=0; i<Object.keys(personas).length; i++) {
			let curr_persona_name_os = Object.keys(personas)[i];
			let curr_persona = personas[curr_persona_name_os];
			curr_persona.body.x = movement_target[curr_persona_name_os][0];
			curr_persona.body.y = movement_target[curr_persona_name_os][1];
		}
		execute_count = execute_count_max + 1;
		step = step + 1;

		if (mode == "compressed" && max_step < step) return;
		max_step = Math.max(max_step, step);
		for (let x of document.querySelectorAll("#curr_step, #step_range")) {
			x.value = step;
			x.placeholder = step;
			x.setAttribute("max", max_step);
		}
	}


	const animation = {
		start: function(curr_persona, curr_speech_bubble, curr_pronunciatio, p_name_os) {
			let anims_direction;
			if (curr_persona.body.x < movement_target[p_name_os][0]) {
				anims_direction = "right";
			} else if (curr_persona.body.x > movement_target[p_name_os][0]) {
				anims_direction = "left";
			} else if (curr_persona.body.y < movement_target[p_name_os][1]) {
				anims_direction = "down";
			} else if (curr_persona.body.y > movement_target[p_name_os][1]) {
				anims_direction = "up";
			} else {
				return;
			}

			let isX = ["right", "left"].includes(anims_direction);
			let isPlus = ["right", "down"].includes(anims_direction);
			curr_persona.body[isX ? "x" : "y"] += movement_speed * (isPlus ? 1 : -1);

			curr_speech_bubble.x = curr_persona.body.x + offsets["speech_bubble"][0];
			curr_speech_bubble.y = curr_persona.body.y + offsets["speech_bubble"][1];
			curr_pronunciatio.x = curr_speech_bubble.x - curr_speech_bubble.displayWidth/2 + offsets["pronunciatio"][0];
			curr_pronunciatio.y = curr_speech_bubble.y - curr_speech_bubble.displayHeight/2 + offsets["pronunciatio"][1];

			pre_anims_direction_dict[p_name_os] = anims_direction;
			curr_persona.anims.play(`${p_name_os}-${anims_direction}-walk`, true);
		},
		stop: function(curr_persona, p_name_os) {
			curr_persona.anims.stop();

			// If we were moving, pick an idle frame to use
			curr_persona.setTexture(p_name_os, pre_anims_direction_dict[p_name_os]);
		}
	}

	const setPayloadByStep = function(pronunciatio_content) {
		const data = payloads[step];
		const input = document.querySelector("#curr_payload");
		const isVuln = data?.observations == "exploit_successful";
		vuln_imoji_count = isVuln ? vuln_imoji_count_max : Math.max(vuln_imoji_count-1, -1);

		input.value = data?.payload || "-";
		input.classList.toggle("text-danger", isVuln);
		input.classList.toggle("focus", isVuln);

		imoji_bak = pronunciatio_content || imoji_bak;
		if (vuln_imoji_count != -1) setPronunciatio_content("Black_Hacker", vuln_imoji_count != 0 ? vuln_imoji : imoji_bak);
		insertPayloadTable(document.querySelector("table"), {url: data?.url, data, reverse: true});
	}

	for (let i=1; i<step; i++) {
		const data = payloads[i];
		insertPayloadTable(document.querySelector("table"), {url: data?.url, data, reverse: true});
	}

	return game;
}



const gameContainer = document.querySelector("#game-container");
const game = pen_test_play(gameContainer);
const canvas_resizing = function(size) {
	const canvas = gameContainer.querySelector("canvas");
	if (!canvas) return;

	const canvas_width = typeof size === "number" ? size : gameContainer.clientWidth;
	const canvas_height = canvas_width * canvas_ratio;
	canvas.style.width = canvas_width + "px";
	canvas.style.height = canvas_height + "px";
}
window.addEventListener("DOMContentLoaded", canvas_resizing);
window.addEventListener("resize", canvas_resizing);

window.addEventListener("DOMContentLoaded", function() {
	document.querySelector("#on_screen_det_trigger-Isabella_Rodriguez")?.click();
});