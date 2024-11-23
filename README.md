# LLM을 활용한 해킹 공격 및 방어 시뮬레이션 환경 구축

본 프로젝트는
[joonspk-research/generative_agents](https://github.com/joonspk-research/generative_agents)
저장소를 포크하여 진행되었습니다.

![cover](cover.png)



## Development Environment

| Component    | Details                                           |
|--------------|---------------------------------------------------|
| OS           | `Windows 10`, `WSL(Ubuntu 22.04)`, `Ubuntu 24.04` |
| Language     | `Python 3.12.5`                                   |
| GPU (Memory) | NVIDIA GeForce RTX 3060 (12GB)                    |



## Installation

> [!WARNING]
> 파이썬 버전이 `3.12.5`이 아닐 경우 에러가 발생할 수 있습니다.

내용 중 `<이 부분>`은 모두 상황에 맞게 수정해 주세요.

1. 소스코드 다운로드 후 해당 폴더로 이동
2. `pip install -Ur requirements.txt` 명령어를 실행하여 필요한 모듈 자동 설치
3. [DVWA](https://github.com/digininja/dvwa) 또는 별도의 서버로 타겟 서버 구성 및 실행
4. [Ollama](https://ollama.com/) 설치
5. LLM 모델 빌드
    - 사용하고자 하는 모델의 GGUF 파일을 다운로드
    - Modelfile 파일 생성 및 `FROM <File Name>.gguf` 작성 후 `ollama create <Model Name> -f Modelfile` 명령어 실행
6. `environment/frontend_server`에서 아래 명령어를 사용하여 프론트엔드 실행

    ```shell
    python3 manage.py migrate
    python3 manage.py runserver
    # python3 manage.py runserver 0.0.0.0:8000  # 외부 접속이 필요한 경우
    ```

7. `reverie/backend_server`로 이동 후 아래 명령어를 사용하여 백엔드 실행
    - 실행 전 [utils.py](#utilspy) 파일 작성 필수

    ```shell
    python3 reverie.py
    ```

## utils.py

백엔드를 실행하기 위해서는 아래와 같이 작성된 `utils.py` 파일을
`reverie/backend_server` 폴더 내 먼저 생성해아 합니다.

```python
# ollama
ollama_url = "http://<Ollama IP:11434>"
ollama_model = "<Model Name>"

# Target Server Info
dvwa_url = "http://<dvwa_ip:port/base>"
server_path = "<./path/to/source>"

maze_assets_loc = "../../environment/frontend_server/static/assets"
env_matrix = f"{maze_assets_loc}/%s/matrix"
env_visuals = f"{maze_assets_loc}/%s/visuals"

fs_storage = "../../environment/frontend_server/storage"
fs_temp_storage = "../../environment/frontend_server/temp_storage"

black_hats = ["Carlos Gomez", "Yuriko Yamamoto"]
white_hats = ["Abigail Chen", "Arthur Burton"]
server_owners = ["Isabella Rodriguez"]
work_areas = ["computer desk", "control screen"]

# Verbose
debug = True
```



## API

> [!TIP]
> <http://frontend_ip:port/api/> 및 하위 경로로 직접 접근할 수 있습니다.

시뮬레이션 정보 조회 기능만 제공합니다.

| 요청 경로                          | 응답 내용                                                |
|------------------------------------|----------------------------------------------------------|
| /api                               | API 사용법(변경 예정)                                    |
| /api/help                          | API 사용법                                               |
| /api/running                       | 현재 진행 중인 시뮬레이션 정보                           |
| /api/pens                          | 시뮬레이션 목록 및 메타 데이터                           |
| /api/pens/\<pen_code>              | \<pen_code>의 메타 데이터                                |
| /api/pens/\<pen_code>/\<step>      | \<pen_code>의 스텝이 \<step>일 때 에이전트들의 행동 정보 |
| /api/pens/\<pen_code>/-1           | \<pen_code>의 모든 스텝에 대한 에이전트들의 행동 정보    |
| /api/pens/\<pen_code>/payloads     | \<pen_code>에서 생성된 페이로드 목록                     |
| /api/pens/\<pen_code>/patches      | \<pen_code>에서 생성된 모든 패치 제안 목록               |
| /api/pens/\<pen_code>/best         | \<pen_code>에서 생성된 선택된 패치 제안 목록             |
| /api/charts                        | 대시보드에서 제공되는 모든 차트 데이터                   |
| /api/charts/pens                   | 대시보드에서 제공되는 시뮬레이션별 데이터                |
| /api/charts/pens/\<pen_code>       | 대시보드에서 제공되는 \<pen_code> 데이터                 |
| /api/charts/urls                   | 대시보드에서 제공되는 URL별 차트 데이터                  |
| /api/charts/attacks                | 대시보드에서 제공되는 공격 유형별 차트 데이터            |
| /api/charts/attacks/\<attack_name> | 대시보드에서 제공되는 \<attack_name> 데이터              |



## Forked from

- [joonspk-research/generative_agents](http://github.com/joonspk-research/generative_agents)
- [nyoma-diamond/evaluating_generative_agents](https://github.com/nyoma-diamond/evaluating_generative_agents)
