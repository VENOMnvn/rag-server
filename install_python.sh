#!/bin/bash

# Exit immediately if a command exits with a non-zero status
set -e

# Install pyenv and Python 3.10
curl https://pyenv.run | bash

# Load pyenv into the shell
export PATH="$HOME/.pyenv/bin:$PATH"
eval "$(pyenv init --path)"
eval "$(pyenv init -)"
eval "$(pyenv virtualenv-init -)"

# Install Python 3.10
pyenv install 3.10.0
pyenv global 3.10.0

# Install dependencies
pip install --upgrade pip
pip install -r requirements.txt

# Continue with the build process
vercel build
