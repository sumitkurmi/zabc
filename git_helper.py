"""
        git helper file
"""

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

def unstage_all_files():
    """Unstages all currently staged files (git restore --staged .)."""
    try:
        subprocess.run(['git', 'restore', '--staged', '.'], check=True, text=True)
        print("\nSuccess: All staged files have been unstaged.")
    except subprocess.CalledProcessError as e:
        print(f"Error unstaging files: {e}")
        sys.exit(1)

def reset_to_commit_snapshot():
    """Resets the repository or creates a new branch pointing to a past commit."""
    commit_hash = input("\nEnter the target commit hash: ").strip()
    if not commit_hash:
        print("Commit hash cannot be empty. Aborted.")
        return

    print("\nHow would you like to restore this snapshot?")
    print("1. Permanently reset current branch (HARD RESET - discards changes after commit)")
    print("2. Create a new branch from this commit (Safe)")
    print("3. Inspect commit in detached HEAD mode (Read-only view)")
    
    mode = input("\nSelect option (1-3): ").strip()

    if mode == '1':
        confirm = input(f"\nWARNING: Permanent reset to {commit_hash}. ALL uncommitted changes and newer commits WILL BE LOST. Continue? (y/N): ").strip().lower()
        if confirm == 'y':
            try:
                subprocess.run(['git', 'reset', '--hard', commit_hash], check=True, text=True)
                print(f"\nSuccess: Local repo reset to commit {commit_hash}.")
            except subprocess.CalledProcessError as e:
                print(f"\nError during reset: {e.stderr.strip() if e.stderr else e}")
        else:
            print("\nOperation cancelled.")

    elif mode == '2':
        branch_name = input("Enter new branch name: ").strip()
        if not branch_name:
            print("Branch name cannot be empty. Aborted.")
            return
        try:
            subprocess.run(['git', 'checkout', '-b', branch_name, commit_hash], check=True, text=True)
            print(f"\nSuccess: Created and switched to branch '{branch_name}' at commit {commit_hash}.")
        except subprocess.CalledProcessError as e:
            print(f"\nError creating branch: {e.stderr.strip() if e.stderr else e}")

    elif mode == '3':
        try:
            subprocess.run(['git', 'checkout', commit_hash], check=True, text=True)
            print(f"\nSuccess: Switched to detached HEAD at commit {commit_hash}.")
        except subprocess.CalledProcessError as e:
            print(f"\nError checking out commit: {e.stderr.strip() if e.stderr else e}")
    else:
        print("Invalid selection. Aborted.")

def soft_delete_last_commit():
    """Resets the last commit softly, keeping changes staged."""
    try:
        subprocess.run(['git', 'reset', '--soft', 'HEAD~1'], check=True, text=True)
        print("\nSuccess: Last commit soft-reset (changes remain staged).")
    except subprocess.CalledProcessError as e:
        print(f"Error resetting commit: {e}")
        sys.exit(1)

def hard_delete_last_commit():
    """Resets the last commit hard, discarding all changes in working tree and staging area."""
    confirm = input("\nWARNING: A hard reset will permanently discard the last commit and ALL uncommitted changes. Are you sure? (y/N): ").strip().lower()
    if confirm == 'y':
        try:
            subprocess.run(['git', 'reset', '--hard', 'HEAD~1'], check=True, text=True)
            print("\nSuccess: Last commit hard-reset (changes discarded).")
        except subprocess.CalledProcessError as e:
            print(f"Error resetting commit: {e}")
            sys.exit(1)
    else:
        print("\nOperation cancelled.")

def get_all_branches():
    """Helper function to fetch all local git branches."""
    try:
        result = subprocess.run(
            ['git', 'branch', '--format=%(refname:short)'],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=True
        )
        branches = [b.strip() for b in result.stdout.splitlines() if b.strip()]
        return branches
    except subprocess.CalledProcessError:
        # Fallback for older git versions
        try:
            result = subprocess.run(['git', 'branch'], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=True)
            return [line.replace('*', '').strip() for line in result.stdout.splitlines() if line.strip()]
        except Exception:
            return []

def print_recent_commits():
    """Dynamically lists local branches, lets the user select one, and prints recent commits."""
    branches = get_all_branches()
    
    print("\n=== Available Branches ===")
    print("0. Current Branch (Default)")
    for i, branch in enumerate(branches, 1):
        print(f"{i}. {branch}")
        
    selected_branch = ""
    if branches:
        branch_choice = input(f"\nSelect branch number (0-{len(branches)}): ").strip()
        if branch_choice.isdigit():
            idx = int(branch_choice)
            if 1 <= idx <= len(branches):
                selected_branch = branches[idx - 1]
            elif idx != 0:
                print("Invalid selection. Defaulting to current branch.")
    
    count_input = input("How many recent commits to show? (default 5): ").strip()
    count = count_input if count_input.isdigit() else "5"
    
    cmd = ['git', 'log', '-n', count, '--oneline']
    if selected_branch:
        cmd.insert(2, selected_branch)
        
    try:
        result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=True)
        branch_label = f"on branch [{selected_branch}]" if selected_branch else "on current branch"
        print(f"\n=== Recent {count} Commits {branch_label} ===\n")
        print(result.stdout if result.stdout.strip() else "No commits found.")
    except subprocess.CalledProcessError as e:
        print(f"Error fetching commits: {e.stderr.strip()}")

