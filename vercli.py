import typer
import requests
import sys
import os

app = typer.Typer()
HTTP_PORT = os.getenv('HTTP_PORT', 8000)
DEFAULT_API_BASE = f"http://localhost:{HTTP_PORT}"

def get_api_base(ctx: typer.Context):
    return ctx.obj.get("api_base") or os.getenv("VERSIONCI_API_BASE") or DEFAULT_API_BASE

@app.callback()
def main(ctx: typer.Context, api_base: str = typer.Option(None, help="Base URL of VerCI API")):
    ctx.obj = {"api_base": api_base}

@app.command()
def register(ctx: typer.Context, name: str, repo: str):
    base = get_api_base(ctx)
    resp = requests.post(f"{base}/projects", json={"name": name, "repo": repo})
    if resp.status_code == 200:
        typer.echo("✅ Project registered.")
    else:
        typer.echo(f"❌ Error: {resp.json().get('detail')}", err=True)
        sys.exit(1)

@app.command()
def list(ctx: typer.Context):
    base = get_api_base(ctx)
    resp = requests.get(f"{base}/projects")
    typer.echo("\n".join(resp.json()))

@app.command()
def get_version(ctx: typer.Context, project: str, branch: str):
    base = get_api_base(ctx)
    resp = requests.get(f"{base}/projects/{project}/versions")
    if resp.status_code == 200:
        branches = resp.json()
        version = branches.get(branch)
        if version:
            typer.echo(version["version"])
        else:
            typer.echo("❌ Branch not found.", err=True)
            sys.exit(1)
    else:
        typer.echo("❌ Project not found.", err=True)
        sys.exit(1)

@app.command()
def set_version(ctx: typer.Context, project: str, branch: str, version: str):
    base = get_api_base(ctx)
    resp = requests.patch(f"{base}/projects/{project}/version", params={"branch": branch, "version": version})
    typer.echo(resp.json().get("message"))

@app.command()
def bump(ctx: typer.Context, project: str, branch: str, strategy: str = "patch"):
    base = get_api_base(ctx)
    resp = requests.post(f"{base}/projects/{project}/bump", params={"branch": branch, "strategy": strategy})
    if resp.status_code == 200:
        typer.echo(f"🔼 New version: {resp.json()['new_version']}")
    else:
        typer.echo(f"❌ Error: {resp.json().get('detail')}", err=True)
        sys.exit(1)

@app.command()
def remove(ctx: typer.Context, project: str, branch: str = typer.Option(None, help="Branch name to remove")):
    """
    Remove a project or a branch from a project.
    """
    base = get_api_base(ctx)
    params = {}
    if branch:
        params["branch"] = branch
    resp = requests.delete(f"{base}/projects/{project}", params=params)
    if resp.status_code == 200:
        typer.echo(f"✅ {resp.json().get('message')}")
    else:
        typer.echo(f"❌ Error: {resp.json().get('detail')}", err=True)
        sys.exit(1)

if __name__ == "__main__":
    app()
