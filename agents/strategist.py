from typing import List, Dict, Optional
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.utils import save_json, load_json
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
import random

class StrategistAgent:
    """Agent responsible for planning contribution strategies and prioritizing opportunities"""

    def __init__(self, anthropic_api_key: Optional[str] = None):
        self.console = Console()

        # Initialize Claude client if API key provided
        if anthropic_api_key:
            try:
                import anthropic
                self.claude = anthropic.Anthropic(api_key=anthropic_api_key)
                self.use_ai = True
            except ImportError:
                self.use_ai = False
                self.console.print("⚠️  [yellow]Anthropic not installed. Strategy will be rule-based only.[/yellow]")
        else:
            self.use_ai = False
            self.console.print("⚠️  [yellow]Claude API key not provided. Strategy will be rule-based only.[/yellow]")

    def create_contribution_strategy(self, analysis: Dict, user_preferences: Dict = None) -> Dict:
        """
        Create a comprehensive contribution strategy based on repository analysis

        Args:
            analysis: Repository analysis from Analyzer agent
            user_preferences: User preferences (skills, time, interests)

        Returns:
            Strategic plan with prioritized contributions
        """
        self.console.print(f"🎯 [bold blue]Strategist Agent: Planning contributions for {analysis['repository']['full_name']}...[/bold blue]")

        # Set default preferences if none provided
        if not user_preferences:
            user_preferences = {
                'skill_level': 'intermediate',
                'available_time': 'medium',  # low, medium, high
                'preferred_types': ['documentation', 'bug fixes', 'testing'],
                'languages': ['Python', 'JavaScript']
            }

        strategy = {
            'repository': analysis['repository']['full_name'],
            'analysis_summary': self._summarize_analysis(analysis),
            'prioritized_opportunities': self._prioritize_opportunities(analysis, user_preferences),
            'contribution_plan': [],
            'risk_assessment': self._assess_risks(analysis),
            'success_probability': 0,
            'recommendations': []
        }

        # Create detailed contribution plan
        strategy['contribution_plan'] = self._create_contribution_plan(
            strategy['prioritized_opportunities'], user_preferences
        )

        # Calculate success probability
        strategy['success_probability'] = self._calculate_success_probability(analysis, user_preferences)

        # Generate strategic recommendations
        strategy['recommendations'] = self._generate_recommendations(analysis, user_preferences)

        # Enhance strategy with Claude if available
        strategy = self._claude_enhance_strategy(strategy, analysis, user_preferences)

        self.console.print(f"✅ [bold green]Strategy created for {analysis['repository']['full_name']}[/bold green]")
        return strategy

    def _summarize_analysis(self, analysis: Dict) -> Dict:
        """Summarize key insights from repository analysis"""
        return {
            'health_score': analysis['health_score'],
            'total_opportunities': len(analysis['contribution_opportunities']),
            'primary_language': analysis['code_structure'].get('primary_language', 'Unknown'),
            'good_first_issues': analysis['issues_analysis']['good_first_issues'],
            'documentation_gaps': len(analysis['readme_analysis']['missing_sections']),
            'contributor_friendliness': self._assess_contributor_friendliness(analysis)
        }

    def _assess_contributor_friendliness(self, analysis: Dict) -> str:
        """Assess how friendly the repository is to new contributors"""
        score = 0

        # README quality
        if analysis['readme_analysis']['exists']:
            score += 2
        if analysis['readme_analysis']['quality_score'] > 70:
            score += 2

        # Good first issues
        if analysis['issues_analysis']['good_first_issues'] > 0:
            score += 3
        if analysis['issues_analysis']['good_first_issues'] > 5:
            score += 2

        # Active maintenance
        if analysis['repository']['stars'] > 100:
            score += 1

        if score >= 7:
            return "Very Friendly"
        elif score >= 5:
            return "Moderately Friendly"
        elif score >= 3:
            return "Somewhat Friendly"
        else:
            return "Not Very Friendly"

    def _prioritize_opportunities(self, analysis: Dict, user_preferences: Dict) -> List[Dict]:
        """Prioritize contribution opportunities based on analysis and user preferences"""
        opportunities = analysis['contribution_opportunities'].copy()

        for opp in opportunities:
            priority_score = self._calculate_priority_score(opp, user_preferences)
            opp['priority_score'] = priority_score

        # Sort by priority score (higher is better)
        return sorted(opportunities, key=lambda x: x['priority_score'], reverse=True)

    def _calculate_priority_score(self, opportunity: Dict, user_preferences: Dict) -> float:
        """Calculate priority score for an opportunity"""
        score = 0.0

        # Base score based on impact and effort
        impact_scores = {'low': 1, 'medium': 2, 'high': 3}
        effort_scores = {'low': 3, 'medium': 2, 'high': 1, 'varies': 2}

        score += impact_scores.get(opportunity.get('impact', 'medium'), 2) * 2
        score += effort_scores.get(opportunity.get('effort', 'medium'), 2)

        # User preference matching
        if opportunity['type'] in user_preferences.get('preferred_types', []):
            score += 2

        # Priority weighting
        priority_weights = {'high': 3, 'medium': 2, 'low': 1}
        score += priority_weights.get(opportunity.get('priority', 'medium'), 2)

        # Skill level matching
        skill_level = user_preferences.get('skill_level', 'intermediate')
        if skill_level == 'beginner' and opportunity.get('effort') == 'low':
            score += 1
        elif skill_level == 'advanced' and opportunity.get('impact') == 'high':
            score += 1

        return score

    def _create_contribution_plan(self, opportunities: List[Dict], user_preferences: Dict) -> List[Dict]:
        """Create a detailed contribution plan with timeline"""
        plan = []
        available_time = user_preferences.get('available_time', 'medium')

        # Determine how many contributions to plan based on available time
        max_contributions = {
            'low': 2,
            'medium': 4,
            'high': 6
        }

        selected_opportunities = opportunities[:max_contributions.get(available_time, 4)]

        for i, opp in enumerate(selected_opportunities, 1):
            plan_item = {
                'step': i,
                'opportunity': opp,
                'estimated_timeline': self._estimate_timeline(opp, user_preferences),
                'prerequisites': self._identify_prerequisites(opp),
                'success_metrics': self._define_success_metrics(opp),
                'potential_challenges': self._identify_challenges(opp)
            }
            plan.append(plan_item)

        return plan

    def _estimate_timeline(self, opportunity: Dict, user_preferences: Dict) -> str:
        """Estimate timeline for completing an opportunity"""
        effort = opportunity.get('effort', 'medium')
        skill_level = user_preferences.get('skill_level', 'intermediate')
        available_time = user_preferences.get('available_time', 'medium')

        # Base estimates in days
        base_estimates = {
            'low': 2,
            'medium': 5,
            'high': 10,
            'varies': 7
        }

        base_days = base_estimates.get(effort, 5)

        # Adjust for skill level
        skill_multipliers = {
            'beginner': 1.5,
            'intermediate': 1.0,
            'advanced': 0.7
        }

        # Adjust for available time
        time_multipliers = {
            'low': 2.0,
            'medium': 1.0,
            'high': 0.6
        }

        adjusted_days = base_days * skill_multipliers.get(skill_level, 1.0) * time_multipliers.get(available_time, 1.0)

        if adjusted_days <= 3:
            return "1-3 days"
        elif adjusted_days <= 7:
            return "3-7 days"
        elif adjusted_days <= 14:
            return "1-2 weeks"
        else:
            return "2+ weeks"

    def _identify_prerequisites(self, opportunity: Dict) -> List[str]:
        """Identify prerequisites for an opportunity"""
        prerequisites = []

        if opportunity['type'] == 'issue':
            prerequisites.extend([
                "Read issue description thoroughly",
                "Set up local development environment",
                "Reproduce the issue locally"
            ])
        elif opportunity['type'] == 'documentation':
            prerequisites.extend([
                "Review existing documentation structure",
                "Understand the project's documentation style"
            ])
        elif opportunity['type'] == 'testing':
            prerequisites.extend([
                "Understand the testing framework used",
                "Review existing test structure"
            ])

        return prerequisites

    def _define_success_metrics(self, opportunity: Dict) -> List[str]:
        """Define success metrics for an opportunity"""
        metrics = []

        if opportunity['type'] == 'issue':
            metrics.extend([
                "Issue is resolved and closed",
                "Pull request is merged",
                "No regression introduced"
            ])
        elif opportunity['type'] == 'documentation':
            metrics.extend([
                "Documentation is clear and comprehensive",
                "Community feedback is positive",
                "Reduces future questions about the topic"
            ])
        elif opportunity['type'] == 'testing':
            metrics.extend([
                "Code coverage increases",
                "Tests pass consistently",
                "Edge cases are covered"
            ])

        return metrics

    def _identify_challenges(self, opportunity: Dict) -> List[str]:
        """Identify potential challenges for an opportunity"""
        challenges = []

        general_challenges = [
            "Understanding codebase conventions",
            "Getting maintainer approval",
            "Handling merge conflicts"
        ]

        if opportunity['type'] == 'issue':
            challenges.extend([
                "Issue might be more complex than it appears",
                "Solution might require extensive changes",
                "Someone else might be working on it"
            ])
        elif opportunity['type'] == 'documentation':
            challenges.extend([
                "Ensuring accuracy of information",
                "Matching project's tone and style",
                "Keeping documentation up-to-date"
            ])

        challenges.extend(random.sample(general_challenges, 2))
        return challenges

    def _assess_risks(self, analysis: Dict) -> Dict:
        """Assess risks associated with contributing to this repository"""
        risks = {
            'low_maintainer_activity': False,
            'complex_codebase': False,
            'strict_review_process': False,
            'documentation_gaps': False,
            'risk_level': 'Low'
        }

        # Check for risk indicators
        if analysis['repository']['stars'] > 10000:
            risks['strict_review_process'] = True

        if len(analysis['readme_analysis']['missing_sections']) > 3:
            risks['documentation_gaps'] = True

        if analysis['code_structure']['contributor_count'] < 2:
            risks['low_maintainer_activity'] = True

        # Calculate overall risk level
        risk_count = sum(1 for v in risks.values() if v is True)
        if risk_count >= 3:
            risks['risk_level'] = 'High'
        elif risk_count >= 2:
            risks['risk_level'] = 'Medium'

        return risks

    def _calculate_success_probability(self, analysis: Dict, user_preferences: Dict) -> float:
        """Calculate probability of successful contribution"""
        base_probability = 0.6

        # Positive factors
        if analysis['issues_analysis']['good_first_issues'] > 0:
            base_probability += 0.2

        if analysis['health_score'] > 70:
            base_probability += 0.15

        if analysis['repository']['language'] and analysis['repository']['language'].lower() in [lang.lower() for lang in user_preferences.get('languages', [])]:
            base_probability += 0.1

        # Negative factors
        if analysis['repository']['stars'] > 50000:  # Very large projects can be intimidating
            base_probability -= 0.1

        if len(analysis['readme_analysis']['missing_sections']) > 4:
            base_probability -= 0.05

        return min(max(base_probability, 0.1), 0.95)

    def _generate_recommendations(self, analysis: Dict, user_preferences: Dict) -> List[str]:
        """Generate strategic recommendations"""
        recommendations = []

        # Repository-specific recommendations
        if analysis['issues_analysis']['good_first_issues'] > 0:
            recommendations.append("Start with 'good first issue' labeled issues for easier entry")

        if len(analysis['readme_analysis']['missing_sections']) > 2:
            recommendations.append("Documentation contributions are likely to be well-received")

        if analysis['code_structure']['contributor_count'] < 5:
            recommendations.append("Small contributor base means more visibility for your contributions")

        # User-specific recommendations
        skill_level = user_preferences.get('skill_level', 'intermediate')
        if skill_level == 'beginner':
            recommendations.append("Focus on documentation and small bug fixes initially")
        elif skill_level == 'advanced':
            recommendations.append("Consider tackling complex issues or architectural improvements")

        # General recommendations
        recommendations.extend([
            "Engage with the community through issues before submitting PRs",
            "Follow the project's contribution guidelines carefully",
            "Start small and build reputation before taking on larger tasks"
        ])

        return recommendations

    def display_strategy(self, strategy: Dict) -> None:
        """Display the contribution strategy in a formatted way"""
        repo_name = strategy['repository']

        # Strategy Overview
        summary = strategy['analysis_summary']
        self.console.print(Panel(
            f"[bold cyan]{repo_name}[/bold cyan]\n"
            f"🎯 Success Probability: {strategy['success_probability']:.1%}\n"
            f"📊 Health Score: {summary['health_score']}/100\n"
            f"🤝 Contributor Friendliness: {summary['contributor_friendliness']}\n"
            f"🔍 Total Opportunities: {summary['total_opportunities']}",
            title="🎯 Contribution Strategy Overview"
        ))

        # Top Opportunities Table
        if strategy['prioritized_opportunities']:
            table = Table(title="🏆 Top Contribution Opportunities")
            table.add_column("Priority", style="red", width=8)
            table.add_column("Type", style="cyan", width=12)
            table.add_column("Title", style="green", width=40)
            table.add_column("Effort", style="yellow", width=8)
            table.add_column("Impact", style="magenta", width=8)

            for opp in strategy['prioritized_opportunities'][:5]:
                table.add_row(
                    opp.get('priority', 'medium').title(),
                    opp['type'].title(),
                    opp['title'][:40] + '...' if len(opp['title']) > 40 else opp['title'],
                    opp.get('effort', 'medium').title(),
                    opp.get('impact', 'medium').title()
                )

            self.console.print(table)

        # Contribution Plan
        if strategy['contribution_plan']:
            plan_text = ""
            for item in strategy['contribution_plan'][:3]:
                opp = item['opportunity']
                plan_text += f"[bold]{item['step']}. {opp['title']}[/bold]\n"
                plan_text += f"   📅 Timeline: {item['estimated_timeline']}\n"
                plan_text += f"   🎯 Type: {opp['type'].title()}\n\n"

            self.console.print(Panel(
                plan_text.strip(),
                title="📋 Contribution Plan"
            ))

        # Recommendations
        if strategy['recommendations']:
            rec_text = "\n".join([f"• {rec}" for rec in strategy['recommendations'][:5]])
            self.console.print(Panel(
                rec_text,
                title="💡 Strategic Recommendations"
            ))

    def _claude_enhance_strategy(self, strategy: Dict, analysis: Dict, user_preferences: Dict) -> Dict:
        """Use Claude to enhance and refine the contribution strategy"""
        if not self.use_ai:
            return strategy

        try:
            # Prepare context for Claude
            context = f"""Repository: {strategy['repository']}
Health Score: {analysis['health_score']}/100
User Skill Level: {user_preferences.get('skill_level', 'intermediate')}
Available Time: {user_preferences.get('available_time', 'medium')}
Preferred Types: {', '.join(user_preferences.get('preferred_types', []))}

Current Strategy Success Probability: {strategy['success_probability']:.1%}
Risk Level: {strategy['risk_assessment']['risk_level']}

Top Opportunities:
"""
            for i, opp in enumerate(strategy['prioritized_opportunities'][:3], 1):
                context += f"{i}. {opp['title']} ({opp['type']}, {opp['priority']} priority)\n"

            prompt = f"""As a strategic advisor for open source contributions, please analyze this contribution strategy and provide enhanced recommendations.

{context}

Please provide:
1. Strategic insights about the repository and opportunities
2. Risk mitigation strategies
3. Timeline optimization suggestions
4. Success probability assessment (realistic percentage)
5. 2-3 actionable recommendations to improve success chances

Format your response as JSON:
{{
    "strategic_insights": "your analysis of the situation",
    "risk_mitigation": ["strategy1", "strategy2"],
    "timeline_optimization": "suggestions for better timing",
    "success_probability_assessment": "percentage with reasoning",
    "enhanced_recommendations": ["rec1", "rec2", "rec3"]
}}"""

            response = self.claude.messages.create(
                model="claude-3-haiku-20240307",
                max_tokens=1500,
                temperature=0.3,
                messages=[{
                    "role": "user",
                    "content": prompt
                }]
            )

            # Parse Claude's response
            import json
            try:
                claude_enhancements = json.loads(response.content[0].text)

                # Enhance the strategy with Claude's insights
                strategy['claude_insights'] = claude_enhancements

                # Update recommendations with Claude's suggestions
                if 'enhanced_recommendations' in claude_enhancements:
                    strategy['recommendations'].extend(claude_enhancements['enhanced_recommendations'])

                # Update success probability if Claude provides better assessment
                if 'success_probability_assessment' in claude_enhancements:
                    # Extract percentage from Claude's assessment
                    assessment = claude_enhancements['success_probability_assessment']
                    import re
                    prob_match = re.search(r'(\d+)%', assessment)
                    if prob_match:
                        claude_probability = int(prob_match.group(1)) / 100
                        # Use average of our calculation and Claude's assessment
                        strategy['success_probability'] = (strategy['success_probability'] + claude_probability) / 2

                return strategy

            except json.JSONDecodeError:
                # If JSON parsing fails, add raw insights
                strategy['claude_insights'] = {
                    'raw_analysis': response.content[0].text,
                    'note': 'Claude provided unstructured analysis'
                }
                return strategy

        except Exception as e:
            self.console.print(f"❌ Claude strategy enhancement failed: {str(e)}")
            return strategy

    def save_strategy(self, strategy: Dict, filename: str = None) -> None:
        """Save strategy to file"""
        if not filename:
            repo_name = strategy['repository'].replace('/', '_')
            filename = f"data/strategy_{repo_name}.json"

        save_json(strategy, filename)
        self.console.print(f"💾 Strategy saved to {filename}")

if __name__ == "__main__":
    # Example usage
    strategist = StrategistAgent()

    # Sample analysis (would come from Analyzer agent)
    sample_analysis = {
        'repository': {'full_name': 'example/repo', 'stars': 150, 'language': 'Python'},
        'health_score': 75,
        'readme_analysis': {'exists': True, 'quality_score': 80, 'missing_sections': ['testing']},
        'issues_analysis': {'good_first_issues': 3, 'total_issues': 20, 'issue_categories': {'bug': 5}},
        'code_structure': {'primary_language': 'Python', 'contributor_count': 4},
        'contribution_opportunities': [
            {'type': 'documentation', 'title': 'Add testing section', 'priority': 'medium', 'effort': 'low', 'impact': 'medium'},
            {'type': 'issue', 'title': 'Fix bug #123', 'priority': 'high', 'effort': 'medium', 'impact': 'high'}
        ]
    }

    strategy = strategist.create_contribution_strategy(sample_analysis)
    strategist.display_strategy(strategy)