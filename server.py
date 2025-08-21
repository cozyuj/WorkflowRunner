from fastapi import FastAPI, Form
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
import requests, json, os, zipfile, uuid, asyncio, re
import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

# -----------------------------
# CORS
# -----------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# -----------------------------
# 경로 설정
# -----------------------------
COMFYUI_API = "http://127.0.0.1:8188"
WORKFLOW_JSON = "./workflows/parametricPixel_v3_Workflow_01.json"
OUTPUT_DIR = "../ComfyUI/output"
os.makedirs(OUTPUT_DIR, exist_ok=True)

progress_status = {"progress": 0, "done": False, "download_url": ""}


# -----------------------------
# 템플릿 불러오기
# -----------------------------
TEMPLATE_FILE = "./prompts/templates.json"

@app.get("/templates")
async def get_templates():
    try:
        with open(TEMPLATE_FILE, "r", encoding="utf-8") as f:
            templates = json.load(f)
        return {"status": "ok", "templates": templates}
    except Exception as e:
        return {"status": "fail", "msg": str(e)}


# -----------------------------
# HTML 페이지
# -----------------------------
@app.get("/", response_class=HTMLResponse)
async def form_page():
    return """
<html>
<head>
<title>ComfyUI Generator</title>
<!-- Google Fonts -->
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Roboto:wght@400;500;700&display=swap" rel="stylesheet">
<style>
    body {
        font-family: 'Roboto', sans-serif; /* 전체 폰트 적용 */
    }
    form {
        max-width: 600px;
    }
    select, textarea, input, button {
        width: 100%;
        box-sizing: border-box;
        padding: 8px;
        margin: 6px 0;
        font-size: 16px;
    }
    textarea {
        height: 100px; /* 높이 기본값 */
        resize: vertical; /* 세로 크기만 조절 가능 */
    }
    button {
        cursor: pointer;
        background-color: #4CAF50;
        color: white;
        border: none;
        border-radius: 6px;
    }
    button:hover {
        background-color: #45a049;
    }
    small {
        color: gray;
    }
    p {
        font-weight: bold;   /* 굵게 */
        color: #333333;      /* 진한 회색 */
    }
    hr {
        border: none;             /* 기본 선 제거 */
        height: 1px;              /* 선 두께 */
        background-color: #cccccc; /* 원하는 색상 */
    }
    #progressContainer {
        max-width: 600px;
        background-color: #eee;  /* 바깥 배경 */
        border-radius: 6px;
        overflow: hidden;
        height: 20px;
        margin-bottom: 8px;
    }

    #progressBar {
        width: 1%;                  /* 기본 0% */
        height: 100%;
        background-color: #4CAF50; /* 진행률 색상 */
        transition: width 0.3s ease; /* 부드럽게 이동 */
    }

</style>
</head>
<body>
<h2>ComfyUI 프롬프트 입력</h2>
<hr>
<form id="genForm">
<p>템플릿 선택</p>
<small>미리 저장된 프롬프트/네거티브 조합을 불러옵니다.</small><br>
<select id="templateSelect" onchange="onTemplateChange()"></select><br><br>

<p>prompt</p>
<small>생성하고 싶은 이미지를 묘사하는 문장</small><br>
<textarea id="prompt" rows="4" cols="60"></textarea><br><br>

<p>Negative Prompt</p>
<small>피하고 싶은 요소 (예: low quality, blurry)</small><br>
<textarea id="negative" rows="4" cols="60"></textarea><br><br>

<p>LoRA 적용강도</p>
<small>LoRA가 모델 레이어에 적용되는 강도. 0~1 범위로 조절 가능 (1 = 100%)</small><br>
<input type="number" id="lora_strength" value="1" min="0" max="1"><br><br>
<br><br>


<p>Sampler</p>
<small>픽셀을 확정하는 방식 (알고리즘)</small><br>
<select id="sampler">
<option value="dpmpp_2m_sde_gpu">DPM++ SDE</option>
<option value="euler">Euler a</option>
<option value="lms">LMS</option>
</select>
<br><br>

<p>Steps</p>
<small>샘플링 반복 횟수 (높을수록 디테일 ↑)</small><br>
<input type="number" id="steps" value="30" min="1" max="100"><br><br>

<p>CFG Scale</p>
<small>프롬프트를 얼마나 강하게 반영할지 결정 / 기본 7.0~7.5</small><br>
<input type="number" id="cfg_scale" value="7.5" step="0.1" min="0" max="20"><br><br>

<p>생성 개수</p>
<small>한 번에 몇 장의 이미지를 만들지</small><br>
<input type="number" id="num_images" value="1" min="1" max="10"><br><br>
<button type="button" onclick="generate()">이미지 생성</button>
</form>

<label for="progressBar">진행률</label> <span id="progressText">0%</span><br>
<div id="progressContainer">
    <div id="progressBar"></div>
</div>


<script>
async function generate() {
    const prompt = document.getElementById("prompt").value;
    const negative = document.getElementById("negative").value;
    const sampler = document.getElementById("sampler").value;
    const steps = document.getElementById("steps").value;
    const cfg_scale = document.getElementById("cfg_scale").value;
    const lora_strength = document.getElementById("lora_strength").value;
    const num_images = document.getElementById("num_images").value;

    // 요청 전 alert
    alert(`생성 요청 전송\nPrompt: ${prompt}\nNegative: ${negative}\lora_strength: ${lora_strength}\nSampler: ${sampler}\nSteps: ${steps}\nCFG Scale: ${cfg_scale}\n생성 개수: ${num_images}`);

    const formData = new FormData();
    formData.append("prompt", prompt);
    formData.append("negative", negative);
    formData.append("sampler", sampler);
    formData.append("steps", steps);
    formData.append("cfg_scale", cfg_scale);
    formData.append("lora_strength", lora_strength);
    formData.append("num_images", num_images);

    const resp = await fetch("/generate", {method:"POST", body:formData});
    const data = await resp.json();

    if(resp.ok && data.status === "ok"){
        alert("생성 요청 성공! 이미지가 준비되면 자동 다운로드됩니다.");

        let interval = setInterval(async () => {
            try {
                const statusResp = await fetch("/check_ready");
                const statusData = await statusResp.json();
                console.log("폴링 응답:", statusData); // 디버깅용

                if (statusData.ready) {
                    clearInterval(interval);
                    console.log("이미지 준비 완료, 다운로드 시작:", statusData.download_url);
                    window.open(statusData.download_url, "_blank");
                }
            } catch (err) {
                console.error("폴링 오류:", err);
            }
        }, 1000);

    } else {
        alert("생성 요청 실패! 오류: " + (data.msg||"알 수 없음"));
    }
}
async function loadTemplates() {
    const resp = await fetch("/templates");
    const data = await resp.json();
    console.log("템플릿 응답:", data);  // ✅ 디버깅용

    if (data.status === "ok") {
        templates = data.templates;
        console.log("템플릿 배열:", templates); // ✅ 확인
        const select = document.getElementById("templateSelect");
        select.innerHTML = "";

        templates.forEach((tpl, idx) => {
            console.log("추가되는 옵션:", tpl.name); // ✅ 확인
            const option = document.createElement("option");
            option.value = idx;
            option.textContent = tpl.name;
            select.appendChild(option);
        });

        if (templates.length > 0) {
            select.value = 0;
            applyTemplate(0);
        }
    } else {
        console.error("템플릿 불러오기 실패:", data);
    }
}


// 템플릿 적용 함수
function applyTemplate(idx) {
    if (!templates[idx]) return;
    const tpl = templates[idx];
    document.getElementById("prompt").value = tpl.prompt || "";
    document.getElementById("negative").value = tpl.negative || "";
}

// 선택 시 textarea 채우기
function onTemplateChange() {
    const idx = document.getElementById("templateSelect").value;
    applyTemplate(idx);
}

// 페이지 로드 시 템플릿 불러오기
window.onload = loadTemplates;

</script>
</body>
</html>
"""


