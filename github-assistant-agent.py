#!/usr/bin/env python
# coding: utf-8

# # ✅ Intelligent GitHub Assistant (Demo)

# ## How to Test This Agent:
# 1. **Create a GitHub Personal Access Token:**
#     Go to your GitHub account settings → Developer settings → Personal access tokens → Tokens (classic).
#     Generate a new token with the required permissions (repo access, issues, pull requests, etc.).
# 2. **Create a Google API Personal Access Token:**
# 3. **Set the Tokens in Your Secret key**
# 4. **Run the Agent Using Default Prompts:**
#     Use the pre-defined prompts to interact with the agent, such as listing issues, creating branches, or opening pull requests.
#     The agent will automatically use the tools provided to perform actions on your repository.
# 
# 
# 

# In[1]:


# Install required libraries 
# ============================================
get_ipython().system('pip install PyGithub')
get_ipython().system('pip install google-adk kaggle_secrets requests')
get_ipython().system('pip install google-adk --upgrade')
get_ipython().system('pip install nest_asyncio')
get_ipython().system('pip install aiosqlite')



# In[2]:


# ============================================
# GitHub Assistant Project
# Based on Google's Agent Development Kit (ADK)
# Enhanced with GitHub API Integration
# ============================================

# 1. Project Setup and Configuration
# ============================================
import os
import random
import uuid
import json
import requests
import asyncio
import logging
from github import Auth
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from IPython.display import HTML, display
import nest_asyncio
from functools import wraps

# Kaggle and ADK imports
from kaggle_secrets import UserSecretsClient
from google.adk.agents import Agent, LlmAgent, SequentialAgent, ParallelAgent
from google.adk.models.google_llm import Gemini
from google.adk.sessions import InMemorySessionService
from google.adk.runners import Runner, InMemoryRunner
from google.adk.tools import AgentTool, FunctionTool, google_search
from google.adk.tools.tool_context import ToolContext
from google.adk.memory import InMemoryMemoryService
from google.adk.agents import SequentialAgent
from google.adk.apps.app import App, ResumabilityConfig, EventsCompactionConfig
from google.adk.plugins.logging_plugin import LoggingPlugin
from google.genai import types

# GitHub API imports
from github import Github, GithubException

print("✅ All imports completed successfully")


# In[3]:


# ============================================
# 2. Authentication and Configuration
# ============================================
try:
    GOOGLE_API_KEY = UserSecretsClient().get_secret("GOOGLE_API_KEY")
    os.environ["GOOGLE_API_KEY"] = GOOGLE_API_KEY
    print("✅ Gemini API key configured")
except Exception as e:
    print(f"🔑 Gemini API Key Error: {e}")

try:
    GITHUB_TOKEN = UserSecretsClient().get_secret("GITHUB_TOKEN")
    os.environ["GITHUB_TOKEN"] = GITHUB_TOKEN
    print("✅ GitHub token configured")
except Exception as e:
    print("⚠️ GitHub token not found. Please add 'GITHUB_TOKEN' to your Kaggle secrets.")
    GITHUB_TOKEN = "placeholder_token"  # Placeholder

# Retry options for API calls
retry_config = types.HttpRetryOptions(
    attempts=5,
    exp_base=7,
    initial_delay=1,
    http_status_codes=[429, 500, 503, 504]
)

PROJECT_ID = os.environ.get("GOOGLE_CLOUD_PROJECT", "github-assistant-project")
APP_NAME = "GithubAssistant"
USER_ID = "github_user"

print(f"✅ Project configuration complete with PROJECT_ID: {PROJECT_ID}")


# In[4]:


import os
from kaggle_secrets import UserSecretsClient

# تست دریافت کلیدها
try:
    GOOGLE_API_KEY = UserSecretsClient().get_secret("GOOGLE_API_KEY")
    print("GOOGLE_API_KEY Loaded:", bool(GOOGLE_API_KEY))
except Exception as e:
    print("Google API Error:", e)

try:
    GITHUB_TOKEN = UserSecretsClient().get_secret("GITHUB_TOKEN")
    print("GITHUB_TOKEN Loaded:", bool(GITHUB_TOKEN))
