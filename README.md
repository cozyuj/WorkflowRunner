# API 서버 실행 (–listen 옵션으로 외부 접근 허용)
python main.py --listen 0.0.0.0 --port 8188

# 이미지 요청 API 실행 / Python용 고성능 ASGI 서버
uvicorn server:app --reload --port 8000