# -----------------------------
# 이미지 생성 요청
# -----------------------------
@app.post("/generate")
async def generate_image(
    prompt: str = Form(""),
    negative: str = Form(""),
    lora_strength: float = Form(1),
    sampler: str = Form("Euler a"),
    steps: int = Form(30),
    cfg_scale: float = Form(7.5),
    num_images: int = Form(1)
):
    try:
        if not prompt.strip():
            prompt = "abstract automotive sculpture, pure speedform silhouette, high detail"
        if not negative.strip():
            negative = "(low quality, blurry, watermark, text)"

        with open(WORKFLOW_JSON, "r", encoding="utf-8") as f:
            workflow = json.load(f)

        workflow["3"]["inputs"]["text"] = prompt
        workflow["5"]["inputs"]["text"] = negative
        workflow["6"]["inputs"]["steps"] = steps
        workflow["6"]["inputs"]["cfg"] = cfg_scale
        workflow["6"]["inputs"]["sampler_name"] = sampler
        workflow["13"]["inputs"]["lora_strength"] = lora_strength



        # 비동기 이미지 생성
        asyncio.create_task(run_comfy_workflow(workflow, num_images))

        return {
            "status": "ok",
            "prompt": prompt,
            "negative": negative,
            "sampler": sampler,
            "steps": steps,
            "lora_strength" : lora_strength,
            "cfg_scale": cfg_scale,
            "num_images": num_images
        }

    except Exception as e:
        return {"status":"fail", "msg":str(e)}, 500


