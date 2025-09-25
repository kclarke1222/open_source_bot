from typing import List, Dict, Optional
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.utils import save_json
from rich.console import Console
from rich.panel import Panel
from rich.syntax import Syntax
import random
from datetime import datetime

class CoderAgent:
    """Agent responsible for generating code, documentation, and PR drafts for contributions"""

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
                self.console.print("⚠️  [yellow]Anthropic not installed. Code generation will be template-based.[/yellow]")
        else:
            self.use_ai = False
            self.console.print("⚠️  [yellow]Claude API key not provided. Code generation will be template-based.[/yellow]")

    def generate_contribution(self, strategy_item: Dict, repository_info: Dict) -> Dict:
        """
        Generate a complete contribution based on strategic planning

        Args:
            strategy_item: Single item from contribution plan
            repository_info: Repository information and context

        Returns:
            Generated contribution with code, docs, and PR template
        """
        self.console.print(f"💻 [bold blue]Coder Agent: Generating contribution for '{strategy_item['opportunity']['title']}'...[/bold blue]")

        opportunity = strategy_item['opportunity']
        contribution = {
            'opportunity': opportunity,
            'repository': repository_info['full_name'],
            'type': opportunity['type'],
            'generated_content': {},
            'pr_template': {},
            'commit_messages': [],
            'files_to_create': [],
            'files_to_modify': [],
            'implementation_notes': []
        }

        # Generate appropriate content based on opportunity type
        if opportunity['type'] == 'documentation':
            contribution = self._generate_documentation_contribution(contribution, repository_info)
        elif opportunity['type'] == 'issue':
            contribution = self._generate_issue_fix_contribution(contribution, repository_info)
        elif opportunity['type'] == 'testing':
            contribution = self._generate_testing_contribution(contribution, repository_info)
        elif opportunity['type'] == 'feature':
            contribution = self._generate_feature_contribution(contribution, repository_info)

        # Generate PR template
        contribution['pr_template'] = self._generate_pr_template(contribution)

        # Generate commit messages
        contribution['commit_messages'] = self._generate_commit_messages(contribution)

        self.console.print(f"✅ [bold green]Contribution generated successfully![/bold green]")
        return contribution

    def _generate_documentation_contribution(self, contribution: Dict, repo_info: Dict) -> Dict:
        """Generate documentation-related contribution"""
        opportunity = contribution['opportunity']

        if 'README' in opportunity['title']:
            # Generate README section
            if 'installation' in opportunity['title'].lower():
                content = self._generate_installation_docs(repo_info)
                contribution['files_to_modify'] = ['README.md']
            elif 'usage' in opportunity['title'].lower():
                content = self._generate_usage_docs(repo_info)
                contribution['files_to_modify'] = ['README.md']
            elif 'contributing' in opportunity['title'].lower():
                content = self._generate_contributing_docs(repo_info)
                contribution['files_to_create'] = ['CONTRIBUTING.md']
            else:
                content = self._generate_generic_readme_section(opportunity['title'], repo_info)
                contribution['files_to_modify'] = ['README.md']

            contribution['generated_content']['documentation'] = content

        elif 'API' in opportunity['title']:
            # Generate API documentation
            content = self._generate_api_docs(repo_info)
            contribution['files_to_create'] = ['docs/API.md']
            contribution['generated_content']['api_docs'] = content

        contribution['implementation_notes'].extend([
            "Review existing documentation structure and style",
            "Ensure consistency with project's tone and formatting",
            "Include practical examples where appropriate",
            "Test all code examples before submitting"
        ])

        return contribution

    def _generate_issue_fix_contribution(self, contribution: Dict, repo_info: Dict) -> Dict:
        """Generate code fix for an issue"""
        opportunity = contribution['opportunity']

        # Generate sample fix based on common issue patterns
        if 'bug' in opportunity.get('description', '').lower():
            fix_content = self._generate_bug_fix(repo_info)
            contribution['files_to_modify'] = [f"src/{repo_info.get('primary_language', 'python').lower()}_file.py"]
        else:
            fix_content = self._generate_generic_fix(opportunity, repo_info)
            contribution['files_to_modify'] = ["relevant_file.py"]  # Placeholder

        contribution['generated_content']['code_fix'] = fix_content

        # Add test for the fix
        test_content = self._generate_test_for_fix(fix_content, repo_info)
        contribution['generated_content']['test_code'] = test_content
        contribution['files_to_create'] = ['tests/test_fix.py']

        contribution['implementation_notes'].extend([
            "Reproduce the issue locally before implementing fix",
            "Write tests that fail before the fix and pass after",
            "Consider edge cases and potential side effects",
            "Update relevant documentation if behavior changes"
        ])

        return contribution

    def _generate_testing_contribution(self, contribution: Dict, repo_info: Dict) -> Dict:
        """Generate testing-related contribution"""
        opportunity = contribution['opportunity']

        # Generate unit tests
        test_content = self._generate_unit_tests(repo_info)
        contribution['generated_content']['unit_tests'] = test_content
        contribution['files_to_create'] = ['tests/test_new_functionality.py']

        # Generate test configuration if needed
        if 'coverage' in opportunity['title'].lower():
            config_content = self._generate_test_config(repo_info)
            contribution['generated_content']['test_config'] = config_content
            contribution['files_to_create'].append('.coveragerc')

        contribution['implementation_notes'].extend([
            "Understand the existing test framework and structure",
            "Ensure tests follow project conventions",
            "Aim for comprehensive coverage of edge cases",
            "Run full test suite to ensure no regressions"
        ])

        return contribution

    def _generate_feature_contribution(self, contribution: Dict, repo_info: Dict) -> Dict:
        """Generate feature implementation"""
        opportunity = contribution['opportunity']

        # Generate feature code
        base_feature_content = self._generate_feature_code(opportunity, repo_info)
        # Enhance with Claude if available
        enhanced_feature_content = self._claude_enhance_code(base_feature_content, opportunity, repo_info)
        contribution['generated_content']['feature_code'] = enhanced_feature_content
        contribution['files_to_create'] = [f"src/features/{opportunity['title'].lower().replace(' ', '_')}.py"]

        # Generate tests for feature
        test_content = self._generate_feature_tests(opportunity, repo_info)
        contribution['generated_content']['feature_tests'] = test_content
        contribution['files_to_create'].append(f"tests/test_{opportunity['title'].lower().replace(' ', '_')}.py")

        contribution['implementation_notes'].extend([
            "Design feature to integrate smoothly with existing codebase",
            "Follow project's architectural patterns",
            "Implement comprehensive error handling",
            "Document the feature thoroughly"
        ])

        return contribution

    def _generate_installation_docs(self, repo_info: Dict) -> str:
        """Generate installation documentation"""
        language = repo_info.get('primary_language', 'Python').lower() if repo_info.get('primary_language') else 'python'

        if language == 'python':
            return """## Installation

### Prerequisites
- Python 3.7 or higher
- pip package manager

### Install from PyPI
```bash
pip install {package_name}
```

### Install from Source
```bash
git clone https://github.com/{repo_name}.git
cd {repo_name}
pip install -e .
```

### Development Installation
```bash
git clone https://github.com/{repo_name}.git
cd {repo_name}
pip install -e .[dev]
```""".format(
            package_name=repo_info['full_name'].split('/')[-1],
            repo_name=repo_info['full_name']
        )
        elif language == 'javascript':
            return """## Installation

### Prerequisites
- Node.js 14 or higher
- npm or yarn

### Install via npm
```bash
npm install {package_name}
```

### Install via yarn
```bash
yarn add {package_name}
```

### Development Setup
```bash
git clone https://github.com/{repo_name}.git
cd {repo_name}
npm install
npm run dev
```""".format(
            package_name=repo_info['full_name'].split('/')[-1],
            repo_name=repo_info['full_name']
        )
        else:
            return f"""## Installation

Please refer to the official documentation for {language} package installation procedures.

### From Source
```bash
git clone https://github.com/{repo_info['full_name']}.git
cd {repo_info['full_name'].split('/')[-1]}
# Follow language-specific build instructions
```"""

    def _generate_usage_docs(self, repo_info: Dict) -> str:
        """Generate usage documentation"""
        package_name = repo_info['full_name'].split('/')[-1]
        language = repo_info.get('primary_language', 'Python').lower() if repo_info.get('primary_language') else 'python'

        if language == 'python':
            return f"""## Usage

### Basic Example
```python
import {package_name.replace('-', '_')}

# Initialize the main component
client = {package_name.replace('-', '_')}.Client()

# Perform basic operations
result = client.process_data(your_data)
print(result)
```

### Advanced Usage
```python
from {package_name.replace('-', '_')} import Config, Processor

# Configure with custom settings
config = Config(
    option1="value1",
    option2="value2"
)

# Use advanced features
processor = Processor(config)
results = processor.batch_process(data_list)

for result in results:
    print(f"Processed: {{result}}")
```"""
        else:
            return f"""## Usage

### Quick Start
```{language}
// Basic usage example
const client = new {package_name.replace('-', '')}Client();
const result = await client.processData(yourData);
console.log(result);
```

### Configuration
```{language}
const config = {{
    option1: 'value1',
    option2: 'value2'
}};

const client = new {package_name.replace('-', '')}Client(config);
```"""

    def _generate_contributing_docs(self, repo_info: Dict) -> str:
        """Generate contributing guidelines"""
        return f"""# Contributing to {repo_info['full_name']}

Thank you for your interest in contributing! This document outlines the process for contributing to this project.

## Getting Started

1. **Fork the repository** on GitHub
2. **Clone your fork** locally:
   ```bash
   git clone https://github.com/YOUR_USERNAME/{repo_info['full_name'].split('/')[-1]}.git
   ```
3. **Create a new branch** for your feature or bug fix:
   ```bash
   git checkout -b feature/your-feature-name
   ```

## Development Setup

1. Install dependencies (see Installation section in README)
2. Run tests to ensure everything works:
   ```bash
   # Run project-specific test command
   python -m pytest  # or appropriate test runner
   ```

## Making Changes

1. **Write tests** for your changes
2. **Make your changes** following the project's coding style
3. **Run tests** to ensure nothing breaks
4. **Commit your changes** with descriptive commit messages

## Pull Request Process

1. **Push your changes** to your fork
2. **Submit a pull request** with:
   - Clear title and description
   - Reference to any related issues
   - List of changes made
   - Screenshots (if UI changes)

## Code Style

- Follow existing code conventions
- Use meaningful variable and function names
- Add comments for complex logic
- Keep functions focused and small

## Questions?

Feel free to open an issue for any questions about contributing!
"""

    def _generate_generic_readme_section(self, title: str, repo_info: Dict) -> str:
        """Generate a generic README section"""
        section_name = title.replace('Add ', '').replace(' section', '').title()
        return f"""## {section_name}

This section provides information about {section_name.lower()} for {repo_info['full_name']}.

### Overview

[Provide a brief overview of this topic]

### Details

[Add detailed information, examples, and explanations here]

### See Also

- [Related documentation]
- [External resources]
"""

    def _generate_api_docs(self, repo_info: Dict) -> str:
        """Generate API documentation"""
        return f"""# API Documentation for {repo_info['full_name']}

## Overview

This document describes the API endpoints and usage for {repo_info['full_name']}.

## Authentication

[Describe authentication requirements]

## Endpoints

### GET /api/example
Description of the endpoint

**Parameters:**
- `param1` (string): Description of parameter

**Response:**
```json
{{
  "status": "success",
  "data": {{}}
}}
```

### POST /api/example
Description of the endpoint

**Request Body:**
```json
{{
  "field1": "value1",
  "field2": "value2"
}}
```

**Response:**
```json
{{
  "status": "created",
  "id": "12345"
}}
```

## Error Handling

All API errors follow this format:
```json
{{
  "status": "error",
  "message": "Error description",
  "code": 400
}}
```
"""

    def _generate_bug_fix(self, repo_info: Dict) -> str:
        """Generate sample bug fix code"""
        language = repo_info.get('primary_language', 'Python').lower() if repo_info.get('primary_language') else 'python'

        if language == 'python':
            return '''def fixed_function(data):
    """
    Fixed function that properly handles edge cases.

    Args:
        data: Input data to process

    Returns:
        Processed data

    Raises:
        ValueError: If data is invalid
    """
    if data is None:
        raise ValueError("Data cannot be None")

    # Fix: Add proper validation and error handling
    if not isinstance(data, (list, dict, str)):
        raise ValueError(f"Unsupported data type: {type(data)}")

    # Previous code was missing this boundary check
    if isinstance(data, list) and len(data) == 0:
        return []

    # Apply the fix for the specific issue
    try:
        result = process_data_safely(data)
        return result
    except Exception as e:
        logger.error(f"Error processing data: {e}")
        raise

def process_data_safely(data):
    """Safely process data with proper error handling."""
    # Implementation with proper error handling
    return data  # Placeholder for actual logic
'''
        else:
            return f'''// Fixed function with proper error handling
function fixedFunction(data) {{
    if (data === null || data === undefined) {{
        throw new Error('Data cannot be null or undefined');
    }}

    // Fix: Add proper type checking
    if (typeof data !== 'object' && typeof data !== 'string') {{
        throw new Error(`Unsupported data type: ${{typeof data}}`);
    }}

    try {{
        return processDataSafely(data);
    }} catch (error) {{
        console.error('Error processing data:', error);
        throw error;
    }}
}}

function processDataSafely(data) {{
    // Implementation with proper error handling
    return data; // Placeholder for actual logic
}}'''

    def _generate_generic_fix(self, opportunity: Dict, repo_info: Dict) -> str:
        """Generate generic fix based on opportunity description"""
        return f'''# Fix for: {opportunity["title"]}

## Problem
{opportunity.get("description", "Issue description not available")}

## Solution
```python
def improved_function():
    """
    Improved implementation that addresses the issue.
    """
    # Add proper implementation here
    pass

# Additional helper functions if needed
def helper_function():
    """Helper function to support the main fix."""
    pass
```

## Testing
```python
def test_fix():
    """Test to verify the fix works correctly."""
    # Add test implementation
    assert improved_function() is not None
```
'''

    def _generate_test_for_fix(self, fix_content: str, repo_info: Dict) -> str:
        """Generate test code for a fix"""
        return '''import pytest
from unittest.mock import patch, MagicMock

def test_fixed_function_with_valid_data():
    """Test that the fixed function works with valid data."""
    test_data = {"key": "value"}
    result = fixed_function(test_data)
    assert result is not None

def test_fixed_function_with_none_data():
    """Test that function properly handles None input."""
    with pytest.raises(ValueError, match="Data cannot be None"):
        fixed_function(None)

def test_fixed_function_with_invalid_type():
    """Test that function properly handles invalid data types."""
    with pytest.raises(ValueError, match="Unsupported data type"):
        fixed_function(123)

def test_fixed_function_with_empty_list():
    """Test that function properly handles empty lists."""
    result = fixed_function([])
    assert result == []

def test_fixed_function_error_handling():
    """Test that function properly handles processing errors."""
    with patch('__main__.process_data_safely') as mock_process:
        mock_process.side_effect = Exception("Processing error")

        with pytest.raises(Exception):
            fixed_function({"test": "data"})

def test_edge_cases():
    """Test various edge cases."""
    # Test with different data types
    test_cases = [
        {"data": []},
        {"data": {}},
        {"data": "test_string"},
        {"data": [1, 2, 3]}
    ]

    for case in test_cases:
        result = fixed_function(case["data"])
        assert result is not None
'''

    def _generate_unit_tests(self, repo_info: Dict) -> str:
        """Generate comprehensive unit tests"""
        package_name = repo_info['full_name'].split('/')[-1].replace('-', '_')

        return f'''import pytest
from unittest.mock import Mock, patch

class Test{package_name.title().replace('_', '')}:
    """Comprehensive test suite for {package_name}."""

    def setup_method(self):
        """Set up test fixtures before each test method."""
        self.test_data = {{"test": "data"}}
        self.mock_client = Mock()

    def test_initialization(self):
        """Test proper initialization of main components."""
        # Add actual import and test here
        assert True  # Placeholder

    def test_basic_functionality(self):
        """Test basic functionality works as expected."""
        # Add actual functionality tests here
        assert True  # Placeholder

    def test_error_handling(self):
        """Test that errors are properly handled."""
        with pytest.raises(ValueError):
            # Add actual error test here
            raise ValueError("Test error")

    def test_edge_cases(self):
        """Test various edge cases."""
        # Add edge case tests here
        assert True  # Placeholder

    def test_configuration(self):
        """Test different configuration options."""
        # Add configuration tests here
        assert True  # Placeholder
'''

    def _generate_test_config(self, repo_info: Dict) -> str:
        """Generate test configuration file"""
        return '''# Coverage configuration
[run]
source = .
omit =
    tests/*
    setup.py
    */__pycache__/*
    */venv/*
    */env/*

[report]
exclude_lines =
    pragma: no cover
    def __repr__
    raise AssertionError
    raise NotImplementedError

precision = 2
show_missing = True

[html]
directory = htmlcov
'''

    def _generate_feature_code(self, opportunity: Dict, repo_info: Dict) -> str:
        """Generate feature implementation code"""
        feature_name = opportunity['title'].lower().replace(' ', '_')

        return f'''"""
{opportunity['title']} Feature Implementation

This module implements {opportunity['title'].lower()} functionality.
"""

import logging
from typing import Dict, List, Optional, Any

logger = logging.getLogger(__name__)

class {feature_name.title().replace('_', '')}:
    """
    Implements {opportunity['title'].lower()} feature.

    This class provides methods for {opportunity.get('description', 'feature functionality')}.
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the {feature_name} feature.

        Args:
            config: Configuration dictionary for the feature
        """
        self.config = config or {{}}
        self._initialized = False
        self._setup()

    def _setup(self) -> None:
        """Set up the feature with configuration."""
        try:
            # Initialize feature components
            logger.info(f"Initializing {feature_name} feature")
            self._initialized = True
        except Exception as e:
            logger.error(f"Failed to initialize {feature_name}: {{e}}")
            raise

    def process(self, data: Any) -> Any:
        """
        Main processing method for the feature.

        Args:
            data: Input data to process

        Returns:
            Processed data

        Raises:
            ValueError: If data is invalid
            RuntimeError: If feature is not initialized
        """
        if not self._initialized:
            raise RuntimeError("Feature not properly initialized")

        if data is None:
            raise ValueError("Input data cannot be None")

        try:
            result = self._process_internal(data)
            logger.debug(f"Successfully processed data with {feature_name}")
            return result
        except Exception as e:
            logger.error(f"Error in {feature_name} processing: {{e}}")
            raise

    def _process_internal(self, data: Any) -> Any:
        """
        Internal processing implementation.

        Args:
            data: Data to process

        Returns:
            Processed data
        """
        # Implement feature-specific logic here
        processed_data = data

        # Apply feature transformations
        if isinstance(data, dict):
            processed_data = self._process_dict(data)
        elif isinstance(data, list):
            processed_data = self._process_list(data)
        else:
            processed_data = self._process_other(data)

        return processed_data

    def _process_dict(self, data: Dict) -> Dict:
        """Process dictionary data."""
        return {{k: v for k, v in data.items() if v is not None}}

    def _process_list(self, data: List) -> List:
        """Process list data."""
        return [item for item in data if item is not None]

    def _process_other(self, data: Any) -> Any:
        """Process other data types."""
        return data

    def get_status(self) -> Dict[str, Any]:
        """
        Get current feature status.

        Returns:
            Status information dictionary
        """
        return {{
            "initialized": self._initialized,
            "config": self.config,
            "feature_name": "{feature_name}"
        }}

# Utility functions for the feature
def create_{feature_name}(config: Optional[Dict] = None):
    """
    Factory function to create a {feature_name} instance.

    Args:
        config: Optional configuration dictionary

    Returns:
        Configured {feature_name} instance
    """
    return {feature_name.title().replace('_', '')}(config)
'''

    def _claude_enhance_code(self, base_code: str, opportunity: Dict, repo_info: Dict) -> str:
        """Use Claude to enhance and improve generated code"""
        if not self.use_ai:
            return base_code

        try:
            prompt = f"""Please review and enhance this Python code for a {opportunity['type']} contribution to the {repo_info['full_name']} repository.

Current Code:
```python
{base_code[:2000]}  # Truncated for context
```

Repository Info:
- Language: {repo_info.get('primary_language', 'Python')}
- Type: {opportunity['type']}
- Title: {opportunity['title']}
- Description: {opportunity.get('description', 'No description')}

Please improve the code by:
1. Adding better error handling
2. Improving documentation and docstrings
3. Adding type hints where missing
4. Following Python best practices
5. Making it more maintainable and readable

Return only the improved Python code without explanation."""

            response = self.claude.messages.create(
                model="claude-3-haiku-20240307",
                max_tokens=3000,
                temperature=0.2,
                messages=[{
                    "role": "user",
                    "content": prompt
                }]
            )

            enhanced_code = response.content[0].text

            # Clean up the response to extract just the code
            if "```python" in enhanced_code:
                enhanced_code = enhanced_code.split("```python")[1].split("```")[0].strip()
            elif "```" in enhanced_code:
                enhanced_code = enhanced_code.split("```")[1].strip()

            return enhanced_code if enhanced_code else base_code

        except Exception as e:
            self.console.print(f"❌ Claude code enhancement failed: {str(e)}")
            return base_code

    def _generate_feature_tests(self, opportunity: Dict, repo_info: Dict) -> str:
        """Generate tests for feature implementation"""
        feature_name = opportunity['title'].lower().replace(' ', '_')
        class_name = feature_name.title().replace('_', '')

        return f'''import pytest
from unittest.mock import Mock, patch

# Note: Actual imports would be added here based on the feature implementation

class Test{class_name}:
    """Test suite for {class_name} feature."""

    def setup_method(self):
        """Set up test fixtures."""
        self.config = {{"test_option": "test_value"}}
        self.test_data = {{"key": "value", "number": 42}}

    def test_initialization(self):
        """Test feature initialization."""
        # Add actual initialization tests
        assert True  # Placeholder

    def test_process_valid_data(self):
        """Test processing with valid data."""
        # Add actual processing tests
        assert True  # Placeholder

    def test_process_none_data(self):
        """Test that processing None data raises ValueError."""
        with pytest.raises(ValueError, match="Input data cannot be None"):
            # Add actual test implementation
            raise ValueError("Input data cannot be None")

    def test_validate_valid_data(self):
        """Test validation with valid data."""
        # Add actual validation tests
        assert True  # Placeholder

    def test_get_status(self):
        """Test getting feature status."""
        # Add actual status tests
        assert True  # Placeholder
'''

    def _generate_pr_template(self, contribution: Dict) -> Dict:
        """Generate pull request template"""
        opportunity = contribution['opportunity']

        # Determine PR type and customize accordingly
        pr_type = opportunity['type']
        title = f"{pr_type.title()}: {opportunity['title']}"

        # Generate description based on contribution type
        if pr_type == 'documentation':
            description = f"""## Summary
This PR adds/improves documentation for {opportunity['title']}.

## Changes Made
- Added comprehensive documentation section
- Included practical examples and code snippets
- Followed project's documentation style and formatting

## Motivation
Documentation was missing or incomplete, making it difficult for users to understand how to use this feature effectively.
"""
        elif pr_type == 'issue':
            description = f"""## Summary
This PR fixes the issue described in #{opportunity.get('issue_number', 'XXX')}: {opportunity['title']}.

## Changes Made
- Implemented proper error handling and validation
- Added comprehensive tests to prevent regression
- Updated documentation where applicable

## Root Cause
[Describe what was causing the issue]

## Solution
[Describe how the fix works]

## Testing
- [x] Added unit tests
- [x] Tested locally with various input scenarios
- [x] Verified no existing functionality is broken

Fixes #{opportunity.get('issue_number', 'XXX')}
"""
        elif pr_type == 'testing':
            description = f"""## Summary
This PR improves test coverage by adding {opportunity['title'].lower()}.

## Changes Made
- Added comprehensive unit tests covering various scenarios
- Included edge case testing
- Added test configuration if needed
- Achieved XX% test coverage increase

## Testing Strategy
- Unit tests for core functionality
- Integration tests for component interaction
- Performance tests for critical paths
- Error handling validation
"""
        else:
            description = f"""## Summary
This PR implements {opportunity['title'].lower()}.

## Changes Made
- [List specific changes made]
- [Include any breaking changes]
- [Note any configuration updates needed]

## Motivation
[Explain why this change is needed]

## Testing
- [x] Added comprehensive tests
- [x] Verified backward compatibility
- [x] Tested edge cases
"""

        return {
            'title': title,
            'description': description + "\n\n🤖 Generated with Open Source Contributor Agent\n\nCo-Authored-By: ContributorAgent <noreply@example.com>",
            'labels': self._suggest_pr_labels(opportunity),
            'reviewers': [],  # Can be populated with maintainer info
            'draft': False
        }

    def _suggest_pr_labels(self, opportunity: Dict) -> List[str]:
        """Suggest appropriate labels for the PR"""
        labels = []

        pr_type = opportunity['type']
        if pr_type == 'documentation':
            labels.extend(['documentation', 'improvement'])
        elif pr_type == 'issue':
            labels.extend(['bug fix', 'improvement'])
        elif pr_type == 'testing':
            labels.extend(['testing', 'enhancement'])
        elif pr_type == 'feature':
            labels.extend(['feature', 'enhancement'])

        # Add priority-based labels
        priority = opportunity.get('priority', 'medium')
        if priority == 'high':
            labels.append('high-priority')
        elif priority == 'low':
            labels.append('low-priority')

        return labels

    def _generate_commit_messages(self, contribution: Dict) -> List[str]:
        """Generate appropriate commit messages"""
        opportunity = contribution['opportunity']
        messages = []

        pr_type = opportunity['type']

        if pr_type == 'documentation':
            if contribution.get('files_to_create'):
                messages.append(f"docs: add {opportunity['title'].lower()}")
            if contribution.get('files_to_modify'):
                messages.append(f"docs: update {opportunity['title'].lower()}")

        elif pr_type == 'issue':
            messages.append(f"fix: resolve {opportunity['title'].lower()}")
            if 'test_code' in contribution.get('generated_content', {}):
                messages.append(f"test: add tests for {opportunity['title'].lower()}")

        elif pr_type == 'testing':
            messages.append(f"test: add {opportunity['title'].lower()}")
            if 'test_config' in contribution.get('generated_content', {}):
                messages.append("chore: update test configuration")

        elif pr_type == 'feature':
            messages.append(f"feat: implement {opportunity['title'].lower()}")
            messages.append(f"test: add tests for {opportunity['title'].lower()}")

        return messages

    def display_contribution(self, contribution: Dict) -> None:
        """Display generated contribution in a formatted way"""
        opportunity = contribution['opportunity']

        # Header
        self.console.print(Panel(
            f"[bold cyan]{opportunity['title']}[/bold cyan]\n"
            f"Type: {opportunity['type'].title()}\n"
            f"Repository: {contribution['repository']}\n"
            f"Priority: {opportunity.get('priority', 'medium').title()}",
            title="💻 Generated Contribution"
        ))

        # Files to be modified/created
        if contribution['files_to_create'] or contribution['files_to_modify']:
            files_text = ""
            if contribution['files_to_create']:
                files_text += "**Files to Create:**\n" + "\n".join([f"- {f}" for f in contribution['files_to_create']]) + "\n\n"
            if contribution['files_to_modify']:
                files_text += "**Files to Modify:**\n" + "\n".join([f"- {f}" for f in contribution['files_to_modify']])

            self.console.print(Panel(files_text, title="📁 File Changes"))

        # Generated content preview
        if contribution['generated_content']:
            for content_type, content in contribution['generated_content'].items():
                if content and len(content.strip()) > 0:
                    # Show first 500 characters of generated content
                    preview = content[:500] + "..." if len(content) > 500 else content

                    language = "python" if content_type in ['code_fix', 'feature_code', 'unit_tests'] else "markdown"
                    syntax = Syntax(preview, language, theme="monokai", line_numbers=True)

                    self.console.print(Panel(
                        syntax,
                        title=f"📝 Generated {content_type.replace('_', ' ').title()}"
                    ))

        # PR Template
        pr = contribution['pr_template']
        self.console.print(Panel(
            f"**Title:** {pr['title']}\n\n**Labels:** {', '.join(pr['labels'])}\n\n**Description Preview:**\n{pr['description'][:300]}...",
            title="🔀 Pull Request Template"
        ))

        # Implementation Notes
        if contribution['implementation_notes']:
            notes_text = "\n".join([f"• {note}" for note in contribution['implementation_notes']])
            self.console.print(Panel(notes_text, title="📋 Implementation Notes"))

    def save_contribution(self, contribution: Dict, filename: str = None) -> None:
        """Save generated contribution to file"""
        if not filename:
            repo_name = contribution['repository'].replace('/', '_')
            opportunity_name = contribution['opportunity']['title'].lower().replace(' ', '_')
            filename = f"data/contribution_{repo_name}_{opportunity_name}.json"

        save_json(contribution, filename)
        self.console.print(f"💾 Contribution saved to {filename}")

if __name__ == "__main__":
    # Example usage
    coder = CoderAgent()

    # Sample strategy item
    sample_strategy_item = {
        'opportunity': {
            'type': 'documentation',
            'title': 'Add installation section to README',
            'description': 'README is missing installation information',
            'priority': 'medium',
            'effort': 'low',
            'impact': 'medium'
        }
    }

    sample_repo_info = {
        'full_name': 'example/awesome-project',
        'primary_language': 'Python'
    }

    contribution = coder.generate_contribution(sample_strategy_item, sample_repo_info)
    coder.display_contribution(contribution)