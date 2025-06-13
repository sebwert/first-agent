# scripts/version.py
"""Version management utilities"""
import subprocess
import sys
from pathlib import Path
import toml
import re
from typing import Literal

def get_current_version() -> str:
    """Get current version from pyproject.toml"""
    pyproject_path = Path("pyproject.toml")
    if not pyproject_path.exists():
        print("Error: pyproject.toml not found")
        sys.exit(1)
    
    data = toml.load(pyproject_path)
    return data["project"]["version"]

def bump_version(bump_type: Literal["major", "minor", "patch"]) -> str:
    """Bump version based on type"""
    current = get_current_version()
    major, minor, patch = map(int, current.split("."))
    
    if bump_type == "major":
        major += 1
        minor = 0
        patch = 0
    elif bump_type == "minor":
        minor += 1
        patch = 0
    elif bump_type == "patch":
        patch += 1
    
    new_version = f"{major}.{minor}.{patch}"
    
    # Update pyproject.toml
    pyproject_path = Path("pyproject.toml")
    content = pyproject_path.read_text()
    content = re.sub(
        r'version = "[^"]+"',
        f'version = "{new_version}"',
        content
    )
    pyproject_path.write_text(content)
    
    # Update __init__.py files
    for init_file in Path("src").rglob("__init__.py"):
        if init_file.exists():
            init_content = init_file.read_text()
            if "__version__" in init_content:
                init_content = re.sub(
                    r'__version__ = "[^"]+"',
                    f'__version__ = "{new_version}"',
                    init_content
                )
                init_file.write_text(init_content)
    
    return new_version

def create_git_tag(version: str, message: str = None):
    """Create git tag for version"""
    if not message:
        message = f"Release version {version}"
    
    # Commit changes
    subprocess.run(["git", "add", "-A"])
    subprocess.run(["git", "commit", "-m", f"chore: bump version to {version}"])
    
    # Create tag
    subprocess.run(["git", "tag", "-a", f"v{version}", "-m", message])
    
    print(f"✓ Created tag v{version}")
    print("  Push with: git push origin main --tags")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python scripts/version.py [major|minor|patch]")
        sys.exit(1)
    
    bump_type = sys.argv[1]
    if bump_type not in ["major", "minor", "patch"]:
        print("Error: bump type must be major, minor, or patch")
        sys.exit(1)
    
    current = get_current_version()
    new_version = bump_version(bump_type)
    
    print(f"Bumped version: {current} → {new_version}")
    
    # Optional: create git tag
    if len(sys.argv) > 2 and sys.argv[2] == "--tag":
        create_git_tag(new_version)