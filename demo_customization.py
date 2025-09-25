#!/usr/bin/env python3
"""
Demo script showing the enhanced customization features
"""

import os
import sys
from rich.console import Console
from rich.panel import Panel

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from core.user_preferences import UserPreferenceManager
from agents.scout import ScoutAgent
from agents.analyzer import AnalyzerAgent
from core.utils import load_config

console = Console()

def demo_customization():
    """Demo the new customization features"""
    console.print(Panel(
        "[bold green]🎯 Enhanced Customization Demo[/bold green]\n\n"
        "This demonstrates the new intelligent preference system that:\n"
        "• Filters out unwanted contribution types (like documentation)\n"
        "• Prioritizes meaningful code contributions\n"
        "• Learns from your feedback over time\n"
        "• Provides smarter repository selection",
        title="Welcome to Enhanced Open Source Agent"
    ))

    # 1. Show default preferences vs customized
    console.print("\n[bold]📊 Current User Preferences[/bold]")

    manager = UserPreferenceManager()
    prefs = manager.preferences

    # Show top 5 contribution types by preference
    sorted_prefs = sorted(
        prefs.contribution_weights.items(),
        key=lambda x: x[1],
        reverse=True
    )

    console.print("\n[cyan]Your contribution preferences (1-10 scale):[/cyan]")
    for contrib_type, weight in sorted_prefs[:5]:
        rating = int(weight * 10)
        type_name = contrib_type.replace('_', ' ').title()
        bar = "█" * rating + "░" * (10 - rating)
        console.print(f"  {type_name:<20} {bar} ({rating}/10)")

    if prefs.avoid_types:
        console.print(f"\n[red]❌ You're avoiding: {', '.join(prefs.avoid_types)}[/red]")

    # 2. Demo repository discovery with preferences
    console.print(f"\n[bold]🔍 Finding repositories matching your preferences...[/bold]")

    try:
        config = load_config()
        scout = ScoutAgent(github_token=config.get('GITHUB_TOKEN'))

        # Search with user preferences
        repos = scout.discover_repositories(
            languages=prefs.languages,
            min_stars=prefs.min_stars,
            max_results=3
        )

        if repos:
            console.print(f"✅ Found {len(repos)} repositories")

            # Show why these match preferences
            for repo in repos:
                console.print(f"\n[cyan]📁 {repo['full_name']}[/cyan]")
                console.print(f"   ⭐ {repo['stargazers_count']:,} stars")
                console.print(f"   🏆 Score: {repo.get('contribution_score', 0)}")

                # Show matching factors
                reasons = []
                language = repo.get('language')
                if language and language in prefs.languages:
                    reasons.append(f"Uses {language}")
                if prefs.min_stars <= repo['stargazers_count'] <= prefs.max_stars:
                    reasons.append("Stars in preferred range")

                if reasons:
                    console.print(f"   ✅ {', '.join(reasons)}")
                else:
                    console.print(f"   ℹ️  Found via search")

        # 3. Demo opportunity analysis with preferences
        if repos:
            console.print(f"\n[bold]📊 Analyzing top repository for meaningful contributions...[/bold]")

            analyzer = AnalyzerAgent(
                github_token=config.get('GITHUB_TOKEN'),
                anthropic_api_key=config.get('ANTHROPIC_API_KEY')
            )

            # Analyze the top repository
            repo_info = scout.get_repository_quick_info(repos[0])
            if repo_info:
                analysis = analyzer.analyze_repository(repo_info)

                # Show filtered opportunities
                console.print(f"\n[bold green]🎯 Contribution Opportunities (filtered by your preferences):[/bold green]")

                opportunities = analysis['contribution_opportunities']

                if opportunities:
                    for i, opp in enumerate(opportunities[:5], 1):
                        type_color = "green" if opp['type'] in ['code_features', 'bug_fixes'] else "yellow"
                        preference_score = opp.get('user_preference_score', 0.5)

                        console.print(f"\n{i}. [{type_color}]{opp['title']}[/{type_color}]")
                        console.print(f"   Type: {opp['type'].replace('_', ' ').title()}")
                        console.print(f"   Your interest level: {preference_score:.1%}")
                        console.print(f"   Impact: {opp.get('impact', 'medium').title()}")
                        console.print(f"   Effort: {opp.get('effort', 'medium').title()}")

                        if 'description' in opp:
                            console.print(f"   📝 {opp['description']}")
                else:
                    console.print("❌ No opportunities match your preferences")

    except Exception as e:
        console.print(f"❌ Error during demo: {e}")
        console.print("\nYou can still run: `python setup_preferences.py` to configure preferences")

    # 4. Show how to provide feedback
    console.print(f"\n[bold]📈 Learning from Feedback[/bold]")
    console.print("""
[cyan]The system learns from your contributions:[/cyan]

• After working on a contribution, rate your interest (1-10)
• System adjusts future suggestions based on your feedback
• Successful contributions get higher priority
• Types you dislike get filtered out over time

[yellow]Example feedback commands:[/yellow]
""")

    console.print("""
```python
from core.user_preferences import UserPreferenceManager

manager = UserPreferenceManager()

# Record feedback about a contribution
manager.add_feedback(
    contribution_type='bug_fixes',
    interest_level=0.9,  # You loved working on this!
    success=True,        # It was merged
    repo_info={'name': 'awesome-project'},
    notes="Really enjoyed the debugging challenge"
)
```""")

def main():
    demo_customization()

    console.print(f"\n[bold]⚙️ Next Steps:[/bold]")
    console.print("""
1. Run `python setup_preferences.py` to customize your preferences
2. Run the Jupyter notebook with your new preferences
3. Provide feedback on contributions to improve suggestions
4. The system will learn and adapt to your interests!

[dim]No more unwanted documentation suggestions! 🎉[/dim]
""")

if __name__ == "__main__":
    main()