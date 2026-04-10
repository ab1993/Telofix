# 🤖 Telofix: Autonomous AI Bug Resolver (Level-1 Developer)

[![License](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg)](http://makeapullrequest.com)

**Telofix** is an enterprise-grade, autonomous AI agent that acts as a "Level-1 Developer." It seamlessly integrates with your project management board (Jira), automatically investigates bug reports, writes code to fix them, verifies the fix against your test suite, and pushes the changes for review.

## 🚀 How It Works

This project uses a dual-stack architecture to separate the secure enterprise gateway from the AI reasoning engine.

1. **The Gateway (Java Spring Boot):** Acts as the secure entry point. It receives webhooks from Jira, manages concurrency, deduplicates requests, and safely spins up the agent in a background thread.
2. **The Agent (Python & LangGraph):** A cyclic reasoning loop powered by GPT-4o. The agent explores your codebase, reads the buggy files, applies a fix, and runs `mvn test`. It loops until the tests pass, then updates Jira with a summary.

## 🛠 Prerequisites

To run Telofix locally, you will need:
* **Java 21+** and **Maven**
* **Python 3.9+**
* An **OpenAI API Key**
* A **Jira Cloud** account (with an API Token)
* A **Git Provider** account (GitHub/Bitbucket/GitLab)

## ⚙️ Quick Start

**1. Clone the repository**
```bash
git clone [https://github.com/YOUR_USERNAME/telofix.git](https://github.com/YOUR_USERNAME/telofix.git)
cd agentic-bug-resolver-tool
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
mvn spring-boot:run
The Spring Boot gateway will start on localhost:8080 and listen for Jira webhooks at /webhook/jira-trigger.
```
## 🎯 Usage (The Jira Flow)
   ##### 1. Ensure Telofix is running.

   ##### 2. Create a Bug ticket in your Jira project and include the stack trace or error logs in the description.

   ##### 3. Drag the ticket into the designated AI-Fix column (which triggers the webhook).

   ##### 4. Watch the Spring Boot console as Telofix automatically finds the files, applies the fix, and runs the Maven tests.

   ##### 5. Telofix will automatically comment on the Jira ticket and open a Pull Request when the tests pass.

## 🤝 Contributing

We welcome contributions from the community! Whether it is adding support for new Git providers, improving the agent's prompts, or fixing bugs, your help is appreciated.

Please see our CONTRIBUTING.md for details on how to set up your dev environment, submit pull requests, and report issues.

## 📄 License
This project is licensed under the Apache License 2.0 - see the  file for details.

