#!/usr/bin/env python3
"""
Interactive setup for user contribution preferences
Run this to customize the system for meaningful contributions
"""

import os
import sys
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.prompt import Prompt, IntPrompt, Confirm

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from core.user_preferences import UserPreferenceManager, ContributionType

console = Console()

def main():
    """Interactive preference setup"""
    console.print(Panel(
        "[bold cyan]🎯 Open Source Contribution Preference Setup[/bold cyan]\n\n"
        "Let's customize the system to find meaningful contributions that match your interests!\n"
        "This will help avoid suggestions like 'add README documentation' if you prefer code contributions.",
        title="Welcome"
    ))

    manager = UserPreferenceManager()
    prefs = manager.preferences

    # 1. Basic preferences
    console.print("\n[bold]📊 Basic Preferences[/bold]")

    skill_levels = ["beginner", "intermediate", "advanced", "expert"]
    current_skill = prefs.skill_level
    console.print(f"Current skill level: [cyan]{current_skill}[/cyan]")

    skill_choice = Prompt.ask(
        "Your skill level",
        choices=skill_levels,
        default=current_skill
    )
    prefs.skill_level = skill_choice

    time_options = ["low", "medium", "high"]
    time_descriptions = {
        "low": "2-5 hours per week",
        "medium": "5-15 hours per week",
        "high": "15+ hours per week"
    }

    console.print("\nTime commitment options:")
    for option, desc in time_descriptions.items():
        console.print(f"  [cyan]{option}[/cyan]: {desc}")

    time_choice = Prompt.ask(
        "Available time commitment",
        choices=time_options,
        default=prefs.available_time
    )
    prefs.available_time = time_choice

    # 2. Contribution type preferences
    console.print("\n[bold]🛠️  Contribution Type Preferences[/bold]")
    console.print("Rate each type from 1-10 (10 = most interested, 1 = least interested)")

    table = Table(title="Current Preferences")
    table.add_column("Contribution Type", style="cyan")
    table.add_column("Current Rating", justify="center", style="green")
    table.add_column("Description", style="white")

    descriptions = {
        ContributionType.CODE_FEATURES.value: "Implement new features and functionality",
        ContributionType.BUG_FIXES.value: "Fix bugs and resolve issues",
        ContributionType.PERFORMANCE.value: "Optimize code performance and efficiency",
        ContributionType.ARCHITECTURE.value: "Design system architecture and patterns",
        ContributionType.API_DESIGN.value: "Design and improve APIs",
        ContributionType.SECURITY.value: "Address security vulnerabilities",
        ContributionType.REFACTORING.value: "Improve code quality and structure",
        ContributionType.TESTING.value: "Write tests and improve test coverage",
        ContributionType.CI_CD.value: "Setup CI/CD pipelines and automation",
        ContributionType.DOCUMENTATION.value: "Write documentation and guides"
    }

    for contrib_type in ContributionType:
        current_weight = prefs.contribution_weights.get(contrib_type.value, 0.5)
        current_rating = int(current_weight * 10)
        desc = descriptions.get(contrib_type.value, "")

        table.add_row(
            contrib_type.value.replace('_', ' ').title(),
            str(current_rating),
            desc
        )

    console.print(table)

    console.print("\n[yellow]Press Enter to keep current rating, or enter new rating (1-10)[/yellow]")

    for contrib_type in ContributionType:
        current_weight = prefs.contribution_weights.get(contrib_type.value, 0.5)
        current_rating = int(current_weight * 10)

        type_name = contrib_type.value.replace('_', ' ').title()

        while True:
            rating_input = Prompt.ask(
                f"{type_name} (current: {current_rating})",
                default=str(current_rating)
            )

            try:
                rating = int(rating_input)
                if 1 <= rating <= 10:
                    prefs.contribution_weights[contrib_type.value] = rating / 10.0
                    break
                else:
                    console.print("[red]Please enter a number between 1 and 10[/red]")
            except ValueError:
                console.print("[red]Please enter a valid number[/red]")

    # 3. Repository preferences
    console.print("\n[bold]📁 Repository Preferences[/bold]")

    current_min = prefs.min_stars
    new_min = IntPrompt.ask(
        f"Minimum stars (avoid tiny projects)",
        default=current_min
    )
    prefs.min_stars = new_min

    current_max = prefs.max_stars
    new_max = IntPrompt.ask(
        f"Maximum stars (avoid overwhelming large projects)",
        default=current_max
    )
    prefs.max_stars = new_max

    size_options = ["small", "medium", "large"]
    size_descriptions = {
        "small": "1-20 open issues, smaller codebase",
        "medium": "5-100 open issues, moderate complexity",
        "large": "50+ open issues, large complex projects"
    }

    console.print("\nProject size preferences:")
    for option, desc in size_descriptions.items():
        console.print(f"  [cyan]{option}[/cyan]: {desc}")

    size_choice = Prompt.ask(
        "Preferred project size",
        choices=size_options,
        default=prefs.preferred_project_size
    )
    prefs.preferred_project_size = size_choice

    # 4. Things to avoid
    console.print("\n[bold]🚫 Things to Avoid[/bold]")

    current_avoid = list(prefs.avoid_types)
    if current_avoid:
        console.print(f"Currently avoiding: {', '.join(current_avoid)}")

    avoid_input = Prompt.ask(
        "Additional contribution types to avoid (comma-separated, or press Enter to skip)",
        default=""
    )

    if avoid_input.strip():
        new_avoid = [t.strip().lower() for t in avoid_input.split(',')]
        prefs.avoid_types.update(new_avoid)

    avoid_topics_input = Prompt.ask(
        "Topics/keywords to avoid in repositories (e.g., 'crypto,blockchain', or press Enter to skip)",
        default=""
    )

    if avoid_topics_input.strip():
        new_avoid_topics = [t.strip().lower() for t in avoid_topics_input.split(',')]
        prefs.avoid_topics.update(new_avoid_topics)

    # 5. Languages
    console.print("\n[bold]💻 Programming Languages[/bold]")
    current_languages = ', '.join(prefs.languages)
    console.print(f"Current languages: {current_languages}")

    languages_input = Prompt.ask(
        "Preferred programming languages (comma-separated)",
        default=current_languages
    )

    if languages_input.strip():
        prefs.languages = [lang.strip() for lang in languages_input.split(',')]

    # Save preferences
    manager.save_preferences()

    # Show summary
    console.print("\n[bold green]✅ Preferences Updated![/bold green]")

    summary_table = Table(title="Your Contribution Preferences Summary")
    summary_table.add_column("Category", style="cyan")
    summary_table.add_column("Value", style="green")

    summary_table.add_row("Skill Level", prefs.skill_level.title())
    summary_table.add_row("Available Time", f"{prefs.available_time.title()} ({time_descriptions[prefs.available_time]})")
    summary_table.add_row("Preferred Languages", ', '.join(prefs.languages))
    summary_table.add_row("Project Size", f"{prefs.preferred_project_size.title()} ({size_descriptions[prefs.preferred_project_size]})")
    summary_table.add_row("Stars Range", f"{prefs.min_stars:,} - {prefs.max_stars:,}")

    console.print(summary_table)

    # Show top contribution preferences
    sorted_prefs = sorted(
        prefs.contribution_weights.items(),
        key=lambda x: x[1],
        reverse=True
    )

    console.print("\n[bold]🎯 Your Top Contribution Interests:[/bold]")
    for i, (contrib_type, weight) in enumerate(sorted_prefs[:5], 1):
        type_name = contrib_type.replace('_', ' ').title()
        rating = int(weight * 10)
        console.print(f"{i}. {type_name} (Rating: {rating}/10)")

    if prefs.avoid_types:
        console.print(f"\n[bold red]❌ Avoiding:[/bold red] {', '.join(prefs.avoid_types)}")

    console.print(f"\n[dim]Preferences saved to: {manager.preferences_file}[/dim]")

    if Confirm.ask("\nWould you like to test the system with your new preferences?"):
        console.print("\n🔍 Testing repository discovery with your preferences...")
        test_with_preferences(prefs)

