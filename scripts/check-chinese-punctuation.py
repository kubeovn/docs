#!/usr/bin/env python3
"""
Lint script to check for Chinese punctuation in English markdown files (.en.md)
"""

import os
import sys
import re
import glob
import argparse
from pathlib import Path


def get_punctuation_mapping():
    """
    Get the mapping from Chinese punctuation to English punctuation.
    """
    return {
        '。': '.',
        '，': ',',
        '？': '?',
        '！': '!',
        '；': ';',
        '：': ':',
        '“': '"',
        '”': '"',
        '’': "'",
        '‘': "'",
        '（': '(',
        '）': ')',
        '【': '[',
        '】': ']',
        '《': '<',
        '》': '>',
        '…': '...',
        '——': '--',
        '－': '-',
    }


def find_chinese_punctuation(text):
    """
    Find Chinese punctuation marks in the given text.
    Returns a list of tuples (char, position) for each found punctuation.
    """
    # Define Chinese punctuation patterns
    chinese_punctuation = {
        '。': 'Chinese period (should be .)',
        '，': 'Chinese comma (should be ,)',
        '？': 'Chinese question mark (should be ?)',
        '！': 'Chinese exclamation mark (should be !)',
        '；': 'Chinese semicolon (should be ;)',
        '：': 'Chinese colon (should be :)',
        '“': 'Chinese left double quote (should be ")',
        '”': 'Chinese right double quote (should be ")',
        '‘': 'Chinese left single quote (should be \')',
        '’': 'Chinese right single quote (should be \')',
        '（': 'Chinese left parenthesis (should be ()',
        '）': 'Chinese right parenthesis (should be ))',
        '【': 'Chinese left bracket (should be [)',
        '】': 'Chinese right bracket (should be ])',
        '《': 'Chinese left angle bracket (should be <)',
        '》': 'Chinese right angle bracket (should be >)',
        '…': 'Chinese ellipsis (should be ...)',
        '——': 'Chinese dash (should be --)',
        '－': 'Chinese minus (should be -)',
    }
    
    found = []
    for i, char in enumerate(text):
        if char in chinese_punctuation:
            found.append((char, i, chinese_punctuation[char]))
    
    return found


def fix_chinese_punctuation(text):
    """
    Replace Chinese punctuation with English equivalents in the given text.
    Returns the fixed text and the number of replacements made.
    """
    mapping = get_punctuation_mapping()
    fixed_text = text
    replacements = 0
    
    for chinese_punct, english_punct in mapping.items():
        if chinese_punct in fixed_text:
            count = fixed_text.count(chinese_punct)
            fixed_text = fixed_text.replace(chinese_punct, english_punct)
            replacements += count
    
    return fixed_text, replacements


def is_code_block_line(line, in_code_block):
    """
    Check if a line is part of a code block.
    Returns (is_code_line, new_in_code_block_state).
    """
    stripped = line.strip()
    
    # Check for code fence
    if stripped.startswith('```'):
        return True, not in_code_block
    
    # If we're in a code block, this line is code
    if in_code_block:
        return True, in_code_block
    
    # Check for indented code blocks
    if line.startswith('    ') or line.startswith('\t'):
        return True, in_code_block
    
    return False, in_code_block


def check_file(file_path):
    """
    Check a single file for Chinese punctuation.
    Returns a list of issues found.
    """
    issues = []
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
    except Exception as e:
        print(f"Error reading {file_path}: {e}")
        return issues
    
    in_code_block = False
    for line_num, line in enumerate(lines, 1):
        # Check if this line is part of a code block
        is_code_line, in_code_block = is_code_block_line(line, in_code_block)
        if is_code_line:
            continue
            
        chinese_punct = find_chinese_punctuation(line)
        for char, pos, description in chinese_punct:
            issues.append({
                'file': file_path,
                'line': line_num,
                'column': pos + 1,
                'char': char,
                'description': description,
                'line_content': line.rstrip()
            })
    
    return issues


