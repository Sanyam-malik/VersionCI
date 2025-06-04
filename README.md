# VersionCI - Git Branch Version Tracker & Auto-Bumper

VersionCI is a lightweight version management service designed to track and auto-bump versions per branch across multiple Git projects.  
It supports flexible versioning schemes with configurable rollover thresholds and is built to integrate seamlessly into CI/CD pipelines.

---

## Features

- Register multiple Git projects and track versions per branch  
- Auto-bump versions with strategies: `increment`, `patch`, `minor`, `major`  
- Supports arbitrary version formats (e.g. `1.0`, `1.2.3.4`)  
- Configurable rollover threshold via environment variable (`ROLLOVER_THRESHOLD`)  
- Simple REST API server with a companion CLI client  
- Designed for CI/CD pipeline integration  

---

## Getting Started

### Requirements

- Docker & Docker Compose  
- Python 3.11+ (for local development)  

### Setup & Run

1. Clone the repository  
2. Build and start services:

```bash
docker-compose up --build
```
or Use the install scripts
```bash
curl -fsSL -u http://forgejo.local/Neo/VersionCI/raw/branch/main/install.sh -o install.sh

chmod +x install.sh
sudo ./install.sh
```

---

### Environment Variables

You can configure the rollover threshold for version segments using the `ROLLOVER_THRESHOLD` environment variable. This controls the maximum value a version segment can reach before rolling over and incrementing the previous segment. The default is `9`.

```yaml
services:
  versionci:
    environment:
      - ROLLOVER_THRESHOLD=9
```

## Usage

### Running VerCI CLI Commands

Use the CLI inside the `vercli` container:

### Available CLI Commands

| Command       | Description                                 | Example                                                      |
| ------------- | ------------------------------------------- | ------------------------------------------------------------ |
| `register`    | Register a new Git project                  | `register my-project https://github.com/user/repo.git`       |
| `list`        | List all registered projects                | `list`                                                       |
| `get-version` | Get the version for a specific branch      | `get-version my-project main`                                |
| `set-version` | Set the version manually for a branch      | `set-version my-project main 1.0.0`                          |
| `bump`        | Bump version for a branch with a strategy  | `bump my-project main --strategy minor`                      |

### Bump Strategies

You can use the following strategies when bumping version numbers:

| Strategy   | Description                                                                 |
|------------|-----------------------------------------------------------------------------|
| `increment`| Increments the last available segment (e.g. `1.0` → `1.1`, `1.0.9` → `1.0.10`) |
| `patch`    | Increments the patch segment. If it doesn't exist, it will be added.        |
| `minor`    | Increments the minor segment and resets patch (e.g. `1.2.3` → `1.3.0`)      |
| `major`    | Increments the major segment and resets others (e.g. `1.2.3` → `2.0.0`)     |

You can point the CLI to a remote server by either:
    
Using the `--api-base` option:
```bash
python vercli.py --api-base http://your-server:8000 register my-project https://github.com/user/repo.git
```

## API Examples

Use any HTTP client to interact with the API (default base URL: http://localhost:8000):
1. Register a Project

```bash
curl -X POST "http://localhost:8000/projects" \
-H "Content-Type: application/json" \
-d '{"name":"my-project","repo":"https://github.com/user/repo.git"}'
```
2. List Projects
```bash
curl "http://localhost:8000/projects"
```
3. Get Versions for Branches in a Project
```bash
curl "http://localhost:8000/projects/my-project/versions"
```
4. Set Version for a Branch
```bash
curl -X PATCH "http://localhost:8000/projects/my-project/version?branch=main&version=1.0.0"
```
5. Bump Version for a Branch
```bash
curl -X POST "http://localhost:8000/projects/my-project/bump?branch=main&strategy=minor"
```
## Data Persistence

All project and version data is saved in data/store.json inside the server container or your mounted volume.