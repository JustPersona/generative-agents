# Generative Agents: Interactive Simulacra of Human Behavior

프로젝트 설명서

원본에 대한 자세한 내용은
[joonspk-research/generative_agents](http://github.com/joonspk-research/generative_agents)
참고



## 개발 환경

- `Windows 10`, `Ubuntu 22.04`
- `Python 3.12.5`



## utils.py

백엔드를 실행하기 위해서는 아래와 같이 작성된 `utils.py` 파일을
`reverie/backend_server/utils.py` 위치에 먼저 생성한 후
`<이 부분>`을 모두 수정해야 함

```python
# ollama
ollama_url = "http://<Ollama IP:11434>"
ollama_model = "<Model Name>"

# Attack Info
attack = "<Attack Type, e.g. SQL Injection>"
target_base = "http://<target_ip:port/base>"
target_path = "</target/path/>"
target_url = target_base + target_path
server_path = "<./path/to/source>"

maze_assets_loc = "../../environment/frontend_server/static/assets"
env_matrix = f"{maze_assets_loc}/%s/matrix"
env_visuals = f"{maze_assets_loc}/%s/visuals"

fs_storage = "../../environment/frontend_server/storage"
fs_temp_storage = "../../environment/frontend_server/temp_storage"

auto_save_next_env_file = True

# Verbose 
debug = True

black_hats = ["Carlos Gomez", "Yuriko Yamamoto"]
white_hats = ["Abigail Chen", "Arthur Burton"]
server_owners = ["Isabella Rodriguez"]
work_areas = ["computer desk"]
```



## Forked from

- [원본 저장소](http://github.com/joonspk-research/generative_agents)
- [reverie/backend_server](https://github.com/nyoma-diamond/evaluating_generative_agents)
