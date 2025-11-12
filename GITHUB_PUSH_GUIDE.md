# GitHub Push Authentication Guide

Since you got a "could not read Username" error, here are your options:

## Option 1: Using Personal Access Token (Recommended)

1. Go to GitHub.com → Settings → Developer settings → Personal access tokens → Tokens (classic)
2. Click "Generate new token (classic)"
3. Give it a name like "FF918-push"
4. Select scopes: at minimum check `repo` (all sub-items)
5. Generate token and COPY IT (you won't see it again!)

Then push with:
```bash
cd /Users/bchippada/Documents/hackathon_new_project
git push https://<your-github-username>:<your-token>@github.com/WarnerBrosDiscovery/FF918.git main
```

## Option 2: Using GitHub CLI

```bash
# Install GitHub CLI
brew install gh

# Authenticate
gh auth login

# Push
git push -u origin main
```

## Option 3: Using SSH

```bash
# Change remote to SSH
git remote set-url origin git@github.com:WarnerBrosDiscovery/FF918.git

# Generate SSH key if you don't have one
ssh-keygen -t ed25519 -C "balaji.chippada@wbd.com"

# Add to GitHub: Settings → SSH and GPG keys → New SSH key
# Copy your public key:
cat ~/.ssh/id_ed25519.pub

# Then push
git push -u origin main
```

## Option 4: Configure Git Credentials

```bash
# Set username
git config --global user.name "your-github-username"

# Use credential helper
git config --global credential.helper osxkeychain

# Then push (it will prompt for username/password)
git push -u origin main




```

For the password, use your Personal Access Token, NOT your GitHub password!
