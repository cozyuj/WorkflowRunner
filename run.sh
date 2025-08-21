#!/bin/bash

# 두 프로세스를 실행
cd /Users/youjin/Workspaces/ComfyUI || exit
python main.py --listen 0.0.0.0 --port 8188 &
PID1=$!

cd /Users/youjin/Workspaces/WorkflowRunner || exit
uvicorn server:app --reload --port 8000 &
PID2=$!

# Ctrl+C(SIGINT) 누르면 두 프로세스 종료
trap "kill $PID1 $PID2" SIGINT

# 프로세스가 끝날 때까지 대기
wait

