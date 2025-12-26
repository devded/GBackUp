import os
import shutil
import zipfile
import tempfile
from git import Repo
import boto3
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()
# -----------------------
# CONFIG
# -----------------------
TIGRIS_ENDPOINT = os.getenv("TIGRIS_ENDPOINT")
BUCKET_NAME = os.getenv("BUCKET_NAME")

ACCESS_KEY = os.getenv("ACCESS_KEY")
SECRET_KEY = os.getenv("SECRET_KEY")
print(TIGRIS_ENDPOINT, BUCKET_NAME, ACCESS_KEY, SECRET_KEY)


# -----------------------
# MAIN FUNCTION
# -----------------------
def backup_github_repo(repo_url: str, repo_name: str):
    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")

    with tempfile.TemporaryDirectory() as tmp_dir:
        repo_path = os.path.join(tmp_dir, repo_name)
        zip_path = os.path.join(tmp_dir, f"{repo_name}_{timestamp}.zip")

        print("🔹 Cloning repository...")
        Repo.clone_from(repo_url, repo_path, mirror=True)

        print("🔹 Zipping repository...")
        zip_directory(repo_path, zip_path)

        print("🔹 Uploading to Tigris...")
        upload_to_tigris(zip_path, f"backups/{repo_name}/{os.path.basename(zip_path)}")

        print("✅ Backup completed successfully!")


# -----------------------
# ZIP FUNCTION
# -----------------------
def zip_directory(source_dir, zip_file):
    with zipfile.ZipFile(zip_file, "w", zipfile.ZIP_DEFLATED) as z:
        for root, _, files in os.walk(source_dir):
            for file in files:
                file_path = os.path.join(root, file)
                arcname = os.path.relpath(file_path, source_dir)
                z.write(file_path, arcname)


# -----------------------
# Tigris Upload
# -----------------------
def upload_to_tigris(file_path, object_key):
    s3 = boto3.client(
        "s3",
        endpoint_url=TIGRIS_ENDPOINT,
        aws_access_key_id=ACCESS_KEY,
        aws_secret_access_key=SECRET_KEY,
        region_name="auto",
    )

    s3.upload_file(
        Filename=file_path,
        Bucket=BUCKET_NAME,
        Key=object_key,
    )


# -----------------------
# RUN
# -----------------------
if __name__ == "__main__":
    GITHUB_REPO_URL = "https://github.com/psf/requests.git"
    REPO_NAME = "requests"

    backup_github_repo(GITHUB_REPO_URL, REPO_NAME)
