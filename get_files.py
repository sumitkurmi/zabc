import subprocess
import sys

def get_project_files():
    try:
        # Queries Git directly for tracked & untracked files, automatically excluding .gitignore rules
        result = subprocess.run(
            ['git', 'ls-files', '-c', '-o', '--exclude-standard'],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=True
        )
        files = result.stdout.splitlines()
        return sorted(files)
    except subprocess.CalledProcessError as e:
        print(f"Error running git: {e.stderr}")
        sys.exit(1)
    except FileNotFoundError:
        print("Error: Git is not installed or not found in system PATH.")
        sys.exit(1)

if __name__ == '__main__':
    files = get_project_files()
    print(f"=== Found {len(files)} files (Gitignored files excluded) ===\n")
    for f in files:
        print(f)