import typer
import requests
import sys
import os
import json

app = typer.Typer()
HTTP_PORT = os.getenv('HTTP_PORT', 8000)
DEFAULT_HOST = f"http://localhost:{HTTP_PORT}"

def get_host(ctx: typer.Context):
    return ctx.obj.get("host") or os.getenv("VERSIONCI_API_BASE") or DEFAULT_HOST

@app.callback()
def main(ctx: typer.Context, host: str = typer.Option(None, help="Base URL of VerCI API")):
    ctx.obj = {"host": host}

@app.command(name="list")
def list_store(ctx: typer.Context):
    """
    Show full store JSON from API root.
    """
    host = get_host(ctx)
    resp = requests.get(f"{host}/")
    if resp.status_code == 200:
        typer.echo(json.dumps(resp.json(), indent=2))
    else:
        typer.echo(f"❌ Failed to fetch store data: {resp.status_code}", err=True)
        sys.exit(1)

@app.command(name="projects")
def list_projects(ctx: typer.Context):
    """
    List all project names.
    """
    host = get_host(ctx)
    resp = requests.get(f"{host}/projects")
    if resp.status_code == 200:
        typer.echo("\n".join(resp.json()))
    else:
        typer.echo(f"❌ Failed to fetch projects: {resp.status_code}", err=True)
        sys.exit(1)

@app.command()
def register(ctx: typer.Context, name: str, repo: str):
    host = get_host(ctx)
    resp = requests.post(f"{host}/projects", json={"name": name, "repo": repo})
    if resp.status_code == 200:
        typer.echo("✅ Project registered.")
    else:
        typer.echo(f"❌ Error: {resp.json().get('detail')}", err=True)
        sys.exit(1)

@app.command()
def get_version(ctx: typer.Context, project: str, branch: str):
    host = get_host(ctx)
    resp = requests.get(f"{host}/projects/{project}/versions")
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
def set_version(
    ctx: typer.Context,
    project: str,
    branch: str,
    version: str,
    commit: str = typer.Option(None, help="Optional commit hash to associate with this version"),
):
    host = get_host(ctx)
    params = {"branch": branch, "version": version}
    if commit:
        params["commit"] = commit
    resp = requests.patch(f"{host}/projects/{project}/version", params=params)
    typer.echo(resp.json().get("message"))

@app.command()
def bump(
    ctx: typer.Context,
    project: str,
    branch: str,
    strategy: str = "patch",
    commit: str = typer.Option(None, help="Optional commit hash to associate with the bumped version"),
):
    host = get_host(ctx)
    params = {"branch": branch, "strategy": strategy}
    if commit:
        params["commit"] = commit
    resp = requests.post(f"{host}/projects/{project}/bump", params=params)
    if resp.status_code == 200:
        typer.echo(f"🔼 New version: {resp.json()['new_version']}")
        if resp.json().get("commit"):
            typer.echo(f"Commit: {resp.json()['commit']}")
    else:
        typer.echo(f"❌ Error: {resp.json().get('detail')}", err=True)
        sys.exit(1)

@app.command()
def remove(ctx: typer.Context, project: str, branch: str = typer.Option(None, help="Branch name to remove")):
    """
    Remove a project or a branch from a project.
    """
    host = get_host(ctx)
    params = {}
    if branch:
        params["branch"] = branch
    resp = requests.delete(f"{host}/projects/{project}", params=params)
    if resp.status_code == 200:
        typer.echo(f"✅ {resp.json().get('message')}")
    else:
        typer.echo(f"❌ Error: {resp.json().get('detail')}", err=True)
        sys.exit(1)

if __name__ == "__main__":
    app()