except Exception as e:
    print("GitHub Token Error:", e)


# In[5]:


import requests

url = "https://api.github.com/user"
headers = {"Authorization": f"Bearer {GITHUB_TOKEN}"}
r = requests.get(url, headers=headers)

print("Status:", r.status_code)
print("Response:", r.json())


# In[6]:


# ============================================
# 3. Logging and Observability Setup
# ============================================
# حذف فایل لاگ قبلی در صورتی که وجود داشته باشه
for log_file in ["logger.log"]:
    if os.path.exists(log_file):
        os.remove(log_file)

# پیکربندی لاگینگ
output_dir = "/kaggle/working/"
log_file = os.path.join(output_dir, "logger.log")

logging.basicConfig(
    filename=log_file,
    level=logging.DEBUG,
    format="%(asctime)s - %(filename)s:%(lineno)s - %(levelname)s - %(message)s",
)

print("✅ Logging configured for observability")

# اضافه کردن لاگ‌ها با سطوح مختلف
logging.debug("This is a DEBUG message")
logging.info("This is an INFO message")
logging.warning("This is a WARNING message")
logging.error("This is an ERROR message")
logging.critical("This is a CRITICAL message")

print("✅ Test logs generated.")


# In[7]:


# ============================================
# 4. GitHub API Helper Functions (Fixed)
# ============================================

def get_github_client():
    token = os.environ.get("GITHUB_TOKEN")
    if not token:
        print("❌ Token not found.")
        return None
    auth = Auth.Token(token)
    return Github(auth=auth)

def handle_github_error(func):
    @wraps(func)
    def wrapper_func(*args, **kwargs):  # نام داخلی تغییر کرد
        try:
            return func(*args, **kwargs)
        except GithubException as e:
            return {
                "status": "error",
                "message": f"GitHub API Error: {e.data.get('message', str(e))}",
                "status_code": e.status
            }
        except Exception as e:
            return {
                "status": "error",
                "message": f"An unexpected error occurred: {str(e)}"
            }
    return wrapper_func

print("✅ GitHub API helper functions fixed")


# ============================================
# 5. GitHub Issue Management Tools
# ============================================
@handle_github_error
def list_my_repos():
    client = get_github_client()
    if not client:
        return {"status": "error", "message": "Client not available"}

    repos = [repo.name for repo in client.get_user().get_repos()]
    return {"status": "success", "repos": repos}

@handle_github_error
def create_issue(repo_name: str, title: str, body: str, labels: List[str] = None) -> Dict[str, Any]:
    g = get_github_client()
    if not g: return {"status": "error", "message": "GitHub client not available."}
    repo = g.get_repo(repo_name)
    issue = repo.create_issue(title=title, body=body, labels=labels or [])
    return {
        "status": "success",
        "issue_id": issue.number,
        "issue_url": issue.html_url,
        "title": issue.title,
        "labels": [label.name for label in issue.labels],
        "message": f"Successfully created issue #{issue.number} in {repo_name}"
    }

@handle_github_error
def get_issues(repo_name: str, state: str = "open") -> Dict[str, Any]:
    g = get_github_client()
    if not g: return {"status": "error", "message": "GitHub client not available."}
    repo = g.get_repo(repo_name)
    issues_list = [{
        "id": issue.number,
        "title": issue.title,
        "state": issue.state,
        "url": issue.html_url,
        "created_at": issue.created_at.isoformat()
    } for issue in repo.get_issues(state=state)]
    return {
        "status": "success",
        "count": len(issues_list),
        "issues": issues_list,
        "message": f"Found {len(issues_list)} {state} issues in {repo_name}"
    }

@handle_github_error
def close_issue(repo_name: str, issue_number: int) -> Dict[str, Any]:
    g = get_github_client()
    if not g: return {"status": "error", "message": "GitHub client not available."}
    repo = g.get_repo(repo_name)
    issue = repo.get_issue(issue_number)
    issue.edit(state="closed")
    return {
        "status": "success",
        "issue_id": issue.number,
        "message": f"Successfully closed issue #{issue_number} in {repo_name}"
    }

print("✅ GitHub issue management tools fixed")


