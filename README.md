
# 🤖 Intelligent GitHub Assistant (Powered by Google ADK)

An intelligent AI-powered assistant built using the **Google Agent Development Kit (ADK)** and the **Gemini 2.5** large language model. This assistant allows you to manage your GitHub repositories simply by sending natural language commands.

This project leverages a **Multi-Agent** architecture, where each agent is responsible for a specific task (such as managing Issues, Pull Requests, or Branches), and a Root Coordinator Agent orchestrates them.

---
## 🏆 Certificate

### 5-Day AI Agents Intensive Course with Google

Completed the **5-Day AI Agents Intensive Course with Google** on Kaggle.


[🎓 View Certificate on Kaggle](https://www.kaggle.com/certification/badges/znbrazi/105)

---

## ✨ Features

- **Issue Management:** Create, list, and close issues.
- **Pull Request Management:** Create, list, and merge PRs.
- **Branch Management:** Create new branches and view commit history.
- **File Management:** Create or update files in specific branches.
- **Collaborator Management:** View repository contributors and add collaborators.
- **Analytics:** Generate repository activity reports for specific timeframes.
- **Automated Feature Workflow:** With a single command, it can create a branch, add a file, and open a Pull Request automatically!

---

## 🏗️ System Architecture

This project uses a hierarchical agent architecture:

1. **Root Agent (`GithubAssistant`):** The main point of contact for the user. It understands the prompt and delegates it to the appropriate agent.
2. **Specialized Agents:** 
   - `issue_agent`
   - `pr_agent`
   - `branch_commit_agent`
   - `user_collab_agent`
   - `analytics_agent`
   - `repo_management_agent`
3. **Sequential Agent:**
   - `feature_development_agent`: A 3-step automated workflow that sequentially executes the `branch_agent` -> `file_agent` -> `pr_agent`.

---

## 🛠️ Prerequisites

- Python 3.9 or higher
- A GitHub Personal Access Token (with `repo` and `user` permissions)
- A Google Gemini API Key

---

## ⚙️ Installation & Setup

### 1. Clone the Repository
```bash
git clone https://github.com/YOUR_USERNAME/github-assistant-agent.git
cd github-assistant-agent
```

### 2. Install Dependencies
```bash
pip install PyGithub google-adk requests nest_asyncio aiosqlite python-dotenv
```

### 3. Configure API Keys
**If running on Kaggle:**
Add `GOOGLE_API_KEY` and `GITHUB_TOKEN` to the Kaggle Secrets section.

**If running locally:**
1. Create a `.env` file in the root directory of the project.
2. Add your keys to the file:
```env
GOOGLE_API_KEY=your_google_api_key_here
GITHUB_TOKEN=ghp_your_github_token_here
```
*(Note: To run locally, you will need to modify the `kaggle_secrets` lines in the script to use `dotenv` or `os.environ` instead).*

---

## 🚀 Usage

You can run the code in a Jupyter or Kaggle Notebook. After executing the cells for setup and agent definition, you can interact with the assistant using the `run_session` function.

### Example Prompts:

**Issue Management:**
> "List all issues in the repository 'username/my-repo'."
> "Create a new issue titled 'Bug in login page' in 'username/my-repo'."

**Feature Development (Full Workflow):**
> "Create a feature 'dark-mode' in repository 'username/my-repo' with file 'dark_mode.py' containing 'print(\"Hello Dark Mode\")' and create a pull request to main."

**Analytics:**
> "Generate an activity report for the last 30 days for 'username/my-repo'."

---

## 🌐 Web UI Interface (Optional - Kaggle Only)

If you are running this code in a Kaggle Notebook, you can launch the ADK Web UI at the end of the notebook for a graphical chat interface with the assistant:

```python
!adk web --url_prefix {url_prefix} --app GithubAssistant
```
*(The code to extract the `url_prefix` is included at the end of the main script).*

---

## 📁 Project Structure
```
.
├── github-assistant-agent.py   # Core Python script containing Agents and Tools
├── logger.log                  # System logs (generated upon execution)
├── github_assistant_data.db    # SQLite database for user session management
└── README.md                   # Project documentation
```

## 📝 Technical Notes
- The model used for all agents is `gemini-2.5-flash-lite` to ensure high response speed and cost-efficiency.
- The system includes a built-in retry mechanism to handle Google API rate limits (429) and server errors (5xx).
- GitHub API errors (such as repository not found or permission issues) are caught by a custom decorator (`handle_github_error`) to prevent the chat stream from crashing.

## 📄 License
This project is licensed under the MIT License.
```