import os
import typer
from typing import Optional
from rich.console import Console
from rich.progress import (
    Progress,
    SpinnerColumn,
    TextColumn,
    BarColumn,
    TimeElapsedColumn,
)
import pyfiglet
from dotenv import load_dotenv

from gbackup.core.backup_service import BackupService
from gbackup.providers.source.github import GitHubProvider
from gbackup.providers.storage.s3 import S3StorageProvider
from gbackup.utils.archiver import ZipArchiver

load_dotenv()

app = typer.Typer(help="GBackUp CLI: Securely backup your GitHub repositories.")
console = Console()


def print_banner():
    ascii_art = pyfiglet.figlet_format("GBackUp", font="slant")
    console.print(f"[bold cyan]{ascii_art}[/bold cyan]", justify="center")
    console.print(
        "[bold white on blue]SECURE GITHUB REPOSITORY BACKUP TOOL[/bold white on blue]",
        justify="center",
    )
    console.print("\n")


@app.command()
def backup(
    token: str = typer.Option(
        os.getenv("GITHUB_ACCESS_TOKEN"), help="GitHub Personal Access Token"
    ),
    public_only: bool = typer.Option(False, help="Backup only public repositories"),
    no_upload: bool = typer.Option(False, help="Skip upload to S3/Tigris"),
    output_dir: Optional[str] = typer.Option(None, help="Local output directory"),
):
    print_banner()

    if not token:
        console.print("[bold red]❌ Error: No GitHub Token provided.[/bold red]")
        raise typer.Exit(code=1)

    source = GitHubProvider(token, owner_only=not public_only)

    endpoint_url = os.getenv("TIGRIS_ENDPOINT") or ""
    bucket_name = os.getenv("BUCKET_NAME") or ""
    access_key = os.getenv("ACCESS_KEY") or ""
    secret_key = os.getenv("SECRET_KEY") or ""

    if not all([endpoint_url, bucket_name, access_key, secret_key]):
        if not no_upload:
            console.print(
                "[bold red]❌ Error: Missing S3/Tigris environment variables.[/bold red]"
            )
            raise typer.Exit(code=1)

    storage = S3StorageProvider(
        endpoint_url=endpoint_url,
        bucket_name=bucket_name,
        access_key=access_key,
        secret_key=secret_key,
    )
    archiver = ZipArchiver()

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TextColumn("{task.completed}/{task.total}"),
        TimeElapsedColumn(),
        console=console,
    ) as progress:
        task = progress.add_task("[green]Processing repositories...", total=0)

        def update_progress(repo_name, current, total):
            progress.update(
                task, total=total, description=f"[green]Backing up {repo_name}..."
            )
            progress.update(task, completed=current)

        service = BackupService(
            source, storage, archiver, progress_callback=update_progress
        )

        try:
            result = service.run_backup(output_dir=output_dir, no_upload=no_upload)
            if result:
                if no_upload:
                    console.print(
                        f"[bold green]✅ Backup saved locally to: {result}[/bold green]"
                    )
                else:
                    console.print(
                        f"[bold green]✅ Backup uploaded to: {result}[/bold green]"
                    )
            else:
                console.print("[yellow]⚠️ No repositories found to backup.[/yellow]")
        except Exception as e:
            console.print(f"[bold red]❌ Backup failed: {e}[/bold red]")
            raise typer.Exit(code=1)


if __name__ == "__main__":
    app()