# ============================================
# 6. GitHub Pull Request Management Tools
# ============================================
@handle_github_error
def create_pull_request(repo_name: str, title: str, head: str, base: str, body: str = "") -> Dict[str, Any]:
    g = get_github_client()
    if not g: return {"status": "error", "message": "GitHub client not available."}
    repo = g.get_repo(repo_name)
    pr = repo.create_pull(title=title, head=head, base=base, body=body)
    return {
        "status": "success",
        "pr_id": pr.number,
        "pr_url": pr.html_url,
        "title": pr.title,
        "message": f"Successfully created pull request #{pr.number} in {repo_name}"
    }

@handle_github_error
def get_pull_requests(repo_name: str, state: str = "open") -> Dict[str, Any]:
    g = get_github_client()
    if not g: return {"status": "error", "message": "GitHub client not available."}
    repo = g.get_repo(repo_name)
    prs_list = [{
        "id": pr.number,
        "title": pr.title,
        "state": pr.state,
        "url": pr.html_url,
        "head": pr.head.ref,
        "base": pr.base.ref,
        "created_at": pr.created_at.isoformat()
    } for pr in repo.get_pulls(state=state)]
    return {
        "status": "success",
        "count": len(prs_list),
        "pull_requests": prs_list,
        "message": f"Found {len(prs_list)} {state} pull requests in {repo_name}"
    }

@handle_github_error
def merge_pull_request(repo_name: str, pr_number: int, commit_message: str = "") -> Dict[str, Any]:
    g = get_github_client()
    if not g: return {"status": "error", "message": "GitHub client not available."}
    repo = g.get_repo(repo_name)
    pr = repo.get_pull(pr_number)
    if not pr.mergeable:
        return {"status": "error", "message": f"Pull request #{pr_number} is not mergeable."}
    result = pr.merge(commit_message=commit_message)
    return {
        "status": "success",
        "pr_id": pr.number,
        "merged_sha": result.sha,
        "message": f"Successfully merged pull request #{pr_number} in {repo_name}"
    }

print("✅ GitHub pull request management tools fixed")


# In[8]:


# ============================================
# 7. GitHub Branch and Commit Management Tools
# ============================================
@handle_github_error
def create_branch(repo_name: str, branch_name: str, from_branch: str = "main") -> Dict[str, Any]:
    """Create a new branch in a GitHub repository."""
    g = get_github_client()
    if not g:
        return {"status": "error", "message": "GitHub client not available."}

    repo = g.get_repo(repo_name)
    source_branch = repo.get_branch(from_branch)
    repo.create_git_ref(ref=f"refs/heads/{branch_name}", sha=source_branch.commit.sha)

    return {
        "status": "success",
        "branch_name": branch_name,
        "from_branch": from_branch,
        "message": f"Successfully created branch '{branch_name}' from '{from_branch}' in {repo_name}"
    }

@handle_github_error
def get_commits(repo_name: str, branch: str = "main", limit: int = 10) -> Dict[str, Any]:
    """Get recent commits from a GitHub repository."""
    g = get_github_client()
    if not g:
        return {"status": "error", "message": "GitHub client not available."}

    repo = g.get_repo(repo_name)
    commits = repo.get_commits(sha=branch)[:limit]

    commits_list = [{
        "sha": commit.sha[:7],
        "message": commit.commit.message,
        "author": commit.commit.author.name,
        "date": commit.commit.author.date.isoformat(),
        "url": commit.html_url
    } for commit in commits]

    return {
        "status": "success",
        "count": len(commits_list),
        "commits": commits_list,
        "message": f"Retrieved {len(commits_list)} commits from '{branch}' in {repo_name}"
    }

print("✅ GitHub branch and commit management tools defined")


# In[9]:


# ============================================
# 8. GitHub User and Collaboration Management Tools 
# ============================================
@handle_github_error
def get_repo_contributors(repo_name: str) -> Dict[str, Any]:
    """Get contributors to a GitHub repository."""
    g = get_github_client()
    if not g:
        return {"status": "error", "message": "GitHub client not available."}

    repo = g.get_repo(repo_name)
    contributors_list = [{
        "login": c.login,
        "contributions": c.contributions,
        "avatar_url": c.avatar_url,
        "html_url": c.html_url
    } for c in repo.get_contributors()]

    return {
        "status": "success",
        "count": len(contributors_list),
        "contributors": contributors_list,
        "message": f"Found {len(contributors_list)} contributors to {repo_name}"
    }

