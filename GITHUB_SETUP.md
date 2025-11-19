# GitHub Setup Guide

This guide will help you set up your project on GitHub.

## Step 1: Create a GitHub Repository

1. Go to [GitHub](https://github.com) and sign in
2. Click the "+" icon in the top right corner
3. Select "New repository"
4. Choose a repository name (e.g., `jira-flask-app`)
5. Choose visibility (Public or Private)
6. **DO NOT** initialize with README, .gitignore, or license (we already have these)
7. Click "Create repository"

## Step 2: Update Git Remote

After creating the repository, GitHub will show you the repository URL. Use one of these commands:

### For HTTPS:
```bash
git remote set-url origin https://github.com/YOUR_USERNAME/YOUR_REPO_NAME.git
```

### For SSH:
```bash
git remote set-url origin git@github.com:YOUR_USERNAME/YOUR_REPO_NAME.git
```

Replace `YOUR_USERNAME` and `YOUR_REPO_NAME` with your actual GitHub username and repository name.

## Step 3: Verify Remote

```bash
git remote -v
```

You should see your GitHub repository URL instead of the localhost one.

## Step 4: Stage and Commit Changes

```bash
# Stage all changes
git add .

# Commit with a descriptive message
git commit -m "Refactor: Restructure Flask app with blueprints and service layer

- Created proper Flask application structure with app/ directory
- Separated routes into blueprints (auth, issues, search, update)
- Moved business logic to services layer
- Added centralized configuration management
- Improved error handling and logging
- Updated Dockerfile and docker-compose.yml
- Added .env.example and improved documentation
- Updated .gitignore with comprehensive patterns"
```

## Step 5: Push to GitHub

```bash
# Push to main branch
git push -u origin main
```

If you encounter authentication issues:
- For HTTPS: You may need to use a Personal Access Token instead of a password
- For SSH: Make sure your SSH key is added to your GitHub account

## Step 6: Verify on GitHub

Visit your repository on GitHub to verify all files are uploaded correctly.

## Optional: Add GitHub Actions

You can add CI/CD workflows later. A basic workflow file would go in `.github/workflows/`.

## Troubleshooting

### If you get "remote origin already exists" error:
```bash
git remote remove origin
git remote add origin YOUR_GITHUB_REPO_URL
```

### If you need to force push (use with caution):
```bash
git push -u origin main --force
```

**Note:** Only use `--force` if you're sure you want to overwrite the remote repository.