def amend_last_commit():
    """Amends the last commit message."""
    new_msg = input("\nEnter the new commit message: ").strip()
    if not new_msg:
        print("Commit message cannot be empty. Aborted.")
        return
    try:
        subprocess.run(['git', 'commit', '--amend', '-m', new_msg], check=True, text=True)
        print("\nSuccess: Last commit message amended successfully.")
    except subprocess.CalledProcessError as e:
        print(f"Error amending commit: {e}")

def abort_cherry_pick():
    """Aborts an in-progress cherry-pick operation and restores pre-cherry-pick state."""
    try:
        subprocess.run(['git', 'cherry-pick', '--abort'], check=True, text=True)
        print("\nSuccess: Cherry-pick operation aborted successfully.")
    except subprocess.CalledProcessError as e:
        print(f"\nError aborting cherry-pick: {e.stderr.strip() if e.stderr else e}")

def cherry_pick_changes_only():
    """Applies commit changes without committing, optionally unstaging them."""
    commit_hash = input("\nEnter the commit hash: ").strip()
    if not commit_hash:
        print("Commit hash cannot be empty. Aborted.")
        return

    unstage_choice = input("Do you want to leave changes UNSTAGED in working directory? (y/N): ").strip().lower()

    try:
        # Step 1: Cherry-pick without committing (stages changes)
        subprocess.run(['git', 'cherry-pick', '-n', commit_hash], check=True, text=True)
        
        # Step 2: Unstage files if requested
        if unstage_choice == 'y':
            subprocess.run(['git', 'restore', '--staged', '.'], check=True, text=True)
            print(f"\nSuccess: Changes from {commit_hash} applied as UNSTAGED (no commit created).")
        else:
            print(f"\nSuccess: Changes from {commit_hash} applied as STAGED (no commit created).")
            
    except subprocess.CalledProcessError as e:
        print(f"\nError during operation: {e.stderr.strip() if e.stderr else e}")

def prompt_user_choice():
    print("=== Git Status & Commit Manager ===")
    print("1. Staged files only")
    print("2. Unstaged / Untracked files only")
    print("3. Both (All uncommitted files)")
    print("4. Soft delete last commit (git reset --soft HEAD~1)")
    print("5. Hard delete last commit (git reset --hard HEAD~1)")
    print("6. Print recent commits (dynamic branch selection)")
    print("7. Amend last commit message (git commit --amend)")
    print("8. Abort in-progress cherry-pick (git cherry-pick --abort)")
    print("9. Cherry-pick changes only without committing (git cherry-pick -n)")
    print("10. Unstage all staged files (git restore --staged .)")
    print("11. Restore repository state to a past commit snapshot")
    
    valid_choices = [str(i) for i in range(1, 12)]
    while True:
        choice = input("\nEnter your choice (1-11): ").strip()
        if choice in valid_choices:
            return choice
        print("Invalid choice. Please enter a number between 1 and 11.")

if __name__ == '__main__':
    choice = prompt_user_choice()
    
    if choice == '1':
        title = "Staged Files"
        files = get_staged_files()
        print(f"\n=== Found {len(files)} {title} ===\n")
        if files:
            for f in files: print(f)
        else:
            print("No files found.")
            
    elif choice == '2':
        title = "Unstaged / Untracked Files"
        files = get_unstaged_files()
        print(f"\n=== Found {len(files)} {title} ===\n")
        if files:
            for f in files: print(f)
        else:
            print("No files found.")
            
    elif choice == '3':
        title = "All Uncommitted Files (Staged + Unstaged/Untracked)"
        files = get_all_uncommitted_files()
        print(f"\n=== Found {len(files)} {title} ===\n")
        if files:
            for f in files: print(f)
        else:
            print("No files found.")
            
    elif choice == '4':
        soft_delete_last_commit()
        
    elif choice == '5':
        hard_delete_last_commit()
        
    elif choice == '6':
        print_recent_commits()
        
    elif choice == '7':
        amend_last_commit()

    elif choice == '8':
        abort_cherry_pick()

    elif choice == '9':
        cherry_pick_changes_only()

    elif choice == '10':
        unstage_all_files()

    elif choice == '11':
        reset_to_commit_snapshot()