@handle_github_error
def add_collaborator(repo_name: str, username: str, permission: str = "push") -> Dict[str, Any]:
    """Add a collaborator to a GitHub repository."""
    g = get_github_client()
    if not g:
        return {"status": "error", "message": "GitHub client not available."}

    repo = g.get_repo(repo_name)
    repo.add_to_collaborators(username, permission)

    return {
        "status": "success",
        "username": username,
        "permission": permission,
        "message": f"Successfully added '{username}' as a collaborator to {repo_name} with '{permission}' permission."
    }

# *** NEW TOOL: Create Repository ***
@handle_github_error
def create_repository(repo_name: str, description: str = "", is_private: bool = False) -> Dict[str, Any]:
    """یک ریپازیتوری جدید در حساب کاربری GitHub شما ایجاد می‌کند."""
    g = get_github_client()
    if not g:
        return {"status": "error", "message": "GitHub client not available."}

    user = g.get_user()
    repo = user.create_repo(name=repo_name, description=description, private=is_private)

    return {
        "status": "success",
        "repo_name": repo.full_name,
        "repo_url": repo.html_url,
        "private": repo.private,
        "message": f"موفقیت‌آمیز! ریپازیتوری '{repo_name}' ساخته شد."
    }

print("✅ GitHub user and collaboration management tools defined (including repo creation)")



# In[10]:


# ======= GitHub Client =======
g = get_github_client()
if not g:
    raise Exception("GitHub client not available")

repo_name = "ZeynabR199/GitHub_Test_Repo"
repo = g.get_repo(repo_name)

# شاخه و فایل برای تست
base_branch = repo.default_branch
new_branch = "feature/test-pr"
file_path = "example_file.txt"
file_content = "Hello from test branch!"


# In[11]:


# ایجاد Issue
res = create_issue("ZeynabR199/GitHub_Test_Repo", "Test Issue", "This is a test issue")
print(res)

# دریافت Issue ها
res = get_issues("ZeynabR199/GitHub_Test_Repo")
print(res)

# بستن Issue همان ریپو
if res["issues"]:
    issue_number = res["issues"][0]["id"]  # یا "number" بسته به ساختار
    res_close = close_issue("ZeynabR199/GitHub_Test_Repo", issue_number)
    print(res_close)


# In[12]:


# بررسی شاخه
existing_branches = [b.name for b in repo.get_branches()]
if new_branch not in existing_branches:
    create_branch(repo_name, new_branch, from_branch=base_branch)
    print(f"✅ Branch '{new_branch}' created")
else:
    print(f"ℹ️ Branch '{new_branch}' already exists")

# بررسی فایل
try:
    repo.get_contents(file_path, ref=new_branch)
    print(f"ℹ️ File '{file_path}' already exists on branch '{new_branch}'")
except GithubException:
    repo.create_file(path=file_path, message="Add example_file.txt", content=file_content, branch=new_branch)
    print(f"✅ File '{file_path}' added to branch '{new_branch}'")

# دریافت commit ها
commits_res = get_commits(repo_name, branch=new_branch, limit=5)
print("Commits in branch:", commits_res)


# In[13]:


# ============================================
# 9. GitHub Analytics and Reporting Tools
# ============================================
@handle_github_error
def generate_repo_activity_report(repo_name: str, days: int = 30) -> Dict[str, Any]:
    """Generate a high-level activity report for a GitHub repository."""
    g = get_github_client()
    if not g:
        return {"status": "error", "message": "GitHub client not available."}

    repo = g.get_repo(repo_name)
    cutoff_date = datetime.now() - timedelta(days=days)

    open_issues = sum(1 for i in repo.get_issues(state="open") if i.created_at > cutoff_date)
    closed_issues = sum(1 for i in repo.get_issues(state="closed") if i.closed_at and i.closed_at > cutoff_date)
    merged_prs = sum(1 for pr in repo.get_pulls(state="closed") if pr.merged and pr.merged_at and pr.merged_at > cutoff_date)
    recent_commits = [c for c in repo.get_commits() if c.commit.author.date > cutoff_date]

    return {
        "status": "success",
        "repo_name": repo_name,
        "period_days": days,
        "summary": {
            "stars": repo.stargazers_count,
            "forks": repo.forks_count,
            "open_issues_count": repo.open_issues_count
        },
        "activity": {
            "recent_commits": len(recent_commits),
            "issues_opened": open_issues,
            "issues_closed": closed_issues,
            "prs_merged": merged_prs
        },
        "message": f"Generated activity report for {repo_name} over the last {days} days."
    }

