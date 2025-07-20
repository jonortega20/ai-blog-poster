#!/usr/bin/env python3
"""
Blog Automation System using CrewAI
Automatically creates, commits and deploys blog posts weekly
"""

import os
import json
import random
import re
import subprocess
from datetime import datetime
from typing import Dict, Any

from crewai import Agent, Task, Crew
from crewai.tools import BaseTool
import json
import requests
from typing import Type
from pydantic import BaseModel, Field
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class WebSearchInput(BaseModel):
    """Input for web search tool"""
    query: str = Field(default="", description="Search query to find information")
    description: str = Field(default="", description="Alternative field name for search query")

class WebSearchTool(BaseTool):
    """Custom web search tool that doesn't require native compilation"""
    name: str = "web_search"
    description: str = "Search the web for current information and trends. Use this to find recent AI trends and developments."
    args_schema: Type[BaseModel] = WebSearchInput
    
    def _run(self, query: str = "", description: str = "") -> str:
        """Execute web search using Serper.dev API"""
        try:
            # Handle both query and description field names
            search_query = query if query else description
            if not search_query:
                return "Error: No search query provided (neither query nor description field)"
            
            print(f"Debug - WebSearch called with query: '{query}', description: '{description}'")
            print(f"Debug - Using search query: '{search_query}'")
            
            serper_key = os.getenv("SERPER_API_KEY")
            if not serper_key:
                return "Error: SERPER_API_KEY not found in environment variables"
            
            url = "https://google.serper.dev/search"
            headers = {
                "X-API-KEY": serper_key,
                "Content-Type": "application/json"
            }
            payload = {
                "q": search_query,
                "num": 5
            }
            
            response = requests.post(url, headers=headers, json=payload)
            if response.status_code == 200:
                data = response.json()
                results = []
                
                # Debug: Print response structure
                print(f"Debug - API Response keys: {list(data.keys())}")
                
                # Try different possible response structures
                organic_results = data.get("organic", []) or data.get("results", []) or data.get("organic_results", [])
                
                for result in organic_results[:3]:
                    title = result.get("title", "No title")
                    snippet = result.get("snippet", "") or result.get("description", "No description available")
                    link = result.get("link", "")
                    
                    if title and snippet:
                        results.append(f"Title: {title}\nSummary: {snippet}\nSource: {link}\n")
                
                if results:
                    return "\n".join(results)
                else:
                    return f"No results found. Response structure: {list(data.keys())}"
            else:
                return f"Error: Unable to perform search (Status: {response.status_code}) - Response: {response.text[:200]}"
        except Exception as e:
            return f"Error performing web search: {str(e)}"

class FileWriterInput(BaseModel):
    """Input for file writer tool"""
    filename: str = Field(description="Name of the file to write")
    content: str = Field(description="Content to write to the file")

class FileWriterTool(BaseTool):
    """Simple file writer tool"""
    name: str = "file_writer"
    description: str = "Write content to a file"
    args_schema: Type[BaseModel] = FileWriterInput
    
    def _run(self, filename: str, content: str) -> str:
        """Write content to a file with JSON sanitization"""
        try:
            # Si es un archivo JSON, sanitizar y arreglar formato
            if filename.endswith('.json'):
                import json
                import re
                
                print(f"🔧 FileWriter debug - Processing JSON file: {filename}")
                
                # First attempt: try to parse as-is
                try:
                    json.loads(content)
                    print(f"✅ FileWriter debug - JSON is already valid!")
                except json.JSONDecodeError as e:
                    print(f"🚨 FileWriter debug - JSON needs repair: {e}")
                    
                    # Simple and effective approach: find content field and escape newlines
                    try:
                        # Find the content field and properly escape it
                        import re
                        
                        # Pattern to find content field with unescaped newlines
                        content_pattern = r'("content":\s*")(.*?)("(?:\s*\})?$)'
                        
                        def escape_content(match):
                            prefix = match.group(1)
                            content_text = match.group(2)
                            suffix = match.group(3)
                            
                            # Escape newlines, quotes, and other special chars in content
                            escaped_content = (content_text
                                             .replace('\\', '\\\\')  # Escape backslashes first
                                             .replace('"', '\\"')    # Escape quotes
                                             .replace('\n', '\\n')   # Escape newlines
                                             .replace('\r', '\\r')   # Escape carriage returns
                                             .replace('\t', '\\t'))  # Escape tabs
                            
                            return prefix + escaped_content + suffix
                        
                        # Apply the fix
                        content = re.sub(content_pattern, escape_content, content, flags=re.DOTALL)
                        
                        # Ensure proper ending
                        content = content.strip()
                        if not content.endswith('}'):
                            content += '\n}'
                        
                        # Test if it's valid now
                        json.loads(content)
                        print(f"✅ FileWriter debug - JSON successfully repaired with content escaping!")
                        
                    except Exception as e2:
                        print(f"❌ FileWriter debug - Repair failed: {e2}")
                        # Keep original content, validation will catch it
                        pass
            
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(content)
            return f"Successfully wrote content to {filename}"
        except Exception as e:
            return f"Error writing to file: {str(e)}"

