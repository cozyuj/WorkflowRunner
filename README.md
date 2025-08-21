### Running ComfyUI and WorkflowRunner
`$ ./run.sh`  
<br>

### How It Works  
1. ComfyUI is started first in the background.
2. WorkflowRunner starts afterward.
3. Pressing `Ctrl + C` sends a termination signal to both processes.
4. wait -n ensures the script waits until any of the processes exits.
5. Finally, any remaining process is terminated to prevent orphan processes.


<br>

### Run API Server (–listen option allows external access)
`$ python main.py --listen 0.0.0.0 --port 8188`

<br>

### Run FastAPI server on port 8000 with reload
`$ uvicorn server:app --reload --port 8000`


