#!/usr/bin/env python3
"""
Test script to verify all agents work correctly without external APIs.
This can be run without GitHub tokens to test the basic functionality.
"""

import sys
import os
from datetime import datetime

# Import our agents
from agents.scout import ScoutAgent
from agents.analyzer import AnalyzerAgent
from agents.strategist import StrategistAgent
from agents.coder import CoderAgent
from core.feedback import MockFeedbackAgent

def test_basic_functionality():
    """Test basic functionality of all agents without external API calls."""
    print("🧪 Testing Open Source Contribution Agent Components...")
    print("=" * 60)

    # Test 1: Scout Agent initialization
    print("1. Testing Scout Agent initialization...")
    scout = ScoutAgent()  # No token needed for basic test
    assert scout is not None
    print("   ✅ Scout Agent initialized successfully")

    # Test 2: Analyzer Agent initialization
    print("2. Testing Analyzer Agent initialization...")
    analyzer = AnalyzerAgent()  # No token needed for basic test
    assert analyzer is not None
    print("   ✅ Analyzer Agent initialized successfully")

    # Test 3: Strategist Agent initialization
    print("3. Testing Strategist Agent initialization...")
    strategist = StrategistAgent()  # No API key needed for basic test
    assert strategist is not None
    print("   ✅ Strategist Agent initialized successfully")

    # Test 4: Coder Agent initialization
    print("4. Testing Coder Agent initialization...")
    coder = CoderAgent()  # No API key needed for basic test
    assert coder is not None
    print("   ✅ Coder Agent initialized successfully")

    # Test 5: Feedback Agent initialization and basic functionality
    print("5. Testing Feedback Agent...")
    feedback = MockFeedbackAgent()
    assert feedback is not None

    # Test mock feedback generation with sample data
    sample_contribution = {
        'repository': 'test/repo',
        'opportunity': {
            'title': 'Test contribution',
            'type': 'documentation',
            'priority': 'medium',
            'effort': 'low',
            'impact': 'medium'
        },
        'pr_template': {
            'title': 'docs: Add test documentation',
            'labels': ['documentation']
        }
    }

    # Test feedback submission simulation
    submission = feedback.submit_contribution(sample_contribution)
    assert submission['contribution_id'].startswith('pr_')
    print("   ✅ Mock feedback generation working")

    # Test 6: Integration test - Strategist with mock data
    print("6. Testing integration with mock data...")

    # Create mock analysis data
    mock_analysis = {
        'repository': {'full_name': 'test/repo', 'stars': 150, 'language': 'Python'},
        'health_score': 75,
        'readme_analysis': {
            'exists': True,
            'quality_score': 80,
            'missing_sections': ['testing', 'contributing']
        },
        'issues_analysis': {
            'good_first_issues': 3,
            'total_issues': 20,
            'issue_categories': {'bug': 5, 'documentation': 2}
        },
        'code_structure': {
            'primary_language': 'Python',
            'contributor_count': 4,
            'opportunities': ['Small contributor base - good opportunity for impact']
        },
        'contribution_opportunities': [
            {
                'type': 'documentation',
                'title': 'Add testing section to README',
                'description': 'README is missing testing information',
                'priority': 'medium',
                'effort': 'low',
                'impact': 'medium'
            },
            {
                'type': 'issue',
                'title': 'Fix bug #123',
                'description': 'Sample bug fix opportunity',
                'priority': 'high',
                'effort': 'medium',
                'impact': 'high'
            }
        ]
    }

    # Test strategy creation
    strategy = strategist.create_contribution_strategy(mock_analysis)
    assert strategy['repository'] == 'test/repo'
    assert len(strategy['contribution_plan']) > 0
    assert 0.0 <= strategy['success_probability'] <= 1.0
    print("   ✅ Strategy generation working with mock data")

    # Test 7: Coder Agent with mock strategy
    print("7. Testing Coder Agent with mock data...")
    if strategy['contribution_plan']:
        mock_repo_info = {
            'full_name': 'test/repo',
            'primary_language': 'Python'
        }

        contribution = coder.generate_contribution(
            strategy['contribution_plan'][0],
            mock_repo_info
        )

        assert contribution['repository'] == 'test/repo'
        assert 'pr_template' in contribution
        assert 'generated_content' in contribution
        print("   ✅ Code generation working with mock data")

        # Test 8: Full lifecycle simulation
        print("8. Testing full lifecycle simulation...")
        lifecycle = feedback.simulate_contribution_lifecycle(contribution, days_to_simulate=3)
        assert lifecycle['contribution_id'].startswith('pr_')
        assert 'final_outcome' in lifecycle
        assert 'success_metrics' in lifecycle
        print("   ✅ Full lifecycle simulation working")

    print("\n" + "=" * 60)
    print("🎉 All tests passed! The Open Source Contribution Agent is working correctly.")
    print("\n📋 Next steps:")
    print("   1. Add your GitHub token to .env file for live repository discovery")
    print("   2. Optionally add OpenAI API key for enhanced analysis")
    print("   3. Run the Jupyter notebook demo: jupyter notebook notebooks/demo.ipynb")
    print("   4. Try the agents with real repositories!")


def test_file_structure():
    """Test that all required files are present."""
    print("\n🗂️  Testing file structure...")

    required_files = [
        'agents/scout.py',
        'agents/analyzer.py',
        'agents/strategist.py',
        'agents/coder.py',
        'core/github_api.py',
        'core/utils.py',
        'core/feedback.py',
        'notebooks/demo.ipynb',
        'requirements.txt',
        'README.md'
    ]

    missing_files = []
    for file_path in required_files:
        if not os.path.exists(file_path):
            missing_files.append(file_path)

    if missing_files:
        print(f"   ❌ Missing files: {', '.join(missing_files)}")
        return False
    else:
        print("   ✅ All required files present")
        return True


def main():
    """Main test function."""
    print(f"🤖 Open Source Contribution Agent - Test Suite")
    print(f"📅 Running at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()

    try:
        # Test file structure
        if not test_file_structure():
            print("❌ File structure test failed. Please ensure all files are created.")
            sys.exit(1)

        # Test basic functionality
        test_basic_functionality()

        print("\n🚀 Ready to demo! Your Open Source Contribution Agent is fully functional.")

    except Exception as e:
        print(f"\n❌ Test failed with error: {str(e)}")
        print("\n🔧 Debug info:")
        print(f"   Python version: {sys.version}")
        print(f"   Current directory: {os.getcwd()}")
        print(f"   Python path: {sys.path}")
        sys.exit(1)


if __name__ == "__main__":
    main()