print("✅ GitHub analytics and reporting tools defined")



# In[14]:


# ============================================
# 9.  Create File in repo Tools
# ============================================
@handle_github_error
def create_file_in_repo(repo_name: str, file_path: str, file_content: str, branch: str, commit_message: str) -> Dict[str, Any]:
    """ایجاد یا به‌روزرسانی یک فایل در یک شاخه مشخص."""
    g = get_github_client()
    if not g:
        return {"status": "error", "message": "GitHub client not available."}

    repo = g.get_repo(repo_name)
    try:
        # بررسی اینکه آیا فایل از قبل وجود دارد
        file = repo.get_contents(file_path, ref=branch)
        # اگر وجود داشت، آن را آپدیت کن
        repo.update_file(path=file_path, message=commit_message, content=file_content, sha=file.sha, branch=branch)
        action = "updated"
    except GithubException as e:
        if e.status == 404: # فایل وجود ندارد
            # فایل را ایجاد کن
            repo.create_file(path=file_path, message=commit_message, content=file_content, branch=branch)
            action = "created"
        else:
            raise e # خطای دیگر را برگردان

    return {
        "status": "success",
        "repo_name": repo_name,
        "file_path": file_path,
        "branch": branch,
        "action": action,
        "message": f"Successfully {action} file '{file_path}' in branch '{branch}' of {repo_name}"
    }

print("✅ GitHub Create_File_in_repo_Tools defined")


# In[15]:


# # ============================================
# # Specialized GitHub Agents ##
# # ============================================

issue_agent = LlmAgent(
    name="issue_agent",
    model=Gemini(model="gemini-2.5-flash-lite", retry_options=retry_config),
    instruction="""
You manage GitHub issues. 
Use only the tools provided to list, create, or close issues.
""",
    tools=[create_issue, get_issues, close_issue]
)


pr_agent = LlmAgent(
    name="pr_agent",
    model=Gemini(model="gemini-2.5-flash-lite", retry_options=retry_config),
    instruction="You manage pull requests using the available tools.",
    tools=[create_pull_request, get_pull_requests, merge_pull_request]
)

branch_commit_agent = LlmAgent(
    name="branch_commit_agent",
    model=Gemini(model="gemini-2.5-flash-lite", retry_options=retry_config),
    instruction="You manage branches & commits using the available tools.",
    tools=[create_branch, get_commits]
)

user_collab_agent = LlmAgent(
    name="user_collab_agent",
    model=Gemini(model="gemini-2.5-flash-lite", retry_options=retry_config),
    instruction="You manage contributors & collaboration using the provided tools.",
    tools=[get_repo_contributors, add_collaborator]
)

analytics_agent = LlmAgent(
    name="analytics_agent",
    model=Gemini(model="gemini-2.5-flash-lite", retry_options=retry_config),
    instruction="You generate repository activity analytics using the available tools.",
    tools=[generate_repo_activity_report]
)

repo_management_agent = LlmAgent(
    name="repo_management_agent",
    model=Gemini(model="gemini-2.5-flash-lite", retry_options=retry_config),
    instruction="You create new repositories using the provided tools.",
    tools=[create_repository]
)


# # =============================================
# # Workflow Sub-Agents
# # =============================================

branch_agent_for_workflow = LlmAgent(
    name="branch_workflow_agent",
    model=Gemini(model="gemini-2.5-flash-lite", retry_options=retry_config),
    instruction="Create a branch using create_branch tool.",
    tools=[create_branch]
)

