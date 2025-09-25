import os
import json
from typing import Dict, List, Any
from datetime import datetime

def load_config(config_path: str = '.env') -> Dict[str, str]:
    """Load configuration from environment file"""
    config = {}
    if os.path.exists(config_path):
        from dotenv import load_dotenv
        load_dotenv(config_path)

    config['ANTHROPIC_API_KEY'] = os.getenv('ANTHROPIC_API_KEY')
    config['GITHUB_TOKEN'] = os.getenv('GITHUB_TOKEN')

    return config

def format_repo_info(repo: Dict) -> str:
    """Format repository information for display"""
    return f"""
📂 {repo['full_name']} (⭐ {repo['stargazers_count']})
📝 {repo['description'] or 'No description'}
🔧 {repo['language'] or 'Unknown'}
📅 Updated: {repo['updated_at'][:10]}
🌐 {repo['html_url']}
"""

def format_issue_info(issue: Dict) -> str:
    """Format issue information for display"""
    labels = ', '.join([label['name'] for label in issue.get('labels', [])])
    return f"""
🐛 #{issue['number']}: {issue['title']}
📝 Labels: {labels}
👤 Author: {issue['user']['login']}
📅 Created: {issue['created_at'][:10]}
🌐 {issue['html_url']}
"""

def extract_repo_owner_name(repo_url: str) -> tuple:
    """Extract owner and repo name from GitHub URL"""
    # Handle both full URLs and owner/repo format
    if 'github.com' in repo_url:
        parts = repo_url.rstrip('/').split('/')
        return parts[-2], parts[-1]
    elif '/' in repo_url:
        return repo_url.split('/')
    else:
        raise ValueError(f"Invalid repo format: {repo_url}")

def save_json(data: Any, filepath: str) -> None:
    """Save data to JSON file"""
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    with open(filepath, 'w') as f:
        json.dump(data, f, indent=2, default=str)

def load_json(filepath: str) -> Any:
    """Load data from JSON file"""
    try:
        with open(filepath, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return None

def truncate_text(text: str, max_length: int = 500) -> str:
    """Truncate text to specified length"""
    if len(text) <= max_length:
        return text
    return text[:max_length] + "..."

def get_file_extension_stats(languages: Dict[str, int]) -> str:
    """Format language statistics"""
    total = sum(languages.values())
    stats = []
    for lang, bytes_count in sorted(languages.items(), key=lambda x: x[1], reverse=True):
        percentage = (bytes_count / total) * 100
        stats.append(f"{lang}: {percentage:.1f}%")
    return ", ".join(stats[:3])  # Top 3 languages