# Publishing django-nplus1-hunter

This guide walks you through publishing your new package to PyPI (Python Package Index) so anyone in the world can install it via `pip`.

## 1. Prerequisites

Before publishing, you need a PyPI account.
1. Go to [pypi.org](https://pypi.org/) and register for an account if you don't have one.
2. Enable Two-Factor Authentication (2FA) on your PyPI account.

## 2. Set up Trusted Publishing (Recommended)

Since we have already created the GitHub Actions workflow (`.github/workflows/publish.yml`) that uses Trusted Publishing, you do not need to create API tokens. You just need to link your GitHub repository to your PyPI account.

1. Go to your PyPI Account Settings -> Publishing.
2. Scroll down to **"Add a new pending publisher"**.
3. Choose **GitHub**.
4. Fill in the details:
   - **PyPI Project Name**: `django-nplus1-hunter`
   - **Owner**: `iamjalipo` (your GitHub username)
   - **Repository name**: `django-nplus1-hunter`
   - **Workflow name**: `publish.yml`
   - **Environment name**: Leave blank (unless you configured one in GitHub Actions).

Once this is set up, PyPI will trust your GitHub Action to publish versions of this package on your behalf.

## 3. Preparing a Release

Before triggering the publishing action, make sure your code is ready:
1. Ensure all tests pass.
2. Update the `__version__` in `src/django_nplus1_hunter/__init__.py`. Currently it's `0.1.0`.

## 4. Triggering the Publish Action

Our GitHub Action is configured to run automatically whenever you push a tag that starts with `v` (like `v0.1.0`).

Run the following commands in your terminal:

```bash
# Ensure you are on the main branch and up to date
git checkout main
git pull

# Create a new tag
git tag v0.1.0

# Push the tag to GitHub
git push origin v0.1.0
```

## 5. Verify Publication

1. Go to your GitHub repository -> **Actions** tab.
2. You should see a new workflow run triggered by your tag.
3. Once it completes successfully with a green checkmark, go to [pypi.org/project/django-nplus1-hunter/](https://pypi.org/project/django-nplus1-hunter/).
4. Your package is now live!

## Future Updates

When you want to release `0.2.0` or any subsequent version:
1. Update `__version__` in `__init__.py`.
2. Commit your changes: `git commit -am "Bump version to 0.2.0"`
3. Tag it: `git tag v0.2.0`
4. Push the tag: `git push origin v0.2.0`
5. GitHub Actions will handle the rest!