class GitCommitInput(BaseModel):
    """Input for git commit tool"""
    message: str = Field(description="Commit message")
    files: str = Field(default="blog_posts.json", description="Files to add (default: blog_posts.json)")

class GitCommitTool(BaseTool):
    """Tool for Git operations with [blog-bot] prefix"""
    name: str = "git_commit"
    description: str = "Add blog_posts.json, commit with [blog-bot] prefix and push to Git repository"
    args_schema: Type[BaseModel] = GitCommitInput
    
    def _run(self, message: str, files: str = "blog_posts.json") -> str:
        """Execute git operations"""
        try:
            # Usar directorio actual
            current_dir = os.getcwd()
            
            # Agregar prefijo [blog-bot] al mensaje
            if not message.startswith("[blog-bot]"):
                message = f"[blog-bot] {message}"
            
            print(f"🔍 Git debug - Working directory: {current_dir}")
            print(f"🔍 Git debug - Files to add: {files}")
            print(f"🔍 Git debug - Commit message: {message}")
            
            # Add files
            result = subprocess.run(["git", "add", files], capture_output=True, text=True, cwd=".")
            if result.returncode != 0:
                return f"Error adding files: {result.stderr}"
            
            # Verificar que hay cambios para commit
            result = subprocess.run(["git", "status", "--porcelain"], capture_output=True, text=True, cwd=".")
            if not result.stdout.strip():
                return "✅ No changes to commit - files already up to date"
            
            print(f"🔍 Git debug - Changes found: {result.stdout.strip()}")
            
            # Commit
            result = subprocess.run(["git", "commit", "-m", message], capture_output=True, text=True, cwd=".")
            if result.returncode != 0:
                error_details = result.stderr.strip() or result.stdout.strip() or "Sin detalles de error"
                print(f"🔍 Git commit debug - stdout: {result.stdout}")
                print(f"🔍 Git commit debug - stderr: {result.stderr}")
                print(f"🔍 Git commit debug - returncode: {result.returncode}")
                return f"Error committing: {error_details}"
            
            # Push
            result = subprocess.run(["git", "push", "blog-poster"], capture_output=True, text=True, cwd=".")
            if result.returncode != 0:
                return f"Error pushing: {result.stderr}"
            
            return f"✅ Successfully committed and pushed: {message}"
        except Exception as e:
            return f"Error in git operations: {str(e)}"

class SlackNotificationInput(BaseModel):
    """Input for Slack notification tool"""
    message: str = Field(description="Message to send to Slack")
    channel: str = Field(default="", description="Channel to send to (optional)")

class SlackNotificationTool(BaseTool):
    """Tool for Slack notifications"""
    name: str = "slack_notification"
    description: str = "Send notification to Slack channel"
    args_schema: Type[BaseModel] = SlackNotificationInput
    
    def _run(self, message: str, channel: str = "") -> str:
        """Send Slack notification"""
        try:
            from slack_sdk import WebClient
            
            slack_token = os.getenv("SLACK_BOT_TOKEN")
            if not slack_token:
                return "❌ SLACK_BOT_TOKEN not configured"
            
            slack_channel = channel or os.getenv("SLACK_CHANNEL", "blog-posts")
            
            # Use the channel ID that we know works from our debug logs
            if slack_channel in ["blog-posts", "#blog-posts"]:
                slack_channel = "C096JQVRXPG"  # Direct channel ID from logs
            elif not slack_channel.startswith('#') and not slack_channel.startswith('C'):
                slack_channel = f"#{slack_channel}"
            
            client = WebClient(token=slack_token)
            
            response = client.chat_postMessage(
                channel=slack_channel,
                text=message,
                username="Blog Automation"
            )
            
            if response.get("ok"):
                return f"✅ Notification sent to {slack_channel}"
            else:
                return f"❌ Slack API error: {response.get('error', 'Unknown error')}"
        except Exception as e:
            return f"Error sending Slack notification: {str(e)}"

class BlogDeploymentInput(BaseModel):
    """Input for blog deployment tool"""
    blog_file: str = Field(description="Path to the blog JSON file")

