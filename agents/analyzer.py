from typing import List, Dict, Optional
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.github_api import GitHubAPI
from core.utils import format_issue_info, truncate_text, get_file_extension_stats
from rich.console import Console
from rich.panel import Panel

class AnalyzerAgent:
    """Agent responsible for analyzing repositories and identifying contribution opportunities"""

    def __init__(self, github_token: Optional[str] = None, anthropic_api_key: Optional[str] = None):
        self.github = GitHubAPI(github_token)
        self.console = Console()

        # Initialize Claude client if API key provided
        if anthropic_api_key:
            try:
                import anthropic
                self.claude = anthropic.Anthropic(api_key=anthropic_api_key)
                self.use_ai = True
            except ImportError:
                self.use_ai = False
                self.console.print("⚠️  [yellow]Anthropic not installed. Analysis will be rule-based only.[/yellow]")
        else:
            self.use_ai = False
            self.console.print("⚠️  [yellow]Claude API key not provided. Analysis will be rule-based only.[/yellow]")

    def analyze_repository(self, repo_info: Dict) -> Dict:
        """
        Perform comprehensive analysis of a repository

        Args:
            repo_info: Repository information from Scout agent

        Returns:
            Analysis results with contribution opportunities
        """
        self.console.print(f"🔍 [bold blue]Analyzer Agent: Analyzing {repo_info['full_name']}...[/bold blue]")

        owner, name = repo_info['full_name'].split('/')

        analysis = {
            'repository': repo_info,
            'readme_analysis': self._analyze_readme(owner, name),
            'issues_analysis': self._analyze_issues(owner, name),
            'code_structure': self._analyze_code_structure(owner, name),
            'contribution_opportunities': [],
            'health_score': 0
        }

        # Identify contribution opportunities
        analysis['contribution_opportunities'] = self._identify_opportunities(analysis)

        # Calculate health score
        analysis['health_score'] = self._calculate_health_score(analysis)

        self.console.print(f"✅ [bold green]Analysis complete for {repo_info['full_name']}[/bold green]")
        return analysis

    def _analyze_readme(self, owner: str, name: str) -> Dict:
        """Analyze repository README for gaps and opportunities"""
        readme_content = self.github.get_repository_readme(owner, name)

        if not readme_content:
            return {
                'exists': False,
                'quality_score': 0,
                'missing_sections': ['README file missing'],
                'opportunities': ['Create comprehensive README']
            }

        readme_analysis = {
            'exists': True,
            'length': len(readme_content),
            'quality_score': 0,
            'missing_sections': [],
            'opportunities': []
        }

        # Check for common README sections
        content_lower = readme_content.lower()
        required_sections = {
            'installation': ['install', 'setup', 'getting started'],
            'usage': ['usage', 'example', 'how to'],
            'contributing': ['contribut', 'development', 'pull request'],
            'license': ['license', 'copyright'],
            'documentation': ['docs', 'documentation', 'api'],
            'testing': ['test', 'testing', 'pytest']
        }

        for section, keywords in required_sections.items():
            if not any(keyword in content_lower for keyword in keywords):
                readme_analysis['missing_sections'].append(section)
                readme_analysis['opportunities'].append(f"Add {section} section")

        # Quality scoring
        base_score = 50 if readme_analysis['length'] > 500 else 20
        readme_analysis['quality_score'] = base_score - (len(readme_analysis['missing_sections']) * 10)

        # Claude-powered analysis if available
        if self.use_ai and readme_content:
            claude_analysis = self._claude_analyze_readme(readme_content)
            if claude_analysis:
                readme_analysis['claude_suggestions'] = claude_analysis

        return readme_analysis

    def _analyze_issues(self, owner: str, name: str) -> Dict:
        """Analyze repository issues for contribution opportunities"""
        try:
            # Get good first issues
            good_first_issues = self.github.get_good_first_issues(owner, name)

            # Get all open issues for broader analysis
            all_issues = self.github.get_repository_issues(owner, name, per_page=50)

            issues_analysis = {
                'total_issues': len(all_issues),
                'good_first_issues': len(good_first_issues),
                'issue_categories': self._categorize_issues(all_issues),
                'top_issues': good_first_issues[:5],  # Top 5 good first issues
                'opportunities': []
            }

            # Identify opportunities based on issue patterns
            if issues_analysis['good_first_issues'] > 0:
                issues_analysis['opportunities'].append(f"{issues_analysis['good_first_issues']} good first issues available")

            if issues_analysis['issue_categories'].get('bug', 0) > 0:
                issues_analysis['opportunities'].append(f"{issues_analysis['issue_categories']['bug']} bug fixes needed")

            if issues_analysis['issue_categories'].get('documentation', 0) > 0:
                issues_analysis['opportunities'].append(f"{issues_analysis['issue_categories']['documentation']} documentation improvements needed")

            return issues_analysis

        except Exception as e:
            self.console.print(f"❌ Error analyzing issues: {str(e)}")
            return {'total_issues': 0, 'good_first_issues': 0, 'issue_categories': {}, 'opportunities': []}

    def _categorize_issues(self, issues: List[Dict]) -> Dict[str, int]:
        """Categorize issues by type"""
        categories = {
            'bug': 0,
            'feature': 0,
            'documentation': 0,
            'testing': 0,
            'enhancement': 0,
            'help wanted': 0
        }

        for issue in issues:
            labels = [label['name'].lower() for label in issue.get('labels', [])]
            title_lower = issue['title'].lower()

            if any(keyword in ' '.join(labels + [title_lower]) for keyword in ['bug', 'error', 'fix']):
                categories['bug'] += 1
            elif any(keyword in ' '.join(labels + [title_lower]) for keyword in ['feature', 'enhancement']):
                categories['feature'] += 1
            elif any(keyword in ' '.join(labels + [title_lower]) for keyword in ['doc', 'readme', 'guide']):
                categories['documentation'] += 1
            elif any(keyword in ' '.join(labels + [title_lower]) for keyword in ['test', 'coverage']):
                categories['testing'] += 1
            elif any(keyword in ' '.join(labels + [title_lower]) for keyword in ['help wanted', 'good first']):
                categories['help wanted'] += 1

        return categories

    def _analyze_code_structure(self, owner: str, name: str) -> Dict:
        """Analyze code structure and identify potential improvements"""
        try:
            languages = self.github.get_repository_languages(owner, name)
            contributors = self.github.get_repository_contributors(owner, name)

            structure_analysis = {
                'languages': languages,
                'language_stats': get_file_extension_stats(languages) if languages else "No languages detected",
                'contributor_count': len(contributors),
                'primary_language': max(languages.keys(), key=languages.get) if languages else 'Unknown',
                'opportunities': []
            }

            # Identify opportunities based on code structure
            if len(languages) == 1:
                structure_analysis['opportunities'].append("Single language project - easy to contribute")

            if structure_analysis['contributor_count'] < 5:
                structure_analysis['opportunities'].append("Small contributor base - good opportunity for impact")

            primary_lang = structure_analysis['primary_language'].lower()
            if primary_lang in ['python', 'javascript', 'typescript']:
                structure_analysis['opportunities'].append(f"{primary_lang.title()} project - popular language")

            return structure_analysis

        except Exception as e:
            self.console.print(f"❌ Error analyzing code structure: {str(e)}")
            return {'languages': {}, 'opportunities': []}

    def _identify_opportunities(self, analysis: Dict, user_preferences=None) -> List[Dict]:
        """Identify specific contribution opportunities based on repository analysis and user preferences"""
        opportunities = []

        # Load user preferences if not provided
        if not user_preferences:
            try:
                from core.user_preferences import get_user_preferences
                user_preferences = get_user_preferences()
            except:
                user_preferences = None

        # Code-focused opportunities (high impact)
        self._add_code_opportunities(opportunities, analysis)

        # Issue opportunities
        self._add_issue_opportunities(opportunities, analysis)

        # Architecture and design opportunities
        self._add_architecture_opportunities(opportunities, analysis)

        # Performance opportunities
        self._add_performance_opportunities(opportunities, analysis)

        # Security opportunities
        self._add_security_opportunities(opportunities, analysis)

        # Testing opportunities
        self._add_testing_opportunities(opportunities, analysis)

        # CI/CD opportunities
        self._add_cicd_opportunities(opportunities, analysis)

        # Documentation opportunities (lower priority by default)
        self._add_documentation_opportunities(opportunities, analysis)

        # Filter and score opportunities based on user preferences
        if user_preferences:
            opportunities = self._filter_by_preferences(opportunities, user_preferences)

        return opportunities

    def _add_code_opportunities(self, opportunities: List[Dict], analysis: Dict):
        """Add code feature and improvement opportunities"""
        issues = analysis['issues_analysis']

        # Feature requests
        feature_count = issues.get('issue_categories', {}).get('enhancement', 0)
        if feature_count > 0:
            opportunities.append({
                'type': 'code_features',
                'title': f'Feature Requests ({feature_count} open)',
                'description': 'Implement new features requested by the community',
                'priority': 'high',
                'effort': 'medium',
                'impact': 'high',
                'technical_complexity': 'medium'
            })

        # API improvements
        if 'api' in analysis['repository'].get('description', '').lower():
            opportunities.append({
                'type': 'api_design',
                'title': 'API Design Improvements',
                'description': 'Enhance API design, endpoints, or developer experience',
                'priority': 'medium',
                'effort': 'medium',
                'impact': 'high',
                'technical_complexity': 'medium'
            })

    def _add_issue_opportunities(self, opportunities: List[Dict], analysis: Dict):
        """Add issue-based opportunities"""
        issues = analysis['issues_analysis']
        good_first_issues = issues['top_issues']

        if len(good_first_issues) > 0:
            for issue in good_first_issues[:3]:  # Top 3
                opportunities.append({
                    'type': 'bug_fixes',
                    'title': f"Issue #{issue['number']}: {truncate_text(issue['title'], 50)}",
                    'description': truncate_text(issue['title'], 100),
                    'priority': 'high',
                    'effort': 'varies',
                    'impact': 'medium',
                    'technical_complexity': 'low',
                    'issue_url': issue['html_url']
                })

        # Bug fixes
        bug_count = issues.get('issue_categories', {}).get('bug', 0)
        if bug_count > 0:
            opportunities.append({
                'type': 'bug_fixes',
                'title': f'Bug Fixes ({bug_count} open bugs)',
                'description': 'Help resolve bugs and improve software reliability',
                'priority': 'high',
                'effort': 'medium',
                'impact': 'high',
                'technical_complexity': 'medium'
            })

    def _add_architecture_opportunities(self, opportunities: List[Dict], analysis: Dict):
        """Add architecture and design opportunities"""
        code_structure = analysis['code_structure']

        # Large files that might need refactoring
        if code_structure.get('contributor_count', 0) > 2:
            opportunities.append({
                'type': 'refactoring',
                'title': 'Code Refactoring',
                'description': 'Improve code structure and maintainability',
                'priority': 'medium',
                'effort': 'medium',
                'impact': 'medium',
                'technical_complexity': 'high'
            })

        # Architecture improvements for larger projects
        stars = analysis['repository'].get('stars', 0)
        if stars > 1000:
            opportunities.append({
                'type': 'architecture',
                'title': 'Architecture Improvements',
                'description': 'Design improvements for scalability and maintainability',
                'priority': 'medium',
                'effort': 'high',
                'impact': 'high',
                'technical_complexity': 'high'
            })

    def _add_performance_opportunities(self, opportunities: List[Dict], analysis: Dict):
        """Add performance-related opportunities"""
        # For data-heavy or computation projects
        description = analysis['repository'].get('description', '').lower()
        if any(keyword in description for keyword in ['data', 'ml', 'algorithm', 'compute']):
            opportunities.append({
                'type': 'performance',
                'title': 'Algorithm/Data Processing Optimization',
                'description': 'Optimize algorithms and data processing workflows',
                'priority': 'medium',
                'effort': 'high',
                'impact': 'high',
                'technical_complexity': 'high'
            })

    def _add_security_opportunities(self, opportunities: List[Dict], analysis: Dict):
        """Add security-related opportunities"""
        # Security issues
        issues = analysis['issues_analysis']
        security_count = issues.get('issue_categories', {}).get('security', 0)

        if security_count > 0:
            opportunities.append({
                'type': 'security',
                'title': f'Security Fixes ({security_count} issues)',
                'description': 'Address security vulnerabilities and improve safety',
                'priority': 'high',
                'effort': 'medium',
                'impact': 'high',
                'technical_complexity': 'medium'
            })

    def _add_testing_opportunities(self, opportunities: List[Dict], analysis: Dict):
        """Add testing opportunities"""
        code_structure = analysis['code_structure']

        # Missing test categories
        if code_structure.get('contributor_count', 0) < 3:
            opportunities.append({
                'type': 'testing',
                'title': 'Add Unit Tests',
                'description': 'Small project likely needs more test coverage',
                'priority': 'medium',
                'effort': 'medium',
                'impact': 'high',
                'technical_complexity': 'low'
            })

    def _add_cicd_opportunities(self, opportunities: List[Dict], analysis: Dict):
        """Add CI/CD opportunities"""
        # For projects without automated workflows
        stars = analysis['repository'].get('stars', 0)
        if stars > 100:  # Only suggest for established projects
            opportunities.append({
                'type': 'ci_cd',
                'title': 'Set up CI/CD Pipeline',
                'description': 'Add automated testing, building, and deployment',
                'priority': 'low',
                'effort': 'medium',
                'impact': 'medium',
                'technical_complexity': 'medium'
            })

    def _add_documentation_opportunities(self, opportunities: List[Dict], analysis: Dict):
        """Add documentation opportunities (typically lower priority)"""
        # Only add critical README opportunities
        if not analysis['readme_analysis']['exists']:
            opportunities.append({
                'type': 'documentation',
                'priority': 'high',
                'title': 'Create README file',
                'description': 'Repository is missing a README file',
                'effort': 'medium',
                'impact': 'high',
                'technical_complexity': 'low'
            })

        # Only add high-impact documentation
        missing_sections = analysis['readme_analysis']['missing_sections']
        high_impact_sections = ['installation', 'usage', 'api']

        for missing_section in missing_sections:
            if missing_section.lower() in high_impact_sections:
                opportunities.append({
                    'type': 'documentation',
                    'title': f'Add {missing_section} section to README',
                    'description': f'README is missing critical {missing_section} information',
                    'priority': 'medium',
                    'effort': 'low',
                    'impact': 'medium',
                    'technical_complexity': 'low'
                })

    def _filter_by_preferences(self, opportunities: List[Dict], user_preferences) -> List[Dict]:
        """Filter and score opportunities based on user preferences"""
        filtered_opportunities = []

        for opp in opportunities:
            # Skip if user wants to avoid this type
            if user_preferences.should_avoid_contribution(opp['type'], []):
                continue

            # Calculate preference score
            base_score = self._calculate_base_opportunity_score(opp)
            user_score = user_preferences.get_contribution_score(opp['type'], base_score)

            # Only include opportunities with reasonable scores
            if user_score >= 0.3:  # Threshold for inclusion
                opp['user_preference_score'] = user_score
                filtered_opportunities.append(opp)

        # Sort by user preference score
        return sorted(filtered_opportunities, key=lambda x: x.get('user_preference_score', 0), reverse=True)

    def _calculate_base_opportunity_score(self, opp: Dict) -> float:
        """Calculate base score for an opportunity"""
        impact_scores = {'low': 0.3, 'medium': 0.6, 'high': 0.9}
        priority_scores = {'low': 0.2, 'medium': 0.5, 'high': 0.8}
        effort_scores = {'low': 0.8, 'medium': 0.6, 'high': 0.4}  # Lower effort = higher score

        impact = impact_scores.get(opp.get('impact', 'medium'), 0.6)
        priority = priority_scores.get(opp.get('priority', 'medium'), 0.5)
        effort = effort_scores.get(opp.get('effort', 'medium'), 0.6)

        return (impact * 0.4) + (priority * 0.3) + (effort * 0.3)

    def _calculate_health_score(self, analysis: Dict) -> int:
        """Calculate repository health score (0-100)"""
        score = 50  # Base score

        # README quality
        score += min(analysis['readme_analysis']['quality_score'], 20)

        # Issue management
        if analysis['issues_analysis']['good_first_issues'] > 0:
            score += 15

        if analysis['issues_analysis']['total_issues'] > 0:
            score += 10

        # Code structure
        if analysis['code_structure']['contributor_count'] > 1:
            score += 5

        return min(score, 100)

    def display_analysis(self, analysis: Dict) -> None:
        """Display analysis results in a formatted way"""
        repo_name = analysis['repository']['full_name']

        # Repository overview
        self.console.print(Panel(
            f"[bold cyan]{repo_name}[/bold cyan]\n"
            f"⭐ Stars: {analysis['repository']['stars']}\n"
            f"🔧 Language: {analysis['repository']['language']}\n"
            f"📊 Health Score: {analysis['health_score']}/100",
            title="📊 Repository Overview"
        ))

        # README Analysis
        readme = analysis['readme_analysis']
        readme_status = "✅ Good" if readme['quality_score'] > 70 else "⚠️ Needs improvement" if readme['exists'] else "❌ Missing"
        self.console.print(Panel(
            f"Status: {readme_status}\n"
            f"Quality Score: {readme['quality_score']}/100\n"
            f"Missing Sections: {', '.join(readme['missing_sections']) if readme['missing_sections'] else 'None'}",
            title="📝 README Analysis"
        ))

        # Issues Analysis
        issues = analysis['issues_analysis']
        self.console.print(Panel(
            f"Total Issues: {issues['total_issues']}\n"
            f"Good First Issues: {issues['good_first_issues']}\n"
            f"Bug Issues: {issues['issue_categories'].get('bug', 0)}\n"
            f"Documentation Issues: {issues['issue_categories'].get('documentation', 0)}",
            title="🐛 Issues Analysis"
        ))

        # Top Opportunities
        if analysis['contribution_opportunities']:
            opportunities_text = "\n".join([
                f"• {opp['title']} ({opp['priority']} priority)"
                for opp in analysis['contribution_opportunities'][:5]
            ])
            self.console.print(Panel(
                opportunities_text,
                title="🎯 Top Contribution Opportunities"
            ))

    def _claude_analyze_readme(self, readme_content: str) -> Optional[Dict]:
        """Use Claude to analyze README quality and suggest improvements"""
        if not self.use_ai:
            return None

        try:
            prompt = f"""Please analyze this README file and provide specific improvement suggestions.

README Content:
{truncate_text(readme_content, 3000)}

Please evaluate:
1. Overall clarity and completeness (score 1-10)
2. Top 3 specific improvements needed
3. Missing sections that would benefit users
4. Any confusing or unclear parts

Respond in JSON format:
{{
    "clarity_score": <1-10>,
    "completeness_score": <1-10>,
    "top_improvements": ["improvement 1", "improvement 2", "improvement 3"],
    "missing_sections": ["section 1", "section 2"],
    "unclear_parts": ["issue 1", "issue 2"]
}}"""

            response = self.claude.messages.create(
                model="claude-3-haiku-20240307",
                max_tokens=1000,
                temperature=0.3,
                messages=[{
                    "role": "user",
                    "content": prompt
                }]
            )

            # Parse Claude's response
            import json
            try:
                analysis = json.loads(response.content[0].text)
                return analysis
            except json.JSONDecodeError:
                # If JSON parsing fails, create a simple analysis
                return {
                    "clarity_score": 7,
                    "completeness_score": 6,
                    "top_improvements": ["Improve documentation clarity", "Add more examples", "Better organization"],
                    "missing_sections": ["FAQ", "Troubleshooting"],
                    "analysis_text": response.content[0].text
                }

        except Exception as e:
            self.console.print(f"❌ Claude analysis failed: {str(e)}")
            return None

if __name__ == "__main__":
    # Example usage
    analyzer = AnalyzerAgent()

    # Sample repository info (would come from Scout agent)
    sample_repo = {
        'full_name': 'example/sample-repo',
        'language': 'Python',
        'stars': 150,
        'description': 'A sample repository for testing'
    }

    analysis = analyzer.analyze_repository(sample_repo)
    analyzer.display_analysis(analysis)