import requests
from git import Repo
from typing import List, Dict, Any
from gbackup.core.interfaces import SourceProvider


class GitHubProvider(SourceProvider):
    def __init__(self, token: str, owner_only: bool = True):
        self.token = token
        self.owner_only = owner_only
        self.base_url = "https://api.github.com/user/repos"
        self.headers = {
            "Authorization": f"token {self.token}",
            "Accept": "application/vnd.github.v3+json",
        }

    def get_repositories(self) -> List[Dict[str, Any]]:
        repos: List[Dict[str, Any]] = []
        page = 1
        per_page = 100

        while True:
            params: Dict[str, Any] = {
                "page": page,
                "per_page": per_page,
            }
            if self.owner_only:
                params["affiliation"] = "owner"

            response = requests.get(self.base_url, headers=self.headers, params=params)
            response.raise_for_status()
            data = response.json()

            if not data:
                break

            for repo in data:
                repos.append(
                    {
                        "name": repo["name"],
                        "clone_url": repo["clone_url"],
                        "owner": repo["owner"]["login"],
                    }
                )

            if len(data) < per_page:
                break
            page += 1

        return repos

    def clone_repository(self, repo_info: Dict[str, Any], destination: str):
        clone_url = repo_info["clone_url"]
        auth_clone_url = clone_url.replace("https://", f"https://{self.token}@", 1)
        Repo.clone_from(auth_clone_url, destination)
