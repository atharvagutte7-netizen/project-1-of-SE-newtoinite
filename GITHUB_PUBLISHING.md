# Publish this project as a public GitHub repository

The repository must be public for the Newtonite submission. Do not commit real customer information, secrets, database files, or personal access tokens.

## Option A — GitHub website + Git

1. Sign in to GitHub and create a **new repository** named `relay-operations-desk`.
2. Set visibility to **Public**. Do not initialize it with a README, `.gitignore`, or license because this project already contains those files.
3. Extract the project zip and open a terminal in the `relay-ops` directory.
4. Run:

```bash
git init
git add .
git status
git commit -m "Build Relay operations coordination MVP"
git branch -M main
git remote add origin https://github.com/YOUR_GITHUB_USERNAME/relay-operations-desk.git
git push -u origin main
```

Replace `YOUR_GITHUB_USERNAME` with your GitHub username. GitHub may ask you to authenticate in your browser or through Git Credential Manager; do not paste access tokens into source files.

5. Open the repository page and confirm the repository is public and the README renders.
6. Include the public repository URL in your submission form.

## Before sharing

- Run `pytest -q` and confirm tests pass.
- Confirm `relay.db`, `.env`, `.venv`, and credentials are not staged. `.gitignore` excludes common local artifacts.
- Check the README run instructions on a clean environment.
- Be ready to explain the concurrency, authorization, and approval tests in a review.