class BlogDeploymentTool(BaseTool):
    """Tool for deploying blog post to JSON collection and cleanup"""
    name: str = "blog_deployment"
    description: str = "Deploy blog post to blog_posts.json collection and remove individual file"
    args_schema: Type[BaseModel] = BlogDeploymentInput
    
    def _run(self, blog_file: str) -> str:
        """Deploy blog post to current directory"""
        try:
            # Read blog post
            with open(blog_file, 'r', encoding='utf-8') as f:
                blog_data = json.load(f)
            
            # Create a simple blog posts collection in current directory
            blog_collection_file = "blog_posts.json"
            current_dir = os.getcwd()
            
            print(f"🔍 Deploy debug - Working directory: {current_dir}")
            print(f"🔍 Deploy debug - Collection file: {blog_collection_file}")
            
            # Load existing posts or create new collection
            if os.path.exists(blog_collection_file):
                with open(blog_collection_file, 'r', encoding='utf-8') as f:
                    try:
                        existing_posts = json.load(f)
                        if not isinstance(existing_posts, list):
                            existing_posts = []
                    except:
                        existing_posts = []
            else:
                existing_posts = []
            
            # Add new post to collection
            existing_posts.append(blog_data)
            
            # Write updated collection
            with open(blog_collection_file, 'w', encoding='utf-8') as f:
                json.dump(existing_posts, f, indent=2, ensure_ascii=False)
            
            print(f"🔍 Deploy debug - Posts in collection: {len(existing_posts)}")
            
            # Remove individual blog file after adding to collection
            try:
                os.remove(blog_file)
                print(f"🔍 Deploy debug - Removed individual file: {blog_file}")
            except Exception as e:
                print(f"⚠️ Warning: Could not remove individual file {blog_file}: {e}")
            
            return f"✅ Blog post deployed to {blog_collection_file}, individual file cleaned up"
        except Exception as e:
            return f"Error deploying blog post: {str(e)}"