def fix_file(file_path):
    """
    Fix Chinese punctuation in a single file.
    Returns the number of replacements made.
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
    except Exception as e:
        print(f"Error reading {file_path}: {e}")
        return 0
    
    total_replacements = 0
    fixed_lines = []
    in_code_block = False
    
    for line in lines:
        # Check if this line is part of a code block
        is_code_line, in_code_block = is_code_block_line(line, in_code_block)
        
        if is_code_line:
            # Don't fix punctuation in code blocks
            fixed_lines.append(line)
        else:
            # Fix punctuation in regular text
            fixed_line, replacements = fix_chinese_punctuation(line)
            fixed_lines.append(fixed_line)
            total_replacements += replacements
    
    # Write back to file if there were changes
    if total_replacements > 0:
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.writelines(fixed_lines)
        except Exception as e:
            print(f"Error writing {file_path}: {e}")
            return 0
    
    return total_replacements


def find_en_md_files():
    """
    Find all .en.md files in the current directory and subdirectories.
    """
    en_md_files = []
    for root, dirs, files in os.walk('.'):
        for file in files:
            if file.endswith('.en.md'):
                en_md_files.append(os.path.join(root, file))
    
    return sorted(en_md_files)


def main():
    """
    Main function to run the Chinese punctuation checker.
    """
    parser = argparse.ArgumentParser(description='Check for Chinese punctuation in English markdown files (.en.md)')
    parser.add_argument('--fix', action='store_true', help='Automatically fix Chinese punctuation issues')
    args = parser.parse_args()
    
    if args.fix:
        print("🔧 Fixing Chinese punctuation in English markdown files (.en.md)...")
    else:
        print("🔍 Checking for Chinese punctuation in English markdown files (.en.md)...")
    print()
    
    # Find all .en.md files
    en_md_files = find_en_md_files()
    
    if not en_md_files:
        print("ℹ️  No .en.md files found.")
        return 0
    
    print(f"📄 Found {len(en_md_files)} .en.md files to {'fix' if args.fix else 'check'}")
    print()
    
    if args.fix:
        # Fix mode
        total_replacements = 0
        files_fixed = 0
        
        for file_path in en_md_files:
            replacements = fix_file(file_path)
            if replacements > 0:
                files_fixed += 1
                total_replacements += replacements
                print(f"✅ {file_path}: {replacements} punctuation marks fixed")
        
        # Summary
        print("=" * 60)
        if total_replacements == 0:
            print("✅ All English markdown files are already clean! No Chinese punctuation found.")
            return 0
        else:
            print(f"🎉 Fixed {total_replacements} Chinese punctuation marks in {files_fixed} files.")
            return 0
    else:
        # Check mode (original behavior)
        total_issues = 0
        files_with_issues = 0
        
        for file_path in en_md_files:
            issues = check_file(file_path)
            
            if issues:
                files_with_issues += 1
                total_issues += len(issues)
                
                print(f"❌ {file_path}")
                for issue in issues:
                    print(f"   Line {issue['line']}, Column {issue['column']}: "
                          f"'{issue['char']}' - {issue['description']}")
                    print(f"   > {issue['line_content']}")
                    print(f"   > {' ' * (issue['column'] - 1)}^")
                print()
        
        # Summary
        print("=" * 60)
        if total_issues == 0:
            print("✅ All English markdown files are clean! No Chinese punctuation found.")
            return 0
        else:
            print(f"❌ Found {total_issues} Chinese punctuation issues in {files_with_issues} files.")
            print()
            print("💡 Please replace Chinese punctuation with English equivalents:")
            print("   。 → .    ， → ,    ？ → ?    ！ → !")
            print("   ： → :    ； → ;    （） → ()   【】 → []")
            print("   "" → \"\"   '' → ''   《》 → <>   … → ...")
            print()
            print("🔧 Tip: Use --fix to automatically fix these issues!")
            return 1


if __name__ == "__main__":
    sys.exit(main())
