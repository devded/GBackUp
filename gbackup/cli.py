import os
import typer
import pyfiglet
from typing import Optional
from dotenv import load_dotenv
from rich.console import Console
from rich.text import Text
from rich.progress import (
    Progress,
    SpinnerColumn,
    TextColumn,
    BarColumn,
    TimeElapsedColumn,
)

from gbackup.core.backup_service import BackupService
from gbackup.providers.source.github import GitHubProvider
from gbackup.providers.storage.s3 import S3StorageProvider
from gbackup.utils.archiver import ZipArchiver

load_dotenv()

app = typer.Typer(help="GBackUp CLI: Securely backup your GitHub repositories.")
console = Console()


def print_banner():
    print("\n\n")
    # Generate banner using pyfiglet banner3 font, then apply gradient
    text = "> GBackUp"
    ascii_art = pyfiglet.figlet_format(text, font="banner3")
    lines = ascii_art.splitlines()

    if not lines:
        return

    max_w = max(len(line) for line in lines) if lines else 1

    for line in lines:
        if not line.strip():
            continue
        rich_text = Text()
        for i, char in enumerate(line):
            if char == " ":
                rich_text.append(" ")
                continue

            # Gradient matching reference: Cyan -> Purple -> Pink
            rel = i / max_w if max_w > 0 else 0
            if rel < 0.5:
                p = rel * 2
                r = int(0 + (138 - 0) * p)
                g = int(210 + (43 - 210) * p)
                b = 255
            else:
                p = (rel - 0.5) * 2
                r = int(138 + (255 - 138) * p)
                g = int(43 + (102 - 43) * p)
                b = int(255 + (180 - 255) * p)

            # Replace '#' with '░' for halftone/dithered look like the reference
            display_char = "░" if char == "#" else char
            rich_text.append(display_char, style=f"bold rgb({r},{g},{b})")

        console.print(rich_text)

    console.print("")
    console.print(
        "[bold white]SECURE GITHUB REPOSITORY BACKUP TOOL[/bold white]",
        justify="center",
    )
    console.print("")


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
