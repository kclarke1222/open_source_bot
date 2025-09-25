from typing import Dict, List, Optional
import random
from datetime import datetime, timedelta
from rich.console import Console
from rich.panel import Panel
import json

class MockFeedbackAgent:
    """
    Mock feedback agent that simulates maintainer responses to contributions.

    In a production system, this would interface with actual GitHub APIs
    to submit PRs and track real feedback. For the MVP, it provides realistic
    simulated responses to demonstrate the feedback loop.
    """

    def __init__(self):
        self.console = Console()
        self.feedback_history = []

    def submit_contribution(self, contribution: Dict) -> Dict:
        """
        Simulate submitting a contribution and receiving initial feedback

        Args:
            contribution: Generated contribution from CoderAgent

        Returns:
            Submission result with initial status
        """
        self.console.print(f"🚀 [bold blue]Mock Feedback Agent: Submitting contribution '{contribution['opportunity']['title']}'...[/bold blue]")

        # Simulate submission process
        submission = {
            'contribution_id': f"pr_{random.randint(1000, 9999)}",
            'repository': contribution['repository'],
            'title': contribution['pr_template']['title'],
            'status': 'submitted',
            'submitted_at': datetime.now().isoformat(),
            'initial_feedback': self._generate_initial_feedback(contribution),
            'reviews': [],
            'ci_status': self._simulate_ci_results(contribution),
            'merge_status': 'pending'
        }

        self.feedback_history.append(submission)

        self.console.print(f"✅ [bold green]Contribution submitted with ID: {submission['contribution_id']}[/bold green]")
        return submission

    def get_feedback_update(self, contribution_id: str, days_elapsed: int = 1) -> Dict:
        """
        Simulate receiving updated feedback after some time has passed

        Args:
            contribution_id: ID of the submitted contribution
            days_elapsed: Number of days since submission

        Returns:
            Updated feedback information
        """
        submission = self._find_submission(contribution_id)
        if not submission:
            return {'error': 'Contribution not found'}

        # Simulate feedback progression over time
        new_feedback = self._generate_time_based_feedback(submission, days_elapsed)
        submission.update(new_feedback)

        return submission

    def _generate_initial_feedback(self, contribution: Dict) -> Dict:
        """Generate initial automated feedback"""
        feedback_scenarios = [
            {
                'type': 'positive_reception',
                'probability': 0.4,
                'feedback': {
                    'automated_checks': 'passed',
                    'initial_comments': [
                        "Thanks for the contribution! The PR looks good at first glance.",
                        "Automated tests are passing. Will review in detail soon."
                    ],
                    'maintainer_sentiment': 'positive',
                    'estimated_review_time': '2-3 days'
                }
            },
            {
                'type': 'needs_changes',
                'probability': 0.35,
                'feedback': {
                    'automated_checks': 'failed',
                    'initial_comments': [
                        "Thanks for the PR! There are a few issues that need to be addressed:",
                        "• Code style doesn't match project conventions",
                        "• Missing tests for edge cases",
                        "• Please update the documentation"
                    ],
                    'maintainer_sentiment': 'constructive',
                    'estimated_review_time': '1-2 days'
                }
            },
            {
                'type': 'neutral_pending',
                'probability': 0.2,
                'feedback': {
                    'automated_checks': 'running',
                    'initial_comments': [
                        "PR received. Will review when I have time.",
                        "Please be patient, we have a backlog of PRs to review."
                    ],
                    'maintainer_sentiment': 'neutral',
                    'estimated_review_time': '5-7 days'
                }
            },
            {
                'type': 'immediate_merge',
                'probability': 0.05,
                'feedback': {
                    'automated_checks': 'passed',
                    'initial_comments': [
                        "Perfect! This is exactly what we needed.",
                        "Merging immediately. Thanks for the quick fix!"
                    ],
                    'maintainer_sentiment': 'enthusiastic',
                    'estimated_review_time': 'immediate'
                }
            }
        ]

        # Choose scenario based on contribution quality factors
        quality_score = self._assess_contribution_quality(contribution)
        scenario = self._select_scenario_by_probability(feedback_scenarios, quality_score)

        return scenario['feedback']

    def _generate_time_based_feedback(self, submission: Dict, days_elapsed: int) -> Dict:
        """Generate feedback updates based on time elapsed"""
        updates = {}

        if days_elapsed >= 1 and submission['status'] == 'submitted':
            # First day updates
            if submission['initial_feedback']['automated_checks'] == 'running':
                updates['ci_status'] = self._simulate_ci_results({'repository': submission['repository']})
                updates['initial_feedback']['automated_checks'] = updates['ci_status']['overall_status']

        if days_elapsed >= 2:
            # Add reviewer feedback
            if not submission.get('reviews'):
                updates['reviews'] = self._generate_reviewer_comments(submission)
                updates['status'] = 'under_review'

        if days_elapsed >= 3:
            # Potential status changes
            if submission['initial_feedback']['maintainer_sentiment'] == 'positive':
                if random.random() > 0.3:  # 70% chance of approval
                    updates['status'] = 'approved'
                    updates['merge_status'] = 'ready_to_merge'

        if days_elapsed >= 5:
            # Final outcomes
            sentiment = submission['initial_feedback']['maintainer_sentiment']
            if sentiment in ['positive', 'enthusiastic'] and updates.get('status') == 'approved':
                updates['status'] = 'merged'
                updates['merge_status'] = 'merged'
                updates['merged_at'] = datetime.now().isoformat()
            elif sentiment == 'constructive' and random.random() > 0.4:
                updates['status'] = 'changes_requested'
                updates['requested_changes'] = self._generate_change_requests()

        if days_elapsed >= 14:
            # Long-term outcomes
            if submission['status'] in ['submitted', 'under_review']:
                outcomes = ['stale', 'closed', 'needs_rebase']
                updates['status'] = random.choice(outcomes)

        return updates

    def _assess_contribution_quality(self, contribution: Dict) -> float:
        """Assess the quality of a contribution for feedback simulation"""
        quality_score = 0.5  # Base score

        opportunity = contribution['opportunity']

        # Type-based scoring
        if opportunity['type'] == 'documentation':
            quality_score += 0.2  # Documentation PRs are usually well-received
        elif opportunity['type'] == 'testing':
            quality_score += 0.15  # Test improvements are valued
        elif opportunity['type'] == 'issue':
            quality_score += 0.1   # Issue fixes vary in complexity

        # Priority-based scoring
        priority = opportunity.get('priority', 'medium')
        if priority == 'high':
            quality_score += 0.1
        elif priority == 'low':
            quality_score -= 0.1

        # Effort consideration (higher effort might mean more potential issues)
        effort = opportunity.get('effort', 'medium')
        if effort == 'low':
            quality_score += 0.1  # Simple changes less likely to have issues
        elif effort == 'high':
            quality_score -= 0.1  # Complex changes more likely to need revision

        return max(0.1, min(0.9, quality_score))

    def _select_scenario_by_probability(self, scenarios: List[Dict], quality_score: float) -> Dict:
        """Select feedback scenario based on quality score"""
        # Adjust probabilities based on quality
        adjusted_scenarios = []
        for scenario in scenarios:
            prob = scenario['probability']

            if scenario['type'] == 'positive_reception' and quality_score > 0.7:
                prob *= 1.5
            elif scenario['type'] == 'needs_changes' and quality_score < 0.4:
                prob *= 1.5
            elif scenario['type'] == 'immediate_merge' and quality_score > 0.8:
                prob *= 2.0

            adjusted_scenarios.append({**scenario, 'adjusted_prob': prob})

        # Normalize probabilities
        total_prob = sum(s['adjusted_prob'] for s in adjusted_scenarios)
        for scenario in adjusted_scenarios:
            scenario['adjusted_prob'] /= total_prob

        # Select based on random choice
        rand = random.random()
        cumulative = 0.0
        for scenario in adjusted_scenarios:
            cumulative += scenario['adjusted_prob']
            if rand <= cumulative:
                return scenario

        return scenarios[-1]  # Fallback

    def _simulate_ci_results(self, contribution: Dict) -> Dict:
        """Simulate CI/CD pipeline results"""
        # Simulate various CI checks
        checks = {
            'lint': random.choice(['passed', 'failed', 'warning']) if random.random() > 0.1 else 'skipped',
            'tests': random.choice(['passed', 'failed']) if random.random() > 0.05 else 'skipped',
            'security_scan': random.choice(['passed', 'warning']) if random.random() > 0.02 else 'failed',
            'build': random.choice(['passed', 'failed']) if random.random() > 0.05 else 'passed'
        }

        # Determine overall status
        if any(status == 'failed' for status in checks.values()):
            overall_status = 'failed'
        elif any(status == 'warning' for status in checks.values()):
            overall_status = 'warning'
        else:
            overall_status = 'passed'

        return {
            'checks': checks,
            'overall_status': overall_status,
            'details': self._generate_ci_details(checks)
        }

    def _generate_ci_details(self, checks: Dict) -> List[str]:
        """Generate detailed CI feedback messages"""
        details = []

        for check, status in checks.items():
            if status == 'failed':
                if check == 'lint':
                    details.append("❌ Linting failed: Code style issues found. Run 'flake8' to see details.")
                elif check == 'tests':
                    details.append("❌ Tests failed: 2 tests are failing. Check test output for details.")
                elif check == 'security_scan':
                    details.append("❌ Security scan failed: Potential vulnerability detected in dependencies.")
                elif check == 'build':
                    details.append("❌ Build failed: Compilation errors found.")
            elif status == 'warning':
                if check == 'lint':
                    details.append("⚠️ Linting warnings: Minor style issues detected.")
                elif check == 'security_scan':
                    details.append("⚠️ Security scan: Low-priority security notice.")
            elif status == 'passed':
                details.append(f"✅ {check.title()} check passed")

        return details

    def _generate_reviewer_comments(self, submission: Dict) -> List[Dict]:
        """Generate realistic reviewer comments"""
        sentiment = submission['initial_feedback']['maintainer_sentiment']

        positive_comments = [
            "Great work! This addresses the issue perfectly.",
            "Clean implementation. I like the approach you've taken.",
            "Thanks for adding comprehensive tests. Much appreciated!",
            "Documentation looks good. This will help users a lot.",
            "Nice catch on the edge case handling."
        ]

        constructive_comments = [
            "The logic looks good, but could you add error handling for edge cases?",
            "Consider using a more descriptive variable name here.",
            "This function is getting a bit long. Maybe split it into smaller functions?",
            "Could you add a docstring explaining what this method does?",
            "The tests look good, but we're missing coverage for the error path."
        ]

        neutral_comments = [
            "Code looks fine overall.",
            "Thanks for the contribution.",
            "Please rebase on the latest main branch.",
            "Could you resolve the merge conflicts?",
            "Looks good, just waiting for CI to pass."
        ]

        if sentiment == 'positive' or sentiment == 'enthusiastic':
            comments = random.sample(positive_comments, min(2, len(positive_comments)))
        elif sentiment == 'constructive':
            comments = random.sample(constructive_comments, min(3, len(constructive_comments)))
        else:
            comments = random.sample(neutral_comments, min(2, len(neutral_comments)))

        return [
            {
                'reviewer': f"maintainer_{random.randint(1, 3)}",
                'comment': comment,
                'timestamp': (datetime.now() - timedelta(hours=random.randint(1, 48))).isoformat()
            }
            for comment in comments
        ]

    def _generate_change_requests(self) -> List[str]:
        """Generate specific change requests"""
        change_requests = [
            "Please add unit tests for the new functionality",
            "Code style doesn't match our conventions. Run 'black' formatter",
            "Add docstrings to all public methods",
            "Consider edge cases: what happens with empty input?",
            "Please update the changelog with your changes",
            "The commit message should follow our format: 'type(scope): description'",
            "Add type hints to function parameters and return values",
            "Consider performance implications for large datasets",
            "Please add error handling for network timeouts",
            "Update the README to document the new feature"
        ]

        return random.sample(change_requests, random.randint(2, 4))

    def _find_submission(self, contribution_id: str) -> Optional[Dict]:
        """Find a submission by ID"""
        for submission in self.feedback_history:
            if submission['contribution_id'] == contribution_id:
                return submission
        return None

    def simulate_contribution_lifecycle(self, contribution: Dict, days_to_simulate: int = 7) -> Dict:
        """
        Simulate the complete lifecycle of a contribution

        Args:
            contribution: Generated contribution
            days_to_simulate: Number of days to simulate

        Returns:
            Complete contribution lifecycle data
        """
        self.console.print(f"🎬 [bold blue]Simulating {days_to_simulate}-day contribution lifecycle...[/bold blue]")

        # Submit contribution
        submission = self.submit_contribution(contribution)

        # Simulate daily updates
        lifecycle = [submission]
        for day in range(1, days_to_simulate + 1):
            daily_update = self.get_feedback_update(submission['contribution_id'], day)
            if daily_update and 'error' not in daily_update:
                lifecycle.append({
                    'day': day,
                    'status': daily_update.get('status', submission['status']),
                    'updates': self._extract_daily_changes(lifecycle[-1], daily_update)
                })

        final_outcome = self._determine_final_outcome(lifecycle[-1])

        result = {
            'contribution_id': submission['contribution_id'],
            'repository': contribution['repository'],
            'opportunity_title': contribution['opportunity']['title'],
            'lifecycle': lifecycle,
            'final_outcome': final_outcome,
            'lessons_learned': self._generate_lessons_learned(final_outcome),
            'success_metrics': self._calculate_success_metrics(lifecycle)
        }

        self.console.print(f"🏁 [bold green]Simulation complete! Final status: {final_outcome['status']}[/bold green]")
        return result

    def _extract_daily_changes(self, previous: Dict, current: Dict) -> Dict:
        """Extract what changed between two states"""
        changes = {}

        if previous.get('status') != current.get('status'):
            changes['status_change'] = {
                'from': previous.get('status'),
                'to': current.get('status')
            }

        if len(current.get('reviews', [])) > len(previous.get('reviews', [])):
            new_reviews = current.get('reviews', [])[len(previous.get('reviews', [])):]
            changes['new_reviews'] = new_reviews

        if current.get('merge_status') != previous.get('merge_status'):
            changes['merge_status_change'] = {
                'from': previous.get('merge_status'),
                'to': current.get('merge_status')
            }

        return changes

    def _determine_final_outcome(self, final_state: Dict) -> Dict:
        """Determine the final outcome of a contribution"""
        status = final_state.get('status', 'unknown')

        outcomes = {
            'merged': {
                'status': 'merged',
                'success': True,
                'description': 'Contribution was successfully merged!',
                'impact': 'Your code is now part of the project and helping users.'
            },
            'approved': {
                'status': 'approved',
                'success': True,
                'description': 'Contribution was approved and ready for merge.',
                'impact': 'Great work! The maintainers liked your contribution.'
            },
            'changes_requested': {
                'status': 'needs_revision',
                'success': False,
                'description': 'Contribution needs changes before it can be merged.',
                'impact': 'Good learning opportunity to improve the code based on feedback.'
            },
            'stale': {
                'status': 'stale',
                'success': False,
                'description': 'Contribution became stale due to inactivity.',
                'impact': 'Consider reviving with updates or creating a new PR.'
            },
            'closed': {
                'status': 'closed',
                'success': False,
                'description': 'Contribution was closed without merging.',
                'impact': 'Learning experience. Consider the feedback for future contributions.'
            }
        }

        return outcomes.get(status, {
            'status': status,
            'success': False,
            'description': f'Contribution ended with status: {status}',
            'impact': 'Mixed results. Consider this experience for future contributions.'
        })

    def _generate_lessons_learned(self, outcome: Dict) -> List[str]:
        """Generate lessons learned based on outcome"""
        lessons = []

        if outcome['success']:
            lessons.extend([
                "Successful contribution! This approach worked well.",
                "Good code quality and documentation helped with acceptance.",
                "Engaging with maintainers early made the process smoother."
            ])
        else:
            lessons.extend([
                "Consider spending more time on initial code quality.",
                "Better communication with maintainers could improve outcomes.",
                "More comprehensive testing might have helped.",
                "Understanding project conventions is crucial for acceptance."
            ])

        return lessons

    def _calculate_success_metrics(self, lifecycle: List[Dict]) -> Dict:
        """Calculate success metrics from lifecycle"""
        final_status = lifecycle[-1].get('status', 'unknown') if lifecycle else 'unknown'

        return {
            'days_to_resolution': len(lifecycle) - 1,
            'review_rounds': sum(1 for entry in lifecycle if entry.get('updates', {}).get('new_reviews')),
            'ci_passes': 1 if any('ci_status' in entry and entry['ci_status']['overall_status'] == 'passed'
                                 for entry in lifecycle) else 0,
            'final_success': final_status in ['merged', 'approved'],
            'maintainer_engagement': len([entry for entry in lifecycle if entry.get('updates', {}).get('new_reviews')]) > 0
        }

    def display_feedback_summary(self, lifecycle_result: Dict) -> None:
        """Display a summary of the contribution feedback"""
        outcome = lifecycle_result['final_outcome']
        metrics = lifecycle_result['success_metrics']

        # Outcome summary
        status_color = "green" if outcome['success'] else "red"
        self.console.print(Panel(
            f"[bold {status_color}]{outcome['description']}[/bold {status_color}]\n\n"
            f"Impact: {outcome['impact']}\n"
            f"Days to Resolution: {metrics['days_to_resolution']}\n"
            f"Review Rounds: {metrics['review_rounds']}\n"
            f"Maintainer Engagement: {'Yes' if metrics['maintainer_engagement'] else 'No'}",
            title=f"📊 Contribution Outcome: {lifecycle_result['repository']}"
        ))

        # Lessons learned
        if lifecycle_result['lessons_learned']:
            lessons_text = "\n".join([f"• {lesson}" for lesson in lifecycle_result['lessons_learned']])
            self.console.print(Panel(lessons_text, title="💡 Lessons Learned"))

    def get_feedback_statistics(self) -> Dict:
        """Get statistics about all simulated feedback"""
        if not self.feedback_history:
            return {'total_submissions': 0}

        total = len(self.feedback_history)
        statuses = [submission.get('status', 'unknown') for submission in self.feedback_history]

        return {
            'total_submissions': total,
            'success_rate': sum(1 for s in statuses if s in ['merged', 'approved']) / total,
            'average_review_time': '2-4 days',  # Simulated average
            'most_common_feedback': 'needs_changes',
            'status_breakdown': {
                status: statuses.count(status) for status in set(statuses)
            }
        }

if __name__ == "__main__":
    # Example usage
    feedback_agent = MockFeedbackAgent()

    # Sample contribution (would come from CoderAgent)
    sample_contribution = {
        'repository': 'example/awesome-project',
        'opportunity': {
            'title': 'Add installation documentation',
            'type': 'documentation',
            'priority': 'medium',
            'effort': 'low'
        },
        'pr_template': {
            'title': 'docs: Add installation section to README',
            'labels': ['documentation', 'improvement']
        }
    }

    # Simulate complete lifecycle
    result = feedback_agent.simulate_contribution_lifecycle(sample_contribution, days_to_simulate=5)
    feedback_agent.display_feedback_summary(result)

    # Show statistics
    stats = feedback_agent.get_feedback_statistics()
    print(f"\nFeedback Statistics: {stats}")