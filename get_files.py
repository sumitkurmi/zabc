import subprocess
import sys

def run_git_command(cmd):
    """Executes a git command and returns output as a sorted list of unique files."""
    try:
        result = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=True
        )
        files = result.stdout.splitlines()
        return sorted(list(set(files)))
    except subprocess.CalledProcessError as e:
        print(f"Error running git: {e.stderr}")
        sys.exit(1)
    except FileNotFoundError:
        print("Error: Git is not installed or not found in system PATH.")
        sys.exit(1)

def get_staged_files():
    # Files staged for commit (index)
    return run_git_command(['git', 'diff', '--name-only', '--cached'])

def get_unstaged_files():
    # Unstaged modified files + untracked files (respecting .gitignore)
    modified = run_git_command(['git', 'diff', '--name-only'])
    untracked = run_git_command(['git', 'ls-files', '-o', '--exclude-standard'])
    return sorted(list(set(modified + untracked)))

def get_all_uncommitted_files():
    # Both staged and unstaged/untracked changes combined
    return sorted(list(set(get_staged_files() + get_unstaged_files())))

def prompt_user_choice():
    print("=== Git Status File Inspector ===")
    print("1. Staged files only")
    print("2. Unstaged / Untracked files only")
    print("3. Both (All uncommitted files)")
    
    while True:
        choice = input("\nEnter your choice (1, 2, or 3): ").strip()
        if choice in ['1', '2', '3']:
            return choice
        print("Invalid choice. Please enter 1, 2, or 3.")

if __name__ == '__main__':
    choice = prompt_user_choice()
    
    if choice == '1':
        title = "Staged Files"
        files = get_staged_files()
    elif choice == '2':
        title = "Unstaged / Untracked Files"
        files = get_unstaged_files()
    else:
        title = "All Uncommitted Files (Staged + Unstaged/Untracked)"
        files = get_all_uncommitted_files()
        
    print(f"\n=== Found {len(files)} {title} ===\n")
    if files:
        for f in files:
            print(f)
    else:
        print("No files found.")