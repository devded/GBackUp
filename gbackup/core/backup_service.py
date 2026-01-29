import os
import tempfile
import shutil
from datetime import datetime
from typing import Optional, Callable
from gbackup.core.interfaces import SourceProvider, StorageProvider, Archiver


class BackupService:
    def __init__(
        self,
        source: SourceProvider,
        storage: StorageProvider,
        archiver: Archiver,
        progress_callback: Optional[Callable[[str, int, int], None]] = None,
    ):
        self.source = source
        self.storage = storage
        self.archiver = archiver
        self.progress_callback = progress_callback

    def run_backup(self, output_dir: Optional[str] = None, no_upload: bool = False):
        repos = self.source.get_repositories()
        if not repos:
            return None

        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")

        # We use current directory for temp if not specified to avoid issues with some OS temp dirs
        with tempfile.TemporaryDirectory(dir=os.getcwd()) as master_tmp_dir:
            zipped_repos_dir = os.path.join(master_tmp_dir, "zipped_repos")
            os.makedirs(zipped_repos_dir)

            clone_temp_dir = os.path.join(master_tmp_dir, "temp_clone")
            os.makedirs(clone_temp_dir)

            for i, repo in enumerate(repos):
                repo_name = repo["name"]
                if self.progress_callback:
                    self.progress_callback(repo_name, i + 1, len(repos))

                current_repo_path = os.path.join(clone_temp_dir, repo_name)
                repo_zip_path = os.path.join(zipped_repos_dir, f"{repo_name}.zip")

                try:
                    self.source.clone_repository(repo, current_repo_path)
                    self.archiver.compress(current_repo_path, repo_zip_path)
                    shutil.rmtree(current_repo_path)
                except Exception as e:
                    # In a real app, we'd log this properly
                    print(f"Error processing {repo_name}: {e}")
                    if os.path.exists(current_repo_path):
                        shutil.rmtree(current_repo_path, ignore_errors=True)

            zip_filename = f"gbackup_snapshot_{timestamp}.zip"
            final_zip_path = os.path.join(master_tmp_dir, zip_filename)

            self.archiver.compress(zipped_repos_dir, final_zip_path)

            if no_upload:
                dest = os.path.join(output_dir or os.getcwd(), zip_filename)
                shutil.copy(final_zip_path, dest)
                return dest
            else:
                object_key = f"backups/account_snapshots/{zip_filename}"
                self.storage.upload(final_zip_path, object_key)
                return object_key
