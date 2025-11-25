# How to Put Your Project on GitHub (Simple Guide)

Since I've already prepared the code on your computer, you just need to create a "home" for it on the internet (GitHub) and connect them.

## Step 1: Create a GitHub Account
If you don't have one, go to [github.com](https://github.com) and sign up. It's free.

## Step 2: Create a New Repository
1.  Log in to GitHub.
2.  Click the **+** icon in the top-right corner and select **New repository**.
3.  **Repository name**: Type `football-betting-model`.
4.  **Public/Private**: Choose "Public" (anyone can see it) or "Private" (only you can see it).
5.  **Important**: Do **NOT** check any boxes under "Initialize this repository with:". Leave "Add a README file", ".gitignore", and "license" **unchecked**.
6.  Click **Create repository**.

## Step 3: Connect Your Code
You will see a page with some code commands. Look for the section titled **"…or push an existing repository from the command line"**.

It will look like this (but with your username):
```bash
git remote add origin https://github.com/YOUR_USERNAME/football-betting-model.git
git branch -M main
git push -u origin main
```

## Step 4: Run the Commands
1.  Copy those 3 lines of code from the GitHub page.
2.  Paste them into your terminal (where you've been running the other commands) and press Enter.

## Success!
If it asks for a username/password, enter your GitHub login details.
Once it finishes, refresh the GitHub page, and you will see all your files there!
