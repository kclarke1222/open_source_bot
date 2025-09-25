#!/usr/bin/env python3
"""
Validation script to check that Claude integration is properly configured.
This script checks the codebase for correct Claude API usage without requiring dependencies.
"""

import os
import re
from datetime import datetime

def check_file_for_claude_integration(filepath):
    """Check a file for proper Claude integration"""
    issues = []

    try:
        with open(filepath, 'r') as f:
            content = f.read()

        # Check for old OpenAI references
        if 'openai' in content.lower() and 'anthropic' not in content.lower():
            issues.append("Still contains OpenAI references without Anthropic")

        # Check for new Anthropic imports (skip .env files)
        if 'anthropic_api_key' in content and 'import anthropic' not in content and not filepath.endswith('.env.example'):
            issues.append("Uses anthropic_api_key but doesn't import anthropic")

        # Check for Claude client initialization (skip .env files)
        if 'anthropic_api_key' in content and not filepath.endswith('.env.example'):
            if 'self.claude = anthropic.Anthropic' not in content:
                issues.append("Has anthropic_api_key parameter but doesn't initialize Claude client")

        # Check for Claude API calls
        if 'self.claude' in content:
            if 'self.claude.messages.create' not in content:
                issues.append("Has Claude client but doesn't use messages API")

        return issues

    except Exception as e:
        return [f"Error reading file: {str(e)}"]

def validate_claude_integration():
    """Validate Claude integration across the project"""
    print("🔍 Validating Claude Integration...")
    print("=" * 50)

    files_to_check = [
        ('core/utils.py', 'Configuration utilities'),
        ('agents/analyzer.py', 'Analyzer Agent'),
        ('agents/strategist.py', 'Strategist Agent'),
        ('agents/coder.py', 'Coder Agent'),
        ('requirements.txt', 'Dependencies'),
        ('.env.example', 'Environment template'),
        ('README.md', 'Documentation')
    ]

    all_issues = []

    for filepath, description in files_to_check:
        if os.path.exists(filepath):
            print(f"✓ Checking {description} ({filepath})")
            issues = check_file_for_claude_integration(filepath)
            if issues:
                print(f"  ❌ Issues found:")
                for issue in issues:
                    print(f"    - {issue}")
                all_issues.extend([(filepath, issue) for issue in issues])
            else:
                print(f"  ✅ Claude integration looks good")
        else:
            print(f"  ⚠️  File not found: {filepath}")
            all_issues.append((filepath, "File not found"))

    print("\n" + "=" * 50)

    if not all_issues:
        print("🎉 Claude integration validation PASSED!")
        print("\n✅ All files correctly use Claude (Anthropic) instead of OpenAI")
        print("✅ Proper API key configuration")
        print("✅ Correct client initialization")
        print("✅ Updated documentation and examples")

        print("\n📋 Next steps:")
        print("1. Install dependencies: pip install -r requirements.txt")
        print("2. Set ANTHROPIC_API_KEY in .env file")
        print("3. Run the Jupyter demo: jupyter notebook notebooks/demo.ipynb")

        return True
    else:
        print("❌ Claude integration validation FAILED!")
        print(f"\nFound {len(all_issues)} issues:")
        for filepath, issue in all_issues:
            print(f"  • {filepath}: {issue}")
        return False

def check_specific_claude_features():
    """Check for specific Claude integration features"""
    print("\n🧪 Checking Claude-specific features...")

    features_found = []

    # Check Analyzer Agent for Claude README analysis
    if os.path.exists('agents/analyzer.py'):
        with open('agents/analyzer.py', 'r') as f:
            content = f.read()
            if '_claude_analyze_readme' in content:
                features_found.append("✅ README analysis with Claude")
            if 'claude-3-haiku-20240307' in content:
                features_found.append("✅ Uses Claude-3 Haiku model")

    # Check Coder Agent for Claude code enhancement
    if os.path.exists('agents/coder.py'):
        with open('agents/coder.py', 'r') as f:
            content = f.read()
            if '_claude_enhance_code' in content:
                features_found.append("✅ Code enhancement with Claude")
            if 'claude-3-haiku-20240307' in content:
                features_found.append("✅ Uses Claude-3 Haiku for code generation")

    # Check requirements for anthropic
    if os.path.exists('requirements.txt'):
        with open('requirements.txt', 'r') as f:
            content = f.read()
            if 'anthropic' in content and 'openai' not in content:
                features_found.append("✅ Dependencies updated to use Anthropic")

    print("Claude-specific features found:")
    for feature in features_found:
        print(f"  {feature}")

    if len(features_found) >= 4:
        print("🚀 Excellent! Claude integration is comprehensive.")
    elif len(features_found) >= 2:
        print("👍 Good! Basic Claude integration is working.")
    else:
        print("⚠️  Limited Claude integration found.")

    return len(features_found)

def main():
    """Main validation function"""
    print("🤖 Claude Integration Validator")
    print(f"📅 Running at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()

    try:
        # Validate basic integration
        basic_passed = validate_claude_integration()

        # Check advanced features
        feature_count = check_specific_claude_features()

        if basic_passed and feature_count >= 3:
            print("\n🎉 SUCCESS: Your Open Source Contribution Agent now uses Claude!")
            print("\n🔥 Key improvements with Claude:")
            print("   • Superior code generation and analysis")
            print("   • Better understanding of context and requirements")
            print("   • More reliable structured output")
            print("   • Enhanced README and documentation analysis")
            print("\n🚀 Ready for demo with Claude-powered intelligence!")
            return True
        else:
            print("\n❌ Integration needs more work.")
            return False

    except Exception as e:
        print(f"\n❌ Validation failed with error: {str(e)}")
        return False

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)