# 🤖 CrewAI Blog Automation System

An intelligent blog automation system powered by CrewAI that generates high-quality Spanish content for SMBs (PyMEs), validates content quality, and automatically deploys to your blog with Git and Slack integration.

## ✨ Features

- 🧠 **AI-Powered Content Creation**: Research Agent + Writer Agent + QA Agent
- 🔍 **Strict Content Validation**: JSON format, content quality, and technical validation
- 🚀 **Automated Deployment**: Adds to blog collection and cleans up individual files
- 📦 **Git Integration**: Automatic commits with `[blog-bot]` prefix and push to repository
- 💬 **Slack Notifications**: Success/error reporting to designated Slack channel
- 🌐 **Spanish Content**: Specialized for PyME (Small/Medium Business) audience
- 🛡️ **Error Protection**: Files preserved for debugging instead of deletion

## 📋 Prerequisites

- Python 3.8+
- Git repository
- OpenAI API key
- Serper.dev API key (for web search)
- Slack workspace with bot permissions
- GitHub repository (optional, for remote storage)

## 🚀 Quick Start

### 1. Clone and Install

```bash
git clone <your-repo>
cd crewai-agentes
pip install -r requirements.txt
```

### 2. Environment Configuration

Create a `.env` file in the project root:

```env
# API Keys
OPENAI_API_KEY=sk-proj-your-openai-key-here
SERPER_API_KEY=your-serper-dev-key-here

# Git Configuration (optional for remote push)
GITHUB_TOKEN=ghp_your-github-token-here

# Slack Configuration
SLACK_BOT_TOKEN=xoxb-your-slack-bot-token-here
SLACK_CHANNEL=blog-posts

# Blog Configuration (optional, defaults shown)
REPO_PATH=
BLOG_POSTS_FILE=
```

### 3. Slack Bot Setup