class BlogAutomationCrew:
    """
    CrewAI-based blog automation system for weekly AI content creation
    """
    
    def __init__(self):
        # Initialize tools that agents will use
        self.web_search_tool = WebSearchTool()
        self.file_writer_tool = FileWriterTool()
        self.git_commit_tool = GitCommitTool()
        self.slack_notification_tool = SlackNotificationTool()
        self.blog_deployment_tool = BlogDeploymentTool()
        
        # Blog post template for consistency
        self.blog_template = {
            "label": "IA para tu PyME",
            "title": "",
            "date": "",
            "author": "Jon Ortega", 
            "readTime": "5 MIN",
            "summary": "",
            "coverImage": "/images/blog/", 
            "slug": "",
            "content": ""
        }
    
    def create_research_agent(self) -> Agent:
        """
        Content Research Agent: Busca temas trending en IA relevantes para PyMEs
        
        ¿Por qué este agente?
        - Se especializa SOLO en investigación
        - Tiene acceso a web search para contenido actualizado
        - Su expertise está en identificar qué temas son relevantes para PyMEs
        """
        return Agent(
            role="AI Content Researcher",
                        goal="""Find trending AI topics, developments, and implications that are currently happening in the AI landscape. 
                     Focus on recent advances, new technologies, industry shifts, and emerging trends in artificial intelligence.""",
            backstory="""You are a specialized AI research analyst with deep expertise in artificial intelligence 
                        developments and emerging technologies. You stay current with the latest AI trends, 
                        research breakthroughs, industry developments, and technological implications. You can 
                        identify which AI developments are significant versus just hype, and understand the 
                        broader implications of AI advances across different sectors.""",
            tools=[self.web_search_tool],  # ← ACCESO A INTERNET para investigación actualizada
            verbose=True,
            allow_delegation=False,  # Este agente no delega, se enfoca en su especialidad
            temperature=0.7  # ← CREATIVIDAD MODERADA: suficiente variedad sin inventar
        )
    
    def create_writer_agent(self) -> Agent:
        """
        Blog Writer Agent: Crea contenido siguiendo el formato exacto requerido
        
        ¿Por qué este agente?
        - Especializado en escritura para audiencia PyME
        - Conoce perfectamente el formato JSON requerido
        - Puede acceder a internet para verificar datos y tendencias
        """
        return Agent(
            role="Technical Blog Writer for SMBs",
            goal="""Take general AI trends and developments and adapt them specifically for small and medium 
                    businesses (PyMEs). Write engaging blog posts in Spanish that translate complex AI concepts 
                    into practical, actionable insights for PyME audiences, following the exact JSON format provided.""",
            backstory="""You are an expert technical writer specialized in translating cutting-edge AI developments 
                        into practical business applications for PyMEs (small and medium businesses). You excel at 
                        taking complex AI concepts and explaining their real-world business value. You understand 
                        PyME concerns about cost, complexity, and implementation. You frequently write about AI topics 
                        like contexto, RAG, agentes, wrappers, IA, LLMs, AGI, ASI, and always focus on how these 
                        technologies can specifically benefit small and medium businesses.""",
            tools=[self.web_search_tool, self.file_writer_tool],  # ← ACCESO A INTERNET + escritura
            verbose=True,
            allow_delegation=False,
            temperature=0.7  # ← CREATIVIDAD MODERADA para escritura engaging pero basada en hechos
        )
    
    def create_qa_agent(self) -> Agent:
        """
        Quality Assurance Agent: Valida formato y calidad del contenido
        
        ¿Por qué este agente?
        - Se asegura de que el JSON tenga el formato exacto
        - Valida que el contenido sea apropiado para la audiencia
        - Revisa que no haya errores técnicos
        """
        return Agent(
            role="Content Quality Assurance Specialist",
            goal="""Review and validate blog posts to ensure they meet exact format requirements, 
                    are technically accurate, and provide genuine value to SMB audiences.""",
            backstory="""You are a meticulous quality assurance specialist with expertise in content 
                        validation and JSON format verification. You ensure that all content meets 
                        strict standards for accuracy, format compliance, and audience appropriateness.""",
            tools=[],  # QA agent doesn't need external tools, focuses on validation
            verbose=True,
            allow_delegation=False,
            temperature=0.2  # ← PRECISIÓN ALTA: enfoque en validación exacta, no creatividad
        )
    
    def create_technical_agent(self) -> Agent:
        """
        Technical Agent: Maneja Git, deployment y notificaciones
        
        ¿Por qué este agente?
        - Especializado en operaciones técnicas
        - Maneja la integración con GitHub y Slack
        - Se encarga del deployment automático
        """
        return Agent(
            role="DevOps and Deployment Specialist", 
            goal="""Handle technical operations including Git commits, deployment, and notifications. 
                    Ensure smooth automation of the publishing pipeline.""",
            backstory="""You are a DevOps specialist with expertise in automated deployment pipelines, 
                        Git operations, and integration with communication tools like Slack. You ensure 
                        that the technical aspects of content publishing work flawlessly.""",
            tools=[self.blog_deployment_tool, self.git_commit_tool, self.slack_notification_tool],
            verbose=True,
            allow_delegation=False,
            temperature=0.1  # ← PRECISIÓN MÁXIMA: operaciones técnicas requieren exactitud
        )
    
    def create_research_task(self, agent: Agent) -> Task:
        """
        Tarea de investigación: busca temas trending con VARIEDAD
        """
        import random
        
        # ROTAR TEMAS para evitar repetición
        topic_angles = [
            "Busca las últimas innovaciones en IA que resuelvan problemas específicos de PyMEs.",
            "Investiga tecnologías emergentes como agentes IA, MCP (Model Context Protocol), RAG avanzado, o AI wrappers que permitan a PyMEs competir con grandes empresas sin grandes inversiones",
            "Explora herramientas no-code y automation que transformen emprendedores agotados en CEOs eficientes: Zapier vs Make vs n8n...",
            "Busca soluciones específicas de marketing con IA que generen ROI inmediato: automación de email marketing, lead generation con IA, nuevas funciones de Meta/Google Ads, CRM inteligentes económicos",
            "Investiga cómo PyMEs pueden usar IA para ser más rentables: herramientas de análisis de datos gratuitas, dashboards automáticos, Business Intelligence accesible, métricas que importen",
            "Tendencias de IA generativa para el marketing y las agencias de publicidad digital",
            "Explora tecnologías que solucionen el caos operativo de pequeñas empresas: project management con IA, comunicación interna automática, gestión de equipos remotos, ERP para PyMEs",
            "Investiga tendencias técnicas específicas pero aplicables: integración de APIs, database querying con IA, workflow automation, herramientas de productividad que realmente funcionen para equipos pequeños"
        ]
        
        # Seleccionar ángulo aleatorio
        selected_angle = random.choice(topic_angles)
        
        return Task(
            description=f"""{selected_angle}

                          Return 1 specific trending AI topic with detailed information about:
                          - What the development/trend is
                          - Why it's significant or trending now
                          - Current market context and adoption
                          - Key implications or applications""",
            agent=agent,
            expected_output="""A single trending AI topic relevant to SMBs with:
                              - Topic title
                              - Detailed description (3-4 sentences)
                              - Why it's specifically relevant for PyMEs
                              - Key points to cover in the blog post
                              - Current market context or recent developments"""
        )
    
    def create_writing_task(self, agent: Agent, research_task: Task) -> Task:
        """
        Tarea de escritura: crea el blog post en formato JSON exacto
        """
        current_date = datetime.now().strftime("%d/%m/%Y")
        author = random.choice(["Jon Ortega", "Leire Legarreta", "Elbio Nielsen"])
        readTime = random.choice(["4 MIN", "5 MIN", "6 MIN"])
        
        return Task(
            description=f"""Take the general AI trend/development from the research and adapt it specifically for PyMEs 
                           (small and medium businesses). Write a complete blog post in Spanish that translates this 
                           AI topic into practical business applications, following this EXACT JSON format:
                           
                           {{
                               "label": "IA para tu PyME",
                               "title": "[Compelling title about the chosen topic]",
                               "date": "{current_date}",
                               "author": "{author}",
                               "readTime": "{readTime}",
                               "summary": "[2-3 sentence summary that hooks the reader]",
                               "coverImage": "/images/blog/[slug-based-filename].jpeg",
                               "slug": "[url-friendly-slug]",
                               "content": "[Full blog post content in markdown format]"
                           }}
                           
                           REQUIREMENTS:
                           - Content must be 800-1200 words
                           - Use a conversational but professional tone specifically for PyME audiences
                           - Transform the general AI topic into specific PyME applications and benefits
                           - Speak about how Wrappers.es adresses that problem: we provide long context windows for company files, infinite memory and vertical agents
                           - Address common PyME concerns: cost, complexity, implementation, ROI
                           - Incorporate relevant AI keywords naturally: contexto, RAG, agentes, wrappers, IA, LLMs, agentes verticales, memoria, ventana de contexto, etc.
                           - Use proper markdown formatting in content field
                           - Generate a URL-friendly slug
                           - CRITICAL: coverImage path must be "/images/blog/[slug].jpeg" where [slug] is the exact slug generated
                           - Create an engaging summary that captures the business value for PyMEs
                           - Include engaging questions and call-to-actions throughout content
                           - Use date format DD/MM/YYYY (not DD-MM-YYYY or YYYY-MM-DD)
                           - Focus on practical implementation and real business benefits
                           - NEVER use placeholders like "[Nombre de la Empresa]" or "[sector]" - use specific real company names and sectors
                           
                           SPANISH TITLE FORMATTING:
                           - Titles should use sentence case: "Así se quiere que sean las mayúsculas"
                           - NOT title case like English: "Así No Deben Ser"
                           - Only capitalize first word and proper nouns
                           
                           AUDIENCE: PyME (small/medium business) owners and decision-makers who want to understand 
                           how the latest AI developments can benefit their business. They may be interested in AI 
                           but have concerns about cost, complexity, implementation time, and ROI. They need practical, 
                           actionable information about AI applications that can realistically be implemented in their business.
                           
                           CRITICAL INSTRUCTION: After creating the JSON content, you MUST save it to a file using the file_writer_tool.
                           Use a filename based on the slug: "[slug].json" (e.g., "automatizacion-precios-ia.json")
                           
                           CRITICAL JSON FORMATTING REQUIREMENTS:
                           - ALWAYS end with a complete, valid JSON structure
                           - Ensure all strings are properly escaped and closed with quotes
                           - Use double quotes for JSON strings, not single quotes
                           - Avoid control characters in content (use \\n for line breaks)
                           - MUST end with closing quote for content field and closing brace }}
                           - Verify the JSON is complete before considering the task done""",
            agent=agent,
            context=[research_task],  # ← El agente writer recibe el resultado del research
            expected_output="Complete blog post in valid JSON format saved to a file using the file_writer_tool"
        )
    
    def create_qa_task(self, agent: Agent, writing_task: Task) -> Task:
        """
        Tarea de QA: valida el formato y calidad
        """
        return Task(
            description="""Review the blog post created by the writer and ensure:
                          
                          1. JSON FORMAT VALIDATION:
                             - Valid JSON syntax
                             - All required fields present
                             - Correct field types and values
                             - Date format must be DD/MM/YYYY (e.g., "09/04/2025")
                             - ReadTime format must include "MIN" (e.g., "5 MIN")
                             
                          2. CONTENT QUALITY CHECK:
                             - Content is appropriate for PyME audience
                             - Technical accuracy of AI concepts
                             - Proper Spanish grammar and spelling
                             - Engaging and valuable content
                             - Include call-to-actions or engaging questions for readers
                             
                          3. TECHNICAL VALIDATION:
                             - Slug is URL-friendly (lowercase, hyphens, no spaces)
                             - CRITICAL: Image path must EXACTLY match format: "/images/blog/[slug].jpeg" where [slug] is the exact slug value
                             - Date format is DD/MM/YYYY
                             - Title uses Spanish sentence case (not English title case)
                             - Content must NOT contain placeholder text like "[Nombre de la Empresa]", "[sector]", etc.
                             
                          If any issues are found, provide specific corrections needed.""",
            agent=agent,
            context=[writing_task],
            expected_output="""Either:
                              - "APPROVED: Blog post meets all requirements" 
                              OR
                              - "CORRECTIONS NEEDED:" followed by specific list of issues to fix"""
        )
    
    def create_technical_task(self, agent: Agent, writing_task: Task, blog_file: str) -> Task:
        """
        Tarea técnica: maneja Git commits y Slack notifications
        """
        return Task(
            description=f"""Handle technical operations for blog post deployment:
                          
                          1. DEPLOY BLOG POST:
                             - Deploy the generated JSON blog post '{blog_file}' to blog_posts.json collection
                             - Add new post entry to the collection
                             - Remove individual JSON file after adding to collection (cleanup)
                             - Ensure proper JSON formatting
                          
                          2. GIT OPERATIONS:
                             - Add only blog_posts.json to git (not individual files)
                             - Create commit with "[blog-bot]" prefix + descriptive message
                             - Push changes to repository
                          
                          3. SLACK NOTIFICATION:
                             - Send success notification to Slack channel
                          
                          CRITICAL: Use the exact file path '{blog_file}' for deployment. Only commit blog_posts.json.
                          If any operation fails, report the error and stop execution.""",
            agent=agent,
            context=[writing_task],
            expected_output="Confirmation that blog post has been successfully deployed and notifications sent"
        )
    
    def validate_blog_post_strict(self, blog_content: str, qa_result: str) -> Dict[str, Any]:
        """
        Validaciones CRÍTICAS que deben pasar 100% para proceder con commit
        
        Returns:
        - {"valid": True} si todo perfecto
        - {"valid": False, "errors": [...]} si hay problemas
        """
        errors = []
        
        try:
            # Debug the problematic character
            if len(blog_content) > 688:
                char_at_688 = blog_content[688]
                print(f"🔍 Debug - Character at position 688: '{char_at_688}' (ord: {ord(char_at_688)})")
                
                # Show context around position 688
                start = max(0, 688-20)
                end = min(len(blog_content), 688+20)
                context = blog_content[start:end]
                print(f"🔍 Debug - Context around 688: {repr(context)}")
            
            # More aggressive cleaning
            import re
            # Remove ALL control characters except \n, \r, \t
            cleaned_content = ''.join(char for char in blog_content if ord(char) >= 32 or char in '\n\r\t')
            print(f"🔍 Validation debug - JSON cleaned, original length: {len(blog_content)}, cleaned: {len(cleaned_content)}")
            
            # Parse JSON
            blog_data = json.loads(cleaned_content)
            
            # VALIDACIÓN 1: Campos obligatorios
            required_fields = ["label", "title", "date", "author", "readTime", "summary", "coverImage", "slug", "content"]
            for field in required_fields:
                if field not in blog_data or not blog_data[field]:
                    errors.append(f"❌ Campo obligatorio faltante o vacío: {field}")
            
            if errors:  # Si ya hay errores, no continuar
                return {"valid": False, "errors": errors}
            
            # VALIDACIÓN 2: CoverImage DEBE coincidir exactamente con slug
            expected_cover = f"/images/blog/{blog_data['slug']}.jpeg"
            if blog_data["coverImage"] != expected_cover:
                errors.append(f"❌ CRÍTICO: coverImage '{blog_data['coverImage']}' NO coincide con slug esperado '{expected_cover}'")
            
            # VALIDACIÓN 3: Formato fecha DD/MM/YYYY
            date_pattern = r"^\d{2}/\d{2}/\d{4}$"
            if not re.match(date_pattern, blog_data["date"]):
                errors.append(f"❌ CRÍTICO: Fecha '{blog_data['date']}' no está en formato DD/MM/YYYY")
            
            # VALIDACIÓN 4: ReadTime debe incluir "MIN"
            if "MIN" not in blog_data["readTime"]:
                errors.append(f"❌ CRÍTICO: readTime '{blog_data['readTime']}' debe incluir 'MIN'")
            
            # VALIDACIÓN 5: Slug URL-friendly
            slug_pattern = r"^[a-z0-9-]+$"
            if not re.match(slug_pattern, blog_data["slug"]):
                errors.append(f"❌ CRÍTICO: Slug '{blog_data['slug']}' no es URL-friendly (solo a-z, 0-9, -)")
            
        except json.JSONDecodeError as e:
            errors.append(f"❌ CRÍTICO: JSON inválido - {str(e)}")
        except Exception as e:
            errors.append(f"❌ CRÍTICO: Error de validación - {str(e)}")
        
        result = {"valid": len(errors) == 0, "errors": errors}
        
        # Include cleaned content if successful and different from original
        if result["valid"] and 'cleaned_content' in locals() and cleaned_content != blog_content:
            result["cleaned_content"] = cleaned_content
            
        return result

    def list_slack_channels(self):
        """Lista todos los canales accesibles para el bot"""
        try:
            from slack_sdk import WebClient
            
            slack_token = os.getenv("SLACK_BOT_TOKEN")
            if not slack_token:
                print("❌ SLACK_BOT_TOKEN no configurado")
                return []
                
            client = WebClient(token=slack_token)
            
            print("🔍 Listando canales accesibles para el bot...")
            
            # Listar canales públicos
            public_channels = client.conversations_list(types="public_channel")
            print("📢 Canales públicos:")
            for channel in public_channels["channels"]:
                is_member = channel.get("is_member", False)
                print(f"  - #{channel['name']} (ID: {channel['id']}, member: {is_member})")
            
            # Listar canales privados donde el bot es miembro
            private_channels = client.conversations_list(types="private_channel")
            print("🔒 Canales privados donde soy miembro:")
            for channel in private_channels["channels"]:
                print(f"  - #{channel['name']} (ID: {channel['id']})")
                
            # Listar DMs
            dms = client.conversations_list(types="im")
            print(f"💬 Mensajes directos: {len(dms['channels'])} disponibles")
            
            return public_channels["channels"] + private_channels["channels"]
            
        except Exception as e:
            print(f"❌ Error listando canales Slack: {e}")
            return []

    def send_slack_error(self, errors: list):
        """Envía errores críticos a Slack"""
        try:
            from slack_sdk import WebClient
            
            slack_token = os.getenv("SLACK_BOT_TOKEN")
            channel = os.getenv("SLACK_CHANNEL", "blog-posts")
            # Añadir # si no está presente
            if channel and not channel.startswith('#'):
                channel = f"#{channel}"
            
            print(f"🔍 Debug Slack: token={slack_token[:10] if slack_token else 'None'}..., channel='{channel}'")
            
            # Listar canales disponibles para debug
            self.list_slack_channels()
            
            if not slack_token:
                print("❌ SLACK_BOT_TOKEN no configurado")
                return
            
            client = WebClient(token=slack_token)
            
            error_message = "🚨 **BLOG POST RECHAZADO - ERRORES CRÍTICOS**\n\n"
            for i, error in enumerate(errors, 1):
                error_message += f"{i}. {error}\n"
            
            error_message += "\n❌ **NO SE REALIZÓ COMMIT** - Corrige los errores y vuelve a ejecutar"
            
            client.chat_postMessage(
                channel=channel,
                text=error_message,
                username="Blog Automation"
            )
            print(f"✅ Error reportado en Slack canal {channel}")
            
        except Exception as e:
            print(f"❌ Error enviando a Slack: {e}")

    def send_slack_success(self, blog_data: dict, latest_file: str):
        """Envía notificación de éxito a Slack"""
        try:
            from slack_sdk import WebClient
            
            slack_token = os.getenv("SLACK_BOT_TOKEN")
            channel = os.getenv("SLACK_CHANNEL", "blog-posts")
            # Añadir # si no está presente
            if channel and not channel.startswith('#'):
                channel = f"#{channel}"
            
            print(f"🔍 Debug Slack Success: token={slack_token[:10] if slack_token else 'None'}..., channel='{channel}'")
            
            # Listar canales disponibles para debug
            self.list_slack_channels()
            
            if not slack_token:
                print("❌ SLACK_BOT_TOKEN no configurado")
                return
            
            client = WebClient(token=slack_token)
            
            success_message = f"""🎉 NUEVO BLOG POST PUBLICADO - {blog_data.get('date', 'N/A')}
📰 Título: {blog_data.get('title', 'Sin título')}
🔗 Link: wrappers.es/blog/{blog_data.get('slug', 'sin-slug')}
📝 Resumen: {blog_data.get('summary', 'Sin resumen')}"""
            
            client.chat_postMessage(
                channel=channel,
                text=success_message,
                username="Blog Automation"
            )
            print(f"✅ Notificación de éxito enviada a Slack canal {channel}")
            
        except Exception as e:
            print(f"❌ Error enviando notificación de éxito a Slack: {e}")

    def run_automation(self) -> Dict[str, Any]:
        """
        Ejecuta el flujo completo de automatización CON VALIDACIONES CRÍTICAS
        
        ¿Cómo funciona el flujo?
        1. Research Agent busca temas trending (CON ACCESO A INTERNET)
        2. Writer Agent crea el post usando esa investigación (CON ACCESO A INTERNET para verificar datos)
        3. QA Agent valida formato y calidad
        4. **VALIDACIONES CRÍTICAS** - Si falla, NO procede
        5. Technical Agent maneja commit y deployment SOLO si validaciones pasan
        """
        
        # Crear los agentes
        research_agent = self.create_research_agent()
        writer_agent = self.create_writer_agent()
        qa_agent = self.create_qa_agent()
        
        # Crear las tareas en secuencia
        research_task = self.create_research_task(research_agent)
        writing_task = self.create_writing_task(writer_agent, research_task)
        qa_task = self.create_qa_task(qa_agent, writing_task)
        
        # Crear y ejecutar el crew SIN technical task (validamos primero)
        crew_content = Crew(
            agents=[research_agent, writer_agent, qa_agent],
            tasks=[research_task, writing_task, qa_task],
            verbose=True,
            memory=True,  # Los agentes recuerdan contexto entre ejecuciones
            max_rpm=10    # Control de rate limiting para APIs
        )
        
        # Ejecutar el flujo
        try:
            print("🚀 Iniciando automatización de blog post...")
            content_result = crew_content.kickoff()
            
            print("\n🔍 EJECUTANDO VALIDACIONES CRÍTICAS...")
            
            # Leer el archivo generado para validación
            # Encontrar el archivo JSON generado más reciente
            json_files = [f for f in os.listdir('.') if f.endswith('.json')]
            # Filtrar archivos de configuración comunes Y blog_posts.json (colección)
            json_files = [f for f in json_files if not f.startswith('.') and 'package' not in f.lower() and f != 'blog_posts.json']
            
            if not json_files:
                print("🔍 Debug: Archivos en directorio:", os.listdir('.'))
                print("🔍 Debug: Archivos JSON encontrados antes de filtrar:", [f for f in os.listdir('.') if f.endswith('.json')])
                self.send_slack_error(["❌ No se encontró archivo JSON generado (excluyendo blog_posts.json)"])
                return {"status": "error", "message": "No se encontró archivo JSON generado"}
            
            latest_file = max(json_files, key=os.path.getctime)
            
            with open(latest_file, 'r', encoding='utf-8') as f:
                blog_content = f.read()
            
            # VALIDACIÓN CRÍTICA
            validation = self.validate_blog_post_strict(blog_content, str(content_result))
            
            # Si la validación pasó y el contenido fue limpiado, reescribir el archivo
            if validation["valid"] and validation.get("cleaned_content"):
                with open(latest_file, 'w', encoding='utf-8') as f:
                    f.write(validation["cleaned_content"])
                print(f"🔧 Archivo limpiado y reescrito: {latest_file}")
            
            if not validation["valid"]:
                print(f"\n🚨 VALIDACIÓN FALLÓ - {len(validation['errors'])} errores críticos:")
                for error in validation["errors"]:
                    print(f"  {error}")
                
                # SAVE FILE FOR DEBUGGING instead of deleting
                debug_file = f"DEBUG_{latest_file}"
                import shutil
                shutil.copy2(latest_file, debug_file)
                print(f"🔍 Archivo copiado para debug: {debug_file}")
                
                # If it's a JSON control character issue, try manual fix
                if any("control character" in error for error in validation["errors"]):
                    print(f"🔧 Intentando reparación manual del JSON...")
                    try:
                        with open(latest_file, 'r', encoding='utf-8') as f:
                            content = f.read()
                        
                        # VERY aggressive cleaning - keep only printable + newlines
                        import string
                        cleaned = ''.join(char for char in content if char in string.printable)
                        
                        with open(latest_file, 'w', encoding='utf-8') as f:
                            f.write(cleaned)
                            
                        print(f"🔧 Archivo reparado, reintentando validación...")
                        validation_retry = self.validate_blog_post_strict(cleaned, str(content_result))
                        
                        if validation_retry["valid"]:
                            print(f"✅ Reparación exitosa!")
                            validation = validation_retry  # Use the successful validation
                        else:
                            print(f"❌ Reparación falló: {validation_retry['errors']}")
                            # Don't delete, keep for manual inspection
                            self.send_slack_error(validation["errors"])
                            return {
                                "status": "error", 
                                "message": "Blog post rechazado por errores críticos - archivo preservado para debug",
                                "errors": validation["errors"],
                                "debug_file": debug_file
                            }
                    except Exception as e:
                        print(f"❌ Error en reparación: {e}")
                
                if not validation.get("fixed", False):
                    # Enviar errores a Slack pero NO eliminar archivo
                    self.send_slack_error(validation["errors"])
                    return {
                        "status": "error", 
                        "message": "Blog post rechazado por errores críticos - archivo preservado para debug",
                        "errors": validation["errors"],
                        "debug_file": debug_file
                    }
            
            print("✅ TODAS LAS VALIDACIONES PASARON - Procediendo con commit...")
            
            # Solo ahora crear y usar technical agent
            technical_agent = self.create_technical_agent()
            technical_task = self.create_technical_task(technical_agent, writing_task, latest_file)
            
            crew_deploy = Crew(
                agents=[technical_agent],
                tasks=[technical_task],
                verbose=True
            )
            
            deploy_result = crew_deploy.kickoff()
            
            # Verificar si deployment fue exitoso
            if "deployment process was unsuccessful" in str(deploy_result).lower() or "error" in str(deploy_result).lower():
                error_msg = f"Deployment falló: {deploy_result}"
                print(f"❌ {error_msg}")
                self.send_slack_error([error_msg])
                return {
                    "status": "error",
                    "message": "Blog post validado pero deployment falló",
                    "content_result": content_result,
                    "deploy_result": deploy_result,
                    "file": latest_file
                }
            
            print("✅ Blog post creado y deployado exitosamente!")
            
            # Enviar notificación de éxito a Slack
            blog_data = json.loads(blog_content)
            self.send_slack_success(blog_data, latest_file)
            
            return {
                "status": "success",
                "message": "Blog post validado, creado y deployeado correctamente",
                "content_result": content_result,
                "deploy_result": deploy_result,
                "file": latest_file
            }
            
        except Exception as e:
            error_msg = f"Error en automatización: {str(e)}"
            print(f"❌ {error_msg}")
            self.send_slack_error([error_msg])
            return {"status": "error", "message": error_msg}

# Configuración para ejecutar como script
if __name__ == "__main__":
    print("🤖 Blog Automation System powered by CrewAI")
    print("=" * 50)
    
    # Verificar variables de entorno necesarias
    required_env_vars = ["OPENAI_API_KEY", "SERPER_API_KEY"]
    missing_vars = [var for var in required_env_vars if not os.getenv(var)]
    
    if missing_vars:
        print(f"❌ Faltan variables de entorno: {', '.join(missing_vars)}")
        print("Crea un archivo .env con las claves necesarias")
        exit(1)
    
    # Ejecutar automatización
    automation = BlogAutomationCrew()
    result = automation.run_automation()
    
    print("\n" + "=" * 50)
    print(f"📊 Resultado: {result['status']}")
    print(f"💬 Mensaje: {result['message']}") 