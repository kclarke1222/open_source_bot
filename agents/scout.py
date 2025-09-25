from typing import List, Dict, Optional
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.github_api import GitHubAPI
from core.utils import format_repo_info, save_json
from rich.console import Console
from rich.table import Table

class ScoutAgent:
    """Agent responsible for discovering suitable repositories for contributions"""

    def __init__(self, github_token: Optional[str] = None):
        self.github = GitHubAPI(github_token)
        self.console = Console()

    def discover_repositories(self,
                            languages: List[str] = None,
                            topics: List[str] = None,
                            min_stars: int = 50,
                            max_results: int = 20) -> List[Dict]:
        """
        Discover repositories based on user preferences

        Args:
            languages: List of programming languages to search for
            topics: List of topics/tags to search for
            min_stars: Minimum number of stars
            max_results: Maximum number of repositories to return

        Returns:
            List of repository dictionaries
        """
        self.console.print("🔍 [bold blue]Scout Agent: Searching for repositories...[/bold blue]")

        # Auto-load user preferences if no parameters provided
        if not languages or not min_stars:
            try:
                from core.user_preferences import UserPreferenceManager
                preference_manager = UserPreferenceManager()
                user_prefs = preference_manager.preferences

                if not languages:
                    languages = user_prefs.languages
                if not min_stars:
                    min_stars = user_prefs.min_stars

                self.console.print("📋 [dim]Using your saved preferences for repository search[/dim]")

            except Exception as e:
                self.console.print(f"⚠️ [yellow]Could not load user preferences: {e}[/yellow]")
                languages = languages or ['Python']
                min_stars = min_stars or 50

        all_repos = []

        # Search for each language/topic combination
        for language in languages:
            try:
                search_results = self.github.search_repositories(
                    language=language,
                    min_stars=min_stars,
                    per_page=min(max_results, 30)
                )

                repos = search_results.get('items', [])
                all_repos.extend(repos)

                self.console.print(f"  Found {len(repos)} repositories for {language}")

                # If we have topics, do additional searches
                if topics:
                    for topic in topics:
                        topic_results = self.github.search_repositories(
                            language=language,
                            topic=topic,
                            min_stars=min_stars,
                            per_page=10
                        )
                        topic_repos = topic_results.get('items', [])
                        all_repos.extend(topic_repos)

                        self.console.print(f"  Found {len(topic_repos)} repositories for {language} + {topic}")

            except Exception as e:
                self.console.print(f"❌ Error searching for {language}: {str(e)}")
                continue

        # Remove duplicates and filter
        unique_repos = self._remove_duplicates(all_repos)
        filtered_repos = self._filter_repositories(unique_repos)

        # Sort by relevance (combination of stars, recent activity, and good first issues)
        scored_repos = self._score_repositories(filtered_repos[:max_results])

        self.console.print(f"✅ [bold green]Found {len(scored_repos)} suitable repositories[/bold green]")
        return scored_repos

    def _remove_duplicates(self, repos: List[Dict]) -> List[Dict]:
        """Remove duplicate repositories"""
        seen = set()
        unique = []
        for repo in repos:
            repo_id = repo['full_name']
            if repo_id not in seen:
                seen.add(repo_id)
                unique.append(repo)
        return unique

    def _filter_repositories(self, repos: List[Dict]) -> List[Dict]:
        """Filter repositories based on contribution-friendly criteria"""
        filtered = []

        for repo in repos:
            # Skip repositories that are less likely to accept contributions
            if (repo.get('archived', False) or
                repo.get('fork', True) or
                repo.get('private', True)):
                continue

            # Prefer repositories with recent activity (within last 6 months)
            from datetime import datetime, timedelta
            updated_at = datetime.strptime(repo['updated_at'], '%Y-%m-%dT%H:%M:%SZ')
            six_months_ago = datetime.now() - timedelta(days=180)

            if updated_at < six_months_ago:
                continue

            # Prefer repositories with reasonable size (not too small, not too large)
            if repo.get('stargazers_count', 0) < 10:
                continue

            filtered.append(repo)

        return filtered

    def _score_repositories(self, repos: List[Dict], user_preferences=None) -> List[Dict]:
        """Score repositories based on contribution potential and user preferences"""
        from core.user_preferences import get_user_preferences

        if not user_preferences:
            try:
                user_preferences = get_user_preferences()
            except:
                # Fallback to basic scoring if preferences not available
                return self._basic_score_repositories(repos)

        for repo in repos:
            score = 0

            # Factor 1: Stars within user's preferred range
            stars = repo.get('stargazers_count', 0)
            min_stars = getattr(user_preferences, 'min_stars', 50)
            max_stars = getattr(user_preferences, 'max_stars', 50000)

            if min_stars <= stars <= max_stars:
                if stars > 5000:
                    score += 4  # High visibility
                elif stars > 1000:
                    score += 3  # Good visibility
                elif stars > 100:
                    score += 2  # Moderate visibility
                else:
                    score += 1
            elif stars < min_stars:
                score -= 1  # Too small
            elif stars > max_stars:
                score -= 2  # Too large/intimidating

            # Factor 2: Recent activity (weighted by user preference)
            from datetime import datetime
            updated_at = datetime.strptime(repo['updated_at'], '%Y-%m-%dT%H:%M:%SZ')
            days_since_update = (datetime.now() - updated_at).days

            activity_multiplier = 1.5 if getattr(user_preferences, 'prefer_active_projects', True) else 1.0

            if days_since_update < 7:
                score += int(3 * activity_multiplier)
            elif days_since_update < 30:
                score += int(2 * activity_multiplier)
            elif days_since_update < 90:
                score += int(1 * activity_multiplier)

            # Factor 3: Open issues analysis
            open_issues = repo.get('open_issues_count', 0)
            preferred_size = getattr(user_preferences, 'preferred_project_size', 'medium')

            if preferred_size == 'small' and 1 <= open_issues <= 20:
                score += 3
            elif preferred_size == 'medium' and 5 <= open_issues <= 100:
                score += 3
            elif preferred_size == 'large' and open_issues > 50:
                score += 2
            elif open_issues > 0:
                score += 1

            # Factor 4: Language preference matching
            language = repo.get('language')
            if language:
                language_lower = language.lower()
                user_languages = [lang.lower() for lang in getattr(user_preferences, 'languages', [])]
                if language_lower in user_languages:
                    # Higher score for preferred languages
                    primary_lang_index = user_languages.index(language_lower) if language_lower in user_languages else len(user_languages)
                    score += max(3 - primary_lang_index, 1)

            # Factor 5: Topic/keyword analysis (avoid disliked topics)
            description = repo.get('description') or ''
            repo_topics = repo.get('topics', []) + [description.lower()]
            avoid_topics = getattr(user_preferences, 'avoid_topics', set())

            if any(topic in ' '.join(repo_topics) for topic in avoid_topics):
                score -= 3  # Penalize avoided topics

            # Factor 6: Fork ratio (prefer original projects)
            forks = repo.get('forks_count', 0)
            if forks > 0 and stars > 0:
                fork_ratio = forks / stars
                if fork_ratio > 0.1:  # Good fork ratio indicates useful project
                    score += 1

            # Factor 7: Has good first issues or contributor-friendly labels
            # This would require additional API calls, so we estimate based on size and activity
            if 100 <= stars <= 10000 and days_since_update < 30:
                score += 1  # Likely to have good first issues

            repo['contribution_score'] = max(score, 0)  # Ensure non-negative

        # Sort by score (descending)
        return sorted(repos, key=lambda x: x.get('contribution_score', 0), reverse=True)

    def _basic_score_repositories(self, repos: List[Dict]) -> List[Dict]:
        """Basic scoring when user preferences aren't available"""
        for repo in repos:
            score = 0

            # Factor 1: Stars (indicates popularity and potential impact)
            stars = repo.get('stargazers_count', 0)
            if stars > 1000:
                score += 3
            elif stars > 100:
                score += 2
            else:
                score += 1

            # Factor 2: Recent activity
            from datetime import datetime
            updated_at = datetime.strptime(repo['updated_at'], '%Y-%m-%dT%H:%M:%SZ')
            days_since_update = (datetime.now() - updated_at).days
            if days_since_update < 7:
                score += 3
            elif days_since_update < 30:
                score += 2
            elif days_since_update < 90:
                score += 1

            # Factor 3: Open issues (indicates active development)
            open_issues = repo.get('open_issues_count', 0)
            if 5 <= open_issues <= 50:  # Sweet spot
                score += 2
            elif open_issues > 0:
                score += 1

            # Factor 4: Language preference (can be customized)
            language = repo.get('language')
            if language and language.lower() in ['python', 'javascript', 'typescript']:
                score += 1

            repo['contribution_score'] = score

        # Sort by score (descending)
        return sorted(repos, key=lambda x: x.get('contribution_score', 0), reverse=True)

    def display_repositories(self, repos: List[Dict]) -> None:
        """Display repositories in a formatted table"""
        if not repos:
            self.console.print("❌ No repositories found")
            return

        table = Table(title="🔍 Discovered Repositories")
        table.add_column("Repository", style="cyan", width=30)
        table.add_column("Stars", justify="right", style="magenta")
        table.add_column("Language", style="green")
        table.add_column("Updated", style="yellow")
        table.add_column("Score", justify="right", style="red")

        for repo in repos[:10]:  # Show top 10
            table.add_row(
                repo['full_name'],
                str(repo.get('stargazers_count', 0)),
                repo.get('language', 'N/A'),
                repo['updated_at'][:10],
                str(repo.get('contribution_score', 0))
            )

        self.console.print(table)

    def get_repository_quick_info(self, repo: Dict) -> Dict:
        """Get quick information about a repository for analysis"""
        try:
            owner, name = repo['full_name'].split('/')

            # Get additional details
            details = self.github.get_repository_details(owner, name)
            languages = self.github.get_repository_languages(owner, name)

            quick_info = {
                'full_name': repo['full_name'],
                'description': repo.get('description'),
                'language': repo.get('language'),
                'languages': languages,
                'stars': repo.get('stargazers_count'),
                'forks': repo.get('forks_count'),
                'open_issues': repo.get('open_issues_count'),
                'updated_at': repo.get('updated_at'),
                'url': repo.get('html_url'),
                'has_issues': details.get('has_issues', False),
                'has_wiki': details.get('has_wiki', False),
                'default_branch': details.get('default_branch', 'main'),
                'contribution_score': repo.get('contribution_score', 0)
            }

            return quick_info

        except Exception as e:
            self.console.print(f"❌ Error getting info for {repo['full_name']}: {str(e)}")
            return None

    def save_discovered_repos(self, repos: List[Dict], filename: str = 'data/discovered_repos.json'):
        """Save discovered repositories to file"""
        save_json(repos, filename)
        self.console.print(f"💾 Saved {len(repos)} repositories to {filename}")

if __name__ == "__main__":
    # Example usage
    scout = ScoutAgent()

    # Discover Python data engineering repositories
    repos = scout.discover_repositories(
        languages=['Python'],
        topics=['data-engineering', 'machine-learning'],
        min_stars=100,
        max_results=15
    )

    scout.display_repositories(repos)

    # Save for other agents to use
    scout.save_discovered_repos(repos)