#### Step 1: Create Slack App
1. Go to [https://api.slack.com/apps](https://api.slack.com/apps)
2. Click "Create New App" → "From scratch"
3. Name your app (e.g., "Blog Automation") and select your workspace

#### Step 2: Configure Bot Permissions
In your Slack app settings, go to **"OAuth & Permissions"** → **"Bot Token Scopes"** and add:

**Required Scopes:**
- `chat:write` - Send messages
- `channels:read` - View basic info about public channels
- `groups:read` - View basic info about private channels  
- `groups:write` - Manage private channels the bot is added to
- `incoming-webhook` - Post messages to specific channels
- `im:write` - Send messages to direct messages

#### Step 3: Install App and Get Token
1. Go to **"OAuth & Permissions"** → **"Install to Workspace"**
2. Copy the **"Bot User OAuth Token"** (starts with `xoxb-`)
3. Add this token to your `.env` file as `SLACK_BOT_TOKEN`

#### Step 4: Invite Bot to Channel
1. Create or go to your target channel (e.g., `#blog-posts`)
2. **CRITICAL**: Invite the bot user to the channel:
   ```
   /invite @your-bot-name
   ```

### 4. Git Repository Setup

#### Local Repository
```bash
git init
git add .
git commit -m "Initial commit"
```

#### Remote Repository (Optional)
```bash
git remote add origin https://github.com/your-username/your-repo.git
git push -u origin main
```

**For automatic push to work, update the remote name in the code or rename your remote:**
```bash
git remote rename origin blog-poster
```

## 🏃‍♂️ Running the System

### Basic Execution
```bash
python blog_automation.py
```

### Expected Output
```
🤖 Blog Automation System powered by CrewAI
==================================================
🚀 Iniciando automatización de blog post...

✅ TODAS LAS VALIDACIONES PASARON - Procediendo con commit...
✅ Blog post deployed to blog_posts.json, individual file cleaned up
✅ Successfully committed and pushed: [blog-bot] Add new blog post...
✅ Notificación de éxito enviada a Slack canal #blog-posts

📊 Resultado: success
💬 Mensaje: Blog post validado, creado y deployeado correctamente
```

### Slack Notification
You'll receive a clean notification in your Slack channel:
```
🎉 NUEVO BLOG POST PUBLICADO - 20/07/2025
📰 Título: La revolución de la IA generativa en las PyMEs de América Latina
🔗 Link: wrappers.es/blog/la-revolucion-de-la-ia-generativa-en-las-pymes-de-america-latina
📝 Resumen: La IA generativa está transformando la forma en que las pequeñas y medianas empresas operan en América Latina...
```

### Available Tests
- `tests/test_system.py`
- `tests/test_websearch.py`
- `tests/test_websearch_descriptions.py`

## 📁 File Structure

```
crewai-agentes/
├── .env                       # Environment variables (create this)
├── blog_automation.py          # Main system file
├── blog_posts.json            # Generated blog collection
├── README.md                  # This file
├── requirements.txt            # Python dependencies
└── tests/                      # Available tests
```

## ⚙️ Configuration Details

### Agent Roles
- **Research Agent**: Finds trending AI topics relevant to SMBs
- **Writer Agent**: Creates Spanish content optimized for PyME audience  
- **QA Agent**: Validates JSON format, content quality, and technical requirements
- **DevOps Agent**: Handles deployment, Git operations, and Slack notifications

### Content Validation
The system performs strict validation including:
- ✅ JSON format and syntax
- ✅ Required fields (title, date, author, readTime, summary, coverImage, slug, content)
- ✅ Date format (DD/MM/YYYY)
- ✅ ReadTime format ("X MIN")
- ✅ URL-friendly slug
- ✅ CoverImage path matching slug
- ✅ No placeholder text
- ✅ Spanish sentence case for titles

### Git Workflow
- Commits only `blog_posts.json` (individual files are cleaned up)
- Automatic `[blog-bot]` prefix for all commit messages
- Pushes to configured remote repository

## 🔧 Troubleshooting

### Common Issues

#### "Channel not found" Slack Error
- **Solution**: Ensure bot is invited to channel with `/invite @bot-name`
- **Check**: Bot appears in channel member list, not just integrations

#### JSON Validation Errors
- **System Protection**: Files are preserved as `DEBUG_filename.json` for inspection
- **Auto-repair**: System attempts to clean control characters automatically

#### Git Push Errors
- **Check**: Remote repository is configured and accessible
- **Verify**: Remote name matches code expectation (`blog-poster`)

#### Missing API Keys
- **Error**: "❌ Faltan variables de entorno"
- **Solution**: Ensure all required keys are in `.env` file

### Debug Mode
The system includes extensive debugging:
- JSON cleaning and validation details
- Slack channel discovery and permissions
- Git operation status and file changes
- File preservation for failed validations

## 🔑 API Key Setup

### OpenAI API Key
1. Visit [https://platform.openai.com/api-keys](https://platform.openai.com/api-keys)
2. Create new secret key
3. Add to `.env` as `OPENAI_API_KEY`

### Serper.dev API Key  
1. Visit [https://serper.dev](https://serper.dev)
2. Sign up and get API key
3. Add to `.env` as `SERPER_API_KEY`

### GitHub Token (Optional)
1. Go to GitHub → Settings → Developer settings → Personal access tokens
2. Generate token with `repo` permissions
3. Add to `.env` as `GITHUB_TOKEN`

## 📝 Customization

### Content Topics
Modify the Research Agent's task description in `blog_automation.py` to focus on different topics or industries.

### Output Format
Adjust the Writer Agent's JSON template to match your blog's schema requirements.

### Validation Rules
Customize `validate_blog_post_strict()` method to add or modify validation criteria.

### Git Behavior
Change remote name, commit message format, or deployment paths in the Git Tool configuration.

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test with your own API keys and Slack workspace
5. Submit a pull request

## 📄 License

This project is open source and available under the [MIT License](LICENSE).

## 🙋‍♂️ Support

If you encounter issues:
1. Check the troubleshooting section above
2. Review the debug output in console logs
3. Inspect preserved debug files for validation errors
4. Verify all API keys and permissions are correctly configured

The system is designed to be robust and provide detailed feedback for debugging any issues. 