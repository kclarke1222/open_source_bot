import requests
import os
from typing import List, Dict, Optional
from datetime import datetime
import json

class GitHubAPI:
    def __init__(self, token: Optional[str] = None):
        self.token = token or os.getenv('GITHUB_TOKEN')
        self.base_url = 'https://api.github.com'
        self.session = requests.Session()

        if self.token:
            self.session.headers.update({'Authorization': f'token {self.token}'})

        self.session.headers.update({
            'Accept': 'application/vnd.github.v3+json',
            'User-Agent': 'OpenSourceContributorAgent/1.0'
        })

    def search_repositories(self,
                          language: str = None,
                          topic: str = None,
                          min_stars: int = 50,
                          sort: str = 'updated',
                          order: str = 'desc',
                          per_page: int = 30) -> Dict:
        """Search for repositories based on criteria"""

        query_parts = []

        if language:
            query_parts.append(f'language:{language}')
        if topic:
            query_parts.append(f'topic:{topic}')
        if min_stars:
            query_parts.append(f'stars:>{min_stars - 1}')

        # Add filters for active repositories
        query_parts.append('archived:false')
        query_parts.append('fork:false')

        query = ' '.join(query_parts)

        params = {
            'q': query,
            'sort': sort,
            'order': order,
            'per_page': per_page
        }

        response = self.session.get(f'{self.base_url}/search/repositories', params=params)
        response.raise_for_status()

        return response.json()

    def get_repository_details(self, owner: str, repo: str) -> Dict:
        """Get detailed information about a repository"""
        response = self.session.get(f'{self.base_url}/repos/{owner}/{repo}')
        response.raise_for_status()
        return response.json()

    def get_repository_readme(self, owner: str, repo: str) -> Optional[str]:
        """Get repository README content"""
        try:
            response = self.session.get(f'{self.base_url}/repos/{owner}/{repo}/readme')
            response.raise_for_status()

            # GitHub API returns base64 encoded content
            import base64
            content = response.json()
            if content['encoding'] == 'base64':
                return base64.b64decode(content['content']).decode('utf-8')
            return content['content']
        except requests.exceptions.HTTPError:
            return None

    def get_repository_issues(self,
                            owner: str,
                            repo: str,
                            labels: List[str] = None,
                            state: str = 'open',
                            per_page: int = 30) -> List[Dict]:
        """Get repository issues, optionally filtered by labels"""

        params = {
            'state': state,
            'per_page': per_page,
            'sort': 'updated',
            'direction': 'desc'
        }

        if labels:
            params['labels'] = ','.join(labels)

        response = self.session.get(f'{self.base_url}/repos/{owner}/{repo}/issues', params=params)
        response.raise_for_status()

        # Filter out pull requests (GitHub API returns PRs as issues)
        issues = [issue for issue in response.json() if 'pull_request' not in issue]
        return issues

    def get_good_first_issues(self, owner: str, repo: str) -> List[Dict]:
        """Get issues labeled as 'good first issue' or 'help wanted'"""
        good_first_labels = ['good first issue', 'good-first-issue', 'help wanted', 'help-wanted']
        return self.get_repository_issues(owner, repo, labels=good_first_labels)

    def get_repository_languages(self, owner: str, repo: str) -> Dict:
        """Get programming languages used in repository"""
        response = self.session.get(f'{self.base_url}/repos/{owner}/{repo}/languages')
        response.raise_for_status()
        return response.json()

    def get_repository_contributors(self, owner: str, repo: str, per_page: int = 30) -> List[Dict]:
        """Get repository contributors"""
        response = self.session.get(
            f'{self.base_url}/repos/{owner}/{repo}/contributors',
            params={'per_page': per_page}
        )
        response.raise_for_status()
        return response.json()

    def get_rate_limit(self) -> Dict:
        """Get current rate limit status"""
        response = self.session.get(f'{self.base_url}/rate_limit')
        response.raise_for_status()
        return response.json()

    def save_repos_to_cache(self, repos: List[Dict], filename: str = 'data/sample_repos.json'):
        """Save repositories to local cache file"""
        os.makedirs(os.path.dirname(filename), exist_ok=True)
        with open(filename, 'w') as f:
            json.dump(repos, f, indent=2, default=str)

    def load_repos_from_cache(self, filename: str = 'data/sample_repos.json') -> List[Dict]:
        """Load repositories from local cache file"""
        try:
            with open(filename, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            return []