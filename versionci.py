import os
import json
import logging

import uvicorn
from fastapi import FastAPI, HTTPException, Query
from fastapi.exceptions import RequestValidationError
from pydantic import BaseModel

from starlette import status
from starlette.requests import Request
from starlette.responses import JSONResponse

HTTP_PORT = os.getenv('HTTP_PORT', 8000)

# ---- App Setup ----

app = FastAPI()
STORE_PATH = "data/store.json"
ROLLOVER_THRESHOLD = int(os.getenv("ROLLOVER_THRESHOLD", "9"))

if not os.path.exists("data"):
    os.makedirs("data")
if not os.path.exists(STORE_PATH):
    with open(STORE_PATH, "w") as f:
        json.dump({}, f)

def load_store():
    with open(STORE_PATH) as f:
        return json.load(f)

def save_store(store):
    with open(STORE_PATH, "w") as f:
        json.dump(store, f, indent=2)

def bump_version(version: str, strategy: str, rollover_threshold: int = 9) -> str:
    parts = list(map(int, version.strip().split(".")))
    length = len(parts)

    def rollover_increment(index: int):
        if index < 0:
            parts.insert(0, 1)
            return
        parts[index] += 1
        if parts[index] > rollover_threshold:
            parts[index] = 0
            rollover_increment(index - 1)

    if strategy == "increment":
        rollover_increment(length - 1)
    elif strategy == "patch":
        if length >= 3:
            parts[2] += 1
            if parts[2] > rollover_threshold:
                parts[2] = 0
                if length >= 2:
                    parts[1] += 1
        elif length == 2:
            parts.append(1)
        else:
            raise ValueError("Version must have at least major.minor")
    elif strategy == "minor":
        if length >= 2:
            parts[1] += 1
            if length >= 3:
                parts[2:] = [0] * (length - 2)
        else:
            raise ValueError("Version must have at least major.minor")
    elif strategy == "major":
        parts[0] += 1
        if length >= 2:
            parts[1:] = [0] * (length - 1)
    else:
        raise ValueError("Unsupported strategy")

    return ".".join(map(str, parts))

# ---- Schemas ----

class RegisterRequest(BaseModel):
    name: str
    repo: str

# ---- Error Handlers ----

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    errors = []
    for err in exc.errors():
        loc = ".".join(str(x) for x in err['loc'] if x != 'query')
        msg = err['msg']
        errors.append(f"{loc}: {msg}")
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"error": "Validation error", "details": errors},
    )

# ---- Routes ----

@app.post("/projects")
def register_project(req: RegisterRequest):
    store = load_store()
    if req.name in store:
        logging.warning(f"Attempt to register existing project: {req.name}")
        raise HTTPException(status_code=400, detail="Project already exists")
    store[req.name] = {"repo": req.repo, "branches": {}}
    save_store(store)
    logging.info(f"Registered project: {req.name}")
    return {"message": "Project registered"}

@app.get("/projects")
def list_projects():
    store = load_store()
    return list(store.keys())

@app.get("/projects/{name}/versions")
def get_versions(name: str):
    store = load_store()
    if name not in store:
        raise HTTPException(status_code=404, detail="Project not found")
    return store[name]["branches"]

@app.patch("/projects/{name}/version")
def set_version(name: str, branch: str = Query(...), version: str = Query(...)):
    store = load_store()
    if name not in store:
        raise HTTPException(status_code=404, detail="Project not found")
    store[name]["branches"][branch] = {"version": version}
    save_store(store)
    logging.info(f"Set version for {name}/{branch} to {version}")
    return {"message": f"Version for branch {branch} set to {version}"}

@app.post("/projects/{name}/bump")
def bump(name: str, branch: str = Query(...), strategy: str = Query("patch")):
    store = load_store()
    if name not in store:
        raise HTTPException(status_code=404, detail="Project not found")
    branches = store[name]["branches"]
    current = branches.get(branch, {}).get("version", "0.0.0")
    new_version = bump_version(current, strategy, ROLLOVER_THRESHOLD)
    branches[branch] = {"version": new_version}
    save_store(store)
    logging.info(f"Bumped version for {name}/{branch} to {new_version}")
    return {"new_version": new_version}

@app.delete("/projects/{name}")
def unregister_project(name: str, branch: str = Query(None)):
    store = load_store()
    if name not in store:
        raise HTTPException(status_code=404, detail="Project not found")

    if branch:
        branches = store[name].get("branches", {})
        if branch not in branches:
            raise HTTPException(status_code=404, detail="Branch not found")
        del branches[branch]
        save_store(store)
        logging.info(f"Removed branch '{branch}' from project '{name}'")
        return {"message": f"Branch '{branch}' removed from project '{name}'"}
    else:
        del store[name]
        save_store(store)
        logging.info(f"Unregistered project: {name}")
        return {"message": f"Project '{name}' unregistered"}

# ---- Main Entry ----

if __name__ == "__main__":
    logging.info("Starting application via versionci.py")
    uvicorn.run(
        "versionci:app",
        host="0.0.0.0",
        port=int(HTTP_PORT),
        log_level="debug",
        workers=1,
        timeout_keep_alive=120,
        limit_concurrency=1000,
        limit_max_requests=1000,
        headers=[("Server", "VersionCI")],
    )
