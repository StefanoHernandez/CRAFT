#!/usr/bin/env python3
"""
Script to update deprecated LLM model names across all documentation and code files.
"""

import os
import re
from pathlib import Path

# Model mappings: old -> new (November 2025)
MODEL_UPDATES = {
    # OpenAI - GPT-5.1 is flagship, GPT-4o for compatibility
    r'gpt-4o(-preview)?': 'gpt-4o',
    r'gpt-4o(?![\w-])': 'gpt-4o',  # Keep gpt-4o as good default for examples
    
    # Anthropic - Claude 4.5 series (Opus/Sonnet/Haiku)
    r'claude-sonnet-4.5': 'claude-sonnet-4.5',
    r'claude-3\.5-sonnet-20241022': 'claude-sonnet-4.5',
    r'claude-sonnet-4.5': 'claude-sonnet-4.5',
    r'claude-opus-4.5': 'claude-opus-4.5',
    r'claude-haiku-4.5': 'claude-haiku-4.5',
    
    # Google - Gemini 3 Pro (preview), Gemini 2.5 for production
    r'gemini-1\.5-pro': 'gemini-2.5-pro',
    r'gemini-1\.5-flash': 'gemini-2.5-flash',
}

# Premium/Flagship models for high-end examples
FLAGSHIP_MODELS = {
    'openai': 'gpt-5.1',  # Most capable, for complex reasoning
    'anthropic': 'claude-opus-4.5',  # Most capable Claude
    'google': 'gemini-3-pro',  # Latest preview
}

# Production-ready models for standard examples
PRODUCTION_MODELS = {
    'openai': 'gpt-4o',  # Fast, reliable
    'anthropic': 'claude-sonnet-4.5',  # Balanced
    'google': 'gemini-2.5-pro',  # Generally available
}

def update_file(filepath: Path):
    """Update model names in a single file."""
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    original_content = content
    
    # Apply all replacements
    for old_pattern, new_model in MODEL_UPDATES.items():
        content = re.sub(old_pattern, new_model, content)
    
    # Only write if changes were made
    if content != original_content:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        return True
    return False

def main():
    project_root = Path('/Users/stefano/Documents/Progetti_personali/CRAFT')
    
    # File patterns to update
    patterns = ['**/*.md', '**/*.py', '**/*.ts', '**/*.tsx', '**/*.json']
    
    # Directories to exclude
    excludes = {'.venv', 'venv', 'node_modules', '.git', '__pycache__', 'htmlcov'}
    
    updated_files = []
    
    for pattern in patterns:
        for filepath in project_root.glob(pattern):
            # Skip excluded directories
            if any(exclude in filepath.parts for exclude in excludes):
                continue
            
            try:
                if update_file(filepath):
                    updated_files.append(filepath)
                    print(f"✓ Updated: {filepath.relative_to(project_root)}")
            except Exception as e:
                print(f"✗ Error updating {filepath}: {e}")
    
    print(f"\n✅ Updated {len(updated_files)} files")

if __name__ == '__main__':
    main()