file_agent_for_workflow = LlmAgent(
    name="file_workflow_agent",
    model=Gemini(model="gemini-2.5-flash-lite", retry_options=retry_config),
    instruction="Create a file in the repository using create_file_in_repo tool.",
    tools=[create_file_in_repo]
)

pr_agent_for_workflow = LlmAgent(
    name="pr_workflow_agent",
    model=Gemini(model="gemini-2.5-flash-lite", retry_options=retry_config),
    instruction="Create a pull request from branch to main.",
    tools=[create_pull_request]
)



# # ===========================================
# # Sequential Agent
# # ===========================================


feature_development_agent = SequentialAgent(
    name="feature_development_agent",
    sub_agents=[
        branch_agent_for_workflow,  # Step 1: Create branch
        file_agent_for_workflow,    # Step 2: Create file
        pr_agent_for_workflow       # Step 3: Create PR
    ]
)


# # ============================================
# # Root Coordinator Agent
# # ============================================

issue_tool = AgentTool(agent=issue_agent)
pr_tool = AgentTool(agent=pr_agent)
branch_tool = AgentTool(agent=branch_commit_agent)
user_tool = AgentTool(agent=user_collab_agent)
analytics_tool = AgentTool(agent=analytics_agent)
repo_tool = AgentTool(agent=repo_management_agent)
feature_development_tool = AgentTool(agent=feature_development_agent)


github_assistant_agent = LlmAgent(
    name="GithubAssistant",
    model=Gemini(model="gemini-2.5-flash-lite", retry_options=retry_config),
    instruction="""
    You are a GitHub Assistant. You can manage the repository using the available tools.
    Capabilities:
    1. Issues: List, create, close, or read issues.
    2. Pull Requests: Create, list, and merge pull requests.
    3. Branches & Commits: Create branches, view commits, and manage commits.
    4. Contributors: List contributors, add collaborators.
    5. Analytics: Generate repository activity reports.
    6. Repositories: Create new repositories if needed.
    7. Feature Development: Create a complete feature workflow (branch, file, PR).

    Rules:
    - Always use the provided tools for each task.
    - Provide clear, step-by-step responses when asked to perform multiple actions.
    - Pass relevant data (branch names, repo name, PR info, etc.) between tools if needed.
    - If a requested action cannot be performed, respond clearly explaining why.
    """,
    tools=[issue_tool, pr_tool, branch_tool, user_tool, analytics_tool, repo_tool, feature_development_tool]
)

# ============================================
# App Configuration
# ============================================
github_app = App(
    name="GithubAssistant",
    root_agent=github_assistant_agent,
    events_compaction_config=  None           #EventsCompactionConfig(
    #     compaction_interval=5,
    #     overlap_size=1
    # )
)

print("✅ Fixed Agents and App defined.")


# In[16]:


from google.adk.sessions import DatabaseSessionService

db_path = "/kaggle/working/github_assistant_data.db"
db_url = f"sqlite+aiosqlite:///{db_path}"
session_service = DatabaseSessionService(db_url=db_url)


# In[17]:


async def run_session(runner_instance: Runner, user_queries: List[str] | str, session_id: str):
    print(f"\n ### Session: {session_id}")

    try:
        session = await session_service.create_session(
            app_name=APP_NAME, user_id=USER_ID, session_id=session_id
        )
    except Exception:
        session = await session_service.get_session(
            app_name=APP_NAME, user_id=USER_ID, session_id=session_id
        )

    if isinstance(user_queries, str):
        user_queries = [user_queries]

    for query in user_queries:
        print(f"\nUser > {query}")
        query_content = types.Content(role="user", parts=[types.Part(text=query)])
        response_text = ""
        async for event in runner_instance.run_async(
            user_id=USER_ID, session_id=session.id, new_message=query_content
        ):
            if event.content and event.content.parts:
                if event.content.parts[0].text:
                    response_text = event.content.parts[0].text
        print(f"Assistant > {response_text}")

print("✅ Session runner function defined.")


