#!/usr/bin/env python3
"""
Development Environment Setup Script
Installs and configures direnv, pyenv, and uv for automatic environment management
"""

import os
import subprocess
import sys
import platform
from pathlib import Path

def install_direnv():
    """Install and configure direnv for automatic .env loading"""
    print("🔧 Setting up direnv for automatic .env loading...")

    try:
        # Install direnv
        if platform.system() == "Linux":
            subprocess.run(["sudo", "apt-get", "update"], check=True)
            subprocess.run(["sudo", "apt-get", "install", "-y", "direnv"], check=True)
        elif platform.system() == "Darwin":  # macOS
            subprocess.run(["brew", "install", "direnv"], check=True)
        else:
            print("⚠️ Unsupported platform for automatic direnv installation")
            return False

        # Add direnv hook to shell
        shell_config = os.path.expanduser("~/.bashrc")
        direnv_hook = '\n# Direnv setup\neval "$(direnv hook bash)"\n'

        with open(shell_config, 'a') as f:
            f.write(direnv_hook)

        print("✅ direnv installed and configured")
        return True

    except Exception as e:
        print(f"❌ Failed to install direnv: {e}")
        return False

def install_pyenv():
    """Install and configure pyenv for Python version management"""
    print("🐍 Setting up pyenv for Python version management...")

    try:
        # Install pyenv dependencies
        if platform.system() == "Linux":
            subprocess.run([
                "sudo", "apt-get", "install", "-y",
                "make", "build-essential", "libssl-dev", "zlib1g-dev",
                "libbz2-dev", "libreadline-dev", "libsqlite3-dev", "wget", "curl", "llvm",
                "libncurses5-dev", "libncursesw5-dev", "xz-utils", "tk-dev", "libffi-dev", "liblzma-dev"
            ], check=True)
        elif platform.system() == "Darwin":
            subprocess.run(["brew", "install", "pyenv"], check=True)

        # Install pyenv
        subprocess.run([
            "curl", "https://pyenv.run", "|", "bash"
        ], shell=True, check=True)

        # Add pyenv to shell
        shell_config = os.path.expanduser("~/.bashrc")
        pyenv_config = '''
# Pyenv setup
export PYENV_ROOT="$HOME/.pyenv"
export PATH="$PYENV_ROOT/bin:$PATH"
eval "$(pyenv init --path)"
eval "$(pyenv virtualenv-init -)"
'''

        with open(shell_config, 'a') as f:
            f.write(pyenv_config)

        print("✅ pyenv installed and configured")
        return True

    except Exception as e:
        print(f"❌ Failed to install pyenv: {e}")
        return False

def install_uv():
    """Install uv as the Python package manager"""
    print("📦 Setting up uv as Python package manager...")

    try:
        # Install uv
        subprocess.run([
            "curl", "-LsSf", "https://astral.sh/uv/install.sh", "|", "sh"
        ], shell=True, check=True)

        # Add uv to PATH
        shell_config = os.path.expanduser("~/.bashrc")
        uv_config = '''
# UV setup
export PATH="$HOME/.cargo/bin:$PATH"
'''

        with open(shell_config, 'a') as f:
            f.write(uv_config)

        print("✅ uv installed and configured")
        return True

    except Exception as e:
        print(f"❌ Failed to install uv: {e}")
        return False

def setup_project_environment():
    """Configure the OpenDiscourse project for automatic environment activation"""
    print("📁 Configuring OpenDiscourse project environment...")

    try:
        project_root = "/home/cbwinslow/Videos/opendiscourse"

        # Create .envrc file for direnv
        envrc_content = '''
# Direnv configuration for OpenDiscourse
# Automatically load .env file and activate virtual environment

export $(grep -v '^#' .env | xargs)

# Check if virtual environment exists, create if not
if [ ! -d ".venv" ]; then
    echo "📦 Creating virtual environment..."
    python -m venv .venv
fi

# Activate virtual environment
if [ -f ".venv/bin/activate" ]; then
    echo "🔌 Activating virtual environment..."
    source .venv/bin/activate
fi

# Install dependencies if not installed
if [ ! -f ".venv/installed" ]; then
    echo "📥 Installing Python dependencies..."
    if [ -f "requirements.txt" ]; then
        pip install -r requirements.txt
    fi
    touch .venv/installed
fi

echo "✅ OpenDiscourse environment ready!"
'''

        with open(f"{project_root}/.envrc", 'w') as f:
            f.write(envrc_content)

        # Allow direnv to load the .envrc file
        os.chdir(project_root)
        subprocess.run(["direnv", "allow"], check=True)

        print("✅ OpenDiscourse project environment configured")
        return True

    except Exception as e:
        print(f"❌ Failed to configure project environment: {e}")
        return False

def main():
    """Main setup function"""
    print("🚀 OpenDiscourse Development Environment Setup")
    print("=" * 60)
    print("This script will install and configure:")
    print("• direnv - for automatic .env file loading")
    print("• pyenv - for Python version management")
    print("• uv - for Python package management")
    print("• Automatic virtual environment activation")
    print()

    # Confirm before proceeding
    response = input("Do you want to proceed with the setup? (yes/no): ")
    if response.lower() != 'yes':
        print("❌ Setup cancelled")
        return

    print("\n📋 Starting installation process...")

    # Install components
    direnv_success = install_direnv()
    pyenv_success = install_pyenv()
    uv_success = install_uv()

    if direnv_success and pyenv_success and uv_success:
        print("\n✅ All components installed successfully!")
        print("📁 Configuring project environment...")

        if setup_project_environment():
            print("\n🎉 Development environment setup complete!")
            print()
            print("📝 Next steps:")
            print("1. Restart your terminal or run: source ~/.bashrc")
            print("2. Navigate to the project: cd /home/cbwinslow/Videos/opendiscourse")
            print("3. direnv will automatically:")
            print("   - Load your .env file with API keys")
            print("   - Activate the virtual environment")
            print("   - Install dependencies if needed")
            print("4. Run your scripts - everything will work automatically!")
        else:
            print("❌ Project configuration failed")
    else:
        print("❌ Some components failed to install")

    print("\n💡 Tip: After setup, you can test by running:")
    print("   cd /home/cbwinslow/Videos/opendiscourse")
    print("   python --version  # Should show your pyenv Python version")
    print("   echo $CONGRESS_API_KEY  # Should show your API key from .env")

if __name__ == "__main__":
    main()
