# Contributing to Telofix

First off, thank you for considering contributing to Telofix! It's people like you that make the open-source community such an amazing place to learn, inspire, and create.

## 🚀 Development Setup

To set up your local environment to contribute to Telofix:

1. **Fork the repository** on GitHub.
2. **Clone your fork** locally:
   `git clone https://github.com/YOUR_USERNAME/telofix.git`
3. **Set up the Python Environment:**
   `python3 -m venv venv`
   `source venv/bin/activate`
   `pip install -r requirements.txt`
4. **Set up the Java Environment:** Ensure you have Java 21+ and Maven installed.
5. **Configure Secrets:** Copy `.env.example` to `.env` and fill in your test credentials.

## 🛠️ How to Contribute

### 1. Find or Create an Issue
Before writing code, please check the existing issues to see if someone is already working on the feature or bug. If not, open a new issue describing what you want to build or fix.

### 2. Create a Branch
Always create a new branch for your work. Use a descriptive naming convention:
* `feature/add-github-support`
* `bugfix/fix-npe-on-startup`
* `docs/update-readme`

### 3. Make your Changes
* Write clean, documented code.
* Ensure your changes don't break the existing Maven test suite.
* (Future) Add unit tests for any new Java or Python logic you introduce.

### 4. Submit a Pull Request
* Push your branch to your fork.
* Open a Pull Request against the `main` branch of the upstream Telofix repository.
* Provide a clear description of the changes and link the PR to the relevant issue.

## 📝 Code of Conduct
By participating in this project, you agree to maintain a respectful and welcoming environment for everyone.