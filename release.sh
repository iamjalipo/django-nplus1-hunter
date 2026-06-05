#!/bin/bash

# Exit on any error
set -e

if [ -z "$1" ]; then
  echo "Usage: ./release.sh <new_version> [commit_message]"
  echo "Example: ./release.sh 1.3.0 \"Add VS Code extension support\""
  exit 1
fi

VERSION=$1
MESSAGE=${2:-"Bump version to $VERSION"}

echo "🚀 Preparing release $VERSION..."

# 1. Update Python package version
echo "📦 Updating Python package version..."
# Works on both GNU and macOS sed with a backup file just in case
sed -i.bak "s/__version__ = .*/__version__ = \"$VERSION\"/" src/django_nplus1_hunter/__init__.py
rm -f src/django_nplus1_hunter/__init__.py.bak

# 2. Update VS Code extension version
echo "🧩 Updating VS Code extension version..."
cd vscode-extension
# Update package.json version without creating a git tag (we'll do that at the root)
npm --no-git-tag-version version $VERSION
cd ..

# 3. Commit and tag
echo "💾 Committing changes..."
git add .
git commit -m "$MESSAGE"

echo "🏷️ Tagging release..."
git tag "v$VERSION"

# 4. Push to GitHub
echo "☁️ Pushing to GitHub..."
git push origin main
git push origin "v$VERSION"

echo ""
echo "✅ Release $VERSION published to GitHub!"
echo "GitHub Actions will now automatically build the .vsix file and attach it to your release!"