def test_with_preferences(prefs):
    """Test the system with user preferences"""
    try:
        from agents.scout import ScoutAgent
        from core.utils import load_config

        config = load_config()
        scout = ScoutAgent(github_token=config.get('GITHUB_TOKEN'))

        # Test discovery with preferences
        console.print("Searching for repositories that match your preferences...")

        discovered_repos = scout.discover_repositories(
            languages=prefs.languages,
            min_stars=prefs.min_stars,
            max_results=5
        )

        if discovered_repos:
            console.print(f"\n✅ Found {len(discovered_repos)} repositories!")
            scout.display_repositories(discovered_repos[:3])

            # Show why these were selected
            console.print("\n[bold]🎯 Why these repositories match your preferences:[/bold]")
            for repo in discovered_repos[:3]:
                reasons = []
                stars = repo.get('stargazers_count', 0)
                language = repo.get('language') or 'Unknown'

                if prefs.min_stars <= stars <= prefs.max_stars:
                    reasons.append(f"Stars in your range ({stars:,})")
                if language and language.lower() in [l.lower() for l in prefs.languages]:
                    reasons.append(f"Uses {language}")

                if reasons:
                    console.print(f"• [cyan]{repo['full_name']}[/cyan]: {', '.join(reasons)}")
                else:
                    console.print(f"• [cyan]{repo['full_name']}[/cyan]: Found via search")

        else:
            console.print("❌ No repositories found. Try adjusting your preferences.")

    except Exception as e:
        console.print(f"❌ Error testing preferences: {e}")
        console.print("You can still run the notebook to test your preferences!")

if __name__ == "__main__":
    main()