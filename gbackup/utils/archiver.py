import os
import zipfile
from gbackup.core.interfaces import Archiver


class ZipArchiver(Archiver):
    def compress(self, source_dir: str, output_path: str):
        with zipfile.ZipFile(output_path, "w", zipfile.ZIP_DEFLATED) as z:
            for root, _, files in os.walk(source_dir):
                for file in files:
                    file_path = os.path.join(root, file)
                    arcname = os.path.relpath(file_path, source_dir)
                    z.write(file_path, arcname)
