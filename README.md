# 🤖 Telofix: Autonomous AI Bug Resolver (Level-1 Developer)

[![License](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg)](http://makeapullrequest.com)

**Telofix** is an enterprise-grade, autonomous AI agent that acts as a "Level-1 Developer." It seamlessly integrates with your project management board (Jira), automatically clones the target repository, investigates bug reports, writes code to fix them, verifies the fix against your test suite, and pushes the changes for review.

## 🚀 Architecture

Telofix is a lightweight, purely Python-based microservice:
1. **The Gateway (FastAPI):** A lightning-fast web server that receives webhooks from Jira, manages concurrency, and safely spins up the agent in a background process.
2. **The Agent (LangGraph + GPT-4o):** A cyclic reasoning loop. The agent clones the code into an isolated sandbox, reads the buggy files, applies a fix, and runs tests. It loops until tests pass, then updates Jira.

## 🛠 Prerequisites

* **Python 3.9+**
* An **OpenAI API Key**
* A **Jira Cloud** account
* A **Git Provider** account (GitHub/Bitbucket/GitLab)

## ⚙️ Quick Start

**1. Clone the repository**
```bash
git clone [https://github.com/YOUR_USERNAME/telofix.git](https://github.com/YOUR_USERNAME/telofix.git)
cd telofix

2. Setup the Python Environment
Bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt

3. Configure your Secrets
Copy the template environment file and add your actual API keys. Do not commit your real .env file to version control.
Bash
cp .env.example .env
(Open .env and fill out your OpenAI, Jira, and Git credentials).

4. Start the Application

Bash
python server.py
```
## 🎯 Usage (The Jira Flow)
   ##### Option 1: Jira Webhook (Automated) Map your Jira board transitions to trigger a webhook to http://<your-server>:8080/webhook/jira-trigger. When you drag a ticket to "AI-Fix", Telofix handles the rest.

   ##### Option 2: CLI Mode (Manual)
    Run the agent directly from your terminal for a specific ticket:
    python agent.py SCRUM-123

## 🤝 Contributing

We welcome contributions from the community! Whether it is adding support for new Git providers, improving the agent's prompts, or fixing bugs, your help is appreciated.

Please see our CONTRIBUTING.md for details on how to set up your dev environment, submit pull requests, and report issues.

## 📄 License
This project is licensed under the Apache License 2.0 - see the  file for details.