# -----------------------------
# 비동기 이미지 생성
# -----------------------------
async def run_comfy_workflow(workflow, num_images):
    global progress_status
    try:
        resp = requests.post(f"{COMFYUI_API}/prompt", json={"prompt": workflow})
        workflow_id = resp.json().get("id")

        # prefix 가져오기
        prefix = ""
        for node in workflow["nodes"]:
            if node["type"] in ["SaveImage", "PreviewImage"]:
                prefix = node["inputs"].get("prefix", "")
                break
        prefix = re.sub(r'[^\w\-_.]', '', prefix)

        # 워크플로우 완료 대기
        total_nodes = len(workflow["nodes"])
        completed_nodes = 0
        while completed_nodes < total_nodes:
            await asyncio.sleep(0.5)
            status_resp = requests.get(f"{COMFYUI_API}/workflow_status/{workflow_id}")
            if status_resp.status_code != 200:
                continue
            status_json = status_resp.json()
            completed_nodes = sum(1 for node in status_json["nodes"] if node.get("done", False))

        # 완료 후 다운로드 URL 생성
        output_files = sorted(
            [f for f in os.listdir(OUTPUT_DIR) if f.startswith(prefix) and f.endswith(".png")],
            key=lambda x: os.path.getmtime(os.path.join(OUTPUT_DIR, x))
        )[-num_images:]

        logger.info("생성된 출력 파일: %s", output_files)

        if len(output_files) == 1:
            progress_status["download_url"] = f"/download/{output_files[0]}"
        else:
            zip_name = f"comfyui_{uuid.uuid4().hex}.zip"
            zip_path = os.path.join(OUTPUT_DIR, zip_name)
            with zipfile.ZipFile(zip_path, "w") as zf:
                for f in output_files:
                    zf.write(os.path.join(OUTPUT_DIR, f), arcname=f)
            progress_status["download_url"] = f"/download/{zip_name}"

        progress_status["done"] = True

    except Exception as e:
        progress_status["done"] = True
        progress_status["download_url"] = ""
# -----------------------------
# 이미지 준비 확인
# -----------------------------
@app.get("/check_ready")
async def check_ready():
    global progress_status
    print("check_ready 호출:", progress_status)  # 디버깅용
    if progress_status.get("done") and progress_status.get("download_url"):
        return {"ready": True, "download_url": progress_status["download_url"]}
    else:
        return {"ready": False}

    
# -----------------------------
# 진행률 SSE
# -----------------------------
from fastapi.responses import StreamingResponse

@app.get("/progress_status")
async def progress_sse():
    async def event_generator():
        global progress_status
        while not progress_status.get("done", False):
            await asyncio.sleep(0.5)
            yield f"data: {json.dumps(progress_status)}\n\n"
        yield f"data: {json.dumps(progress_status)}\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")


# -----------------------------
# 다운로드 엔드포인트
# -----------------------------
@app.get("/download/{filename}")
async def download_file(filename: str):
    file_path = os.path.join(OUTPUT_DIR, filename)
    if not os.path.exists(file_path):
        return HTMLResponse("<h3>파일이 존재하지 않습니다.</h3>", status_code=404)
    return FileResponse(file_path, media_type="application/octet-stream", filename=filename)