# ## DEFAULT_GITHUB_PROMPT = """
# You are GithubAssistant, a helpful agent for managing GitHub repositories.
# 
# You can:
# 1. List, create, or close issues.
#    Example: "List all issues in repository 'MyRepo'."
#    Example: "Create a new issue titled 'Bug in login' in repository 'MyRepo'."
#    Example: "Close issue #12 in repository 'MyRepo'."
# 
# 2. Create a new feature (branch + file + pull request) using the feature development workflow.
#    Example: "Create a feature 'dark-mode' in repository 'MyRepo' with file 'dark_mode.py' containing 'print(\"Hello Dark Mode\")' and create a pull request to main."
#    
# 3. (Optional) Ask for repo analytics, contributors, or add collaborators if needed.
# 
# Instructions for the user:
# - Always specify the repository name.
# - For features, specify branch name, file name, and content.
# - For issues, specify title and optionally description and labels.
# - You can combine multiple commands, but be explicit.
# 
# Now, answer the user's query based on these capabilities.
# """
# 

# In[18]:


# Create the Runner
runner = Runner(app=github_app, session_service=session_service)

# Test queries
test_queries = [
    "List all issues in the repository 'ZeynabR199/GitHub_Test_Repo'.",
    "Create a new branch 'feature/test_branch' in 'ZeynabR199/GitHub_Test_Repo'.",
    "Add a new file 'hello.txt' with content 'Hello World!' in the branch 'feature/test_branch'.",
    "Create a pull request from 'feature/test_branch' to 'main' in 'ZeynabR199/GitHub_Test_Repo'."
]

await run_session(runner, test_queries, "github_demo_session")



# In[ ]:


# 1.4: Helper functions
from IPython.core.display import display, HTML
from jupyter_server.serverapp import list_running_servers

def get_adk_proxy_url():
    PROXY_HOST = "https://kkb-production.jupyter-proxy.kaggle.net"
    ADK_PORT = "8000"

    servers = list(list_running_servers())
    if not servers:
        raise Exception("No running Jupyter servers found.")

    baseURL = servers[0]["base_url"]

    try:
        path_parts = baseURL.split("/")
        kernel = path_parts[2]
        token = path_parts[3]
    except IndexError:
        raise Exception(f"Could not parse kernel/token from base URL: {baseURL}")

    url_prefix = f"/k/{kernel}/{token}/proxy/proxy/{ADK_PORT}"
    url = f"{PROXY_HOST}{url_prefix}"

    styled_html = f"""
    <div style="padding: 15px; border: 2px solid #f0ad4e; border-radius: 8px; background-color: #fef9f0; margin: 20px 0;">
        <div style="font-family: sans-serif; margin-bottom: 12px; color: #333; font-size: 1.1em;">
            <strong>⚠️ IMPORTANT: Action Required</strong>
        </div>
        <div style="font-family: sans-serif; margin-bottom: 15px; color: #333; line-height: 1.5;">
            The ADK web UI is <strong>not running yet</strong>. You must start it in the next cell.
            <ol style="margin-top: 10px; padding-left: 20px;">
                <li style="margin-bottom: 5px;"><strong>Run the next cell</strong> (the one with <code>!adk web ...</code>) to start the ADK web UI.</li>
                <li style="margin-bottom: 5px;">Wait for that cell to show it is "Running" (it will not "complete").</li>
                <li>Once it's running, <strong>return to this button</strong> and click it to open the UI.</li>
            </ol>
            <em style="font-size: 0.9em; color: #555;">(If you click the button before running the next cell, you will get a 500 error.)</em>
        </div>
        <a href='{url}' target='_blank' style="
            display: inline-block; background-color: #1a73e8; color: white; padding: 10px 20px;
            text-decoration: none; border-radius: 25px; font-family: sans-serif; font-weight: 500;
            box-shadow: 0 2px 5px rgba(0,0,0,0.2); transition: all 0.2s ease;">
            Open ADK Web UI (after running cell below) ↗
        </a>
    </div>
    """
    display(HTML(styled_html))
    return url_prefix

print("✅ Helper functions defined.")


# In[ ]:


# 1. ADK Web URL
url_prefix = get_adk_proxy_url()

# 2. Run ADK Web UI
get_ipython().system('adk web --url_prefix {url_prefix} --app GithubAssistant')

