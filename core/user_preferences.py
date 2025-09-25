"""
Enhanced user preference system with feedback learning
"""
from typing import Dict, List, Optional, Set
import json
import os
from datetime import datetime
from dataclasses import dataclass, asdict
from enum import Enum

class ContributionType(Enum):
    """Types of contributions with priority weighting"""
    CODE_FEATURES = "code_features"
    BUG_FIXES = "bug_fixes"
    PERFORMANCE = "performance"
    TESTING = "testing"
    DOCUMENTATION = "documentation"
    CI_CD = "ci_cd"
    REFACTORING = "refactoring"
    SECURITY = "security"
    API_DESIGN = "api_design"
    ARCHITECTURE = "architecture"

@dataclass
class UserPreferences:
    """Enhanced user preferences with learning capabilities"""
    # Core preferences
    skill_level: str = "intermediate"  # beginner, intermediate, advanced, expert
    available_time: str = "medium"     # low (2-5 hrs/week), medium (5-15), high (15+ hrs)
    languages: List[str] = None

    # Contribution preferences with weights (0.0-1.0)
    contribution_weights: Dict[str, float] = None

    # Repository preferences
    min_stars: int = 50
    max_stars: int = 50000
    preferred_project_size: str = "medium"  # small, medium, large
    prefer_active_projects: bool = True

    # Exclusion preferences
    avoid_types: Set[str] = None
    avoid_topics: Set[str] = None

    # Learning from feedback
    feedback_history: List[Dict] = None
    contribution_success_rate: Dict[str, float] = None

    def __post_init__(self):
        if self.languages is None:
            self.languages = ["Python", "JavaScript", "TypeScript"]
        if self.contribution_weights is None:
            self.contribution_weights = {
                ContributionType.CODE_FEATURES.value: 0.9,
                ContributionType.BUG_FIXES.value: 0.8,
                ContributionType.PERFORMANCE.value: 0.7,
                ContributionType.ARCHITECTURE.value: 0.8,
                ContributionType.API_DESIGN.value: 0.7,
                ContributionType.SECURITY.value: 0.6,
                ContributionType.REFACTORING.value: 0.6,
                ContributionType.TESTING.value: 0.4,
                ContributionType.CI_CD.value: 0.5,
                ContributionType.DOCUMENTATION.value: 0.2  # Low weight by default
            }
        if self.avoid_types is None:
            self.avoid_types = set()
        if self.avoid_topics is None:
            self.avoid_topics = set()
        if self.feedback_history is None:
            self.feedback_history = []
        if self.contribution_success_rate is None:
            self.contribution_success_rate = {}

class UserPreferenceManager:
    """Manages user preferences with learning and feedback"""

    def __init__(self, preferences_file: str = "data/user_preferences.json"):
        self.preferences_file = preferences_file
        self.preferences = self._load_preferences()

    def _load_preferences(self) -> UserPreferences:
        """Load preferences from file or create defaults"""
        if os.path.exists(self.preferences_file):
            try:
                with open(self.preferences_file, 'r') as f:
                    data = json.load(f)
                    # Convert sets back from lists
                    if 'avoid_types' in data:
                        data['avoid_types'] = set(data['avoid_types'])
                    if 'avoid_topics' in data:
                        data['avoid_topics'] = set(data['avoid_topics'])
                    return UserPreferences(**data)
            except Exception as e:
                print(f"Error loading preferences: {e}")

        return UserPreferences()

    def save_preferences(self):
        """Save preferences to file"""
        os.makedirs(os.path.dirname(self.preferences_file), exist_ok=True)

        data = asdict(self.preferences)
        # Convert sets to lists for JSON serialization
        data['avoid_types'] = list(data['avoid_types'])
        data['avoid_topics'] = list(data['avoid_topics'])

        with open(self.preferences_file, 'w') as f:
            json.dump(data, f, indent=2, default=str)

    def add_feedback(self, contribution_type: str, interest_level: float,
                    success: bool, repo_info: Dict, notes: str = ""):
        """Record feedback about a contribution"""
        feedback = {
            'timestamp': datetime.now().isoformat(),
            'contribution_type': contribution_type,
            'interest_level': interest_level,  # 0.0-1.0
            'success': success,
            'repo_info': repo_info,
            'notes': notes
        }

        self.preferences.feedback_history.append(feedback)

        # Update success rates
        if contribution_type not in self.preferences.contribution_success_rate:
            self.preferences.contribution_success_rate[contribution_type] = 0.5

        # Moving average of success rate
        current_rate = self.preferences.contribution_success_rate[contribution_type]
        new_rate = current_rate * 0.8 + (1.0 if success else 0.0) * 0.2
        self.preferences.contribution_success_rate[contribution_type] = new_rate

        # Update contribution weights based on interest
        if contribution_type in self.preferences.contribution_weights:
            current_weight = self.preferences.contribution_weights[contribution_type]
            # Adjust weight based on interest level
            adjustment = (interest_level - 0.5) * 0.1  # ±0.05 max adjustment
            self.preferences.contribution_weights[contribution_type] = max(0.0, min(1.0, current_weight + adjustment))

        self.save_preferences()

    def get_contribution_score(self, contribution_type: str, base_score: float = 0.5) -> float:
        """Get weighted score for a contribution type"""
        weight = self.preferences.contribution_weights.get(contribution_type, 0.5)
        success_rate = self.preferences.contribution_success_rate.get(contribution_type, 0.5)

        # Combine base score, user preference weight, and success rate
        return (base_score * 0.4) + (weight * 0.4) + (success_rate * 0.2)

    def should_avoid_contribution(self, contribution_type: str, repo_topics: List[str]) -> bool:
        """Check if contribution should be avoided based on preferences"""
        if contribution_type in self.preferences.avoid_types:
            return True

        if any(topic in self.preferences.avoid_topics for topic in repo_topics):
            return True

        # Very low weight indicates strong disinterest
        weight = self.preferences.contribution_weights.get(contribution_type, 0.5)
        return weight < 0.1

    def update_preferences_interactive(self):
        """Interactive preference update"""
        print("\n🎯 Let's customize your contribution preferences!")
        print("Rate each contribution type from 1-10 (10 = most interested):")

        for contrib_type in ContributionType:
            current_weight = self.preferences.contribution_weights.get(contrib_type.value, 0.5)
            current_rating = int(current_weight * 10)

            while True:
                try:
                    user_input = input(f"\n{contrib_type.value.replace('_', ' ').title()} (current: {current_rating}): ")
                    if user_input.strip() == "":
                        break

                    rating = int(user_input)
                    if 1 <= rating <= 10:
                        self.preferences.contribution_weights[contrib_type.value] = rating / 10.0
                        break
                    else:
                        print("Please enter a number between 1 and 10")
                except ValueError:
                    if user_input.strip() == "":
                        break
                    print("Please enter a valid number")

        # Ask about things to avoid
        avoid_input = input("\nTypes to completely avoid (comma-separated): ").strip()
        if avoid_input:
            self.preferences.avoid_types.update(avoid_input.split(','))

        self.save_preferences()
        print("✅ Preferences updated!")

def get_user_preferences() -> UserPreferences:
    """Get current user preferences"""
    manager = UserPreferenceManager()
    return manager.preferences

if __name__ == "__main__":
    # Interactive preference setup
    manager = UserPreferenceManager()
    manager.update_preferences_interactive()