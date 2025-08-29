# 📸 Screenshots Guide

This directory contains all screenshots used in the main README.md file. Follow this guide to capture and organize the screenshots properly.

## 📋 Required Screenshots List

### 1. **Platform Overview** (`platform-overview.png`)
**What to capture**: A high-level view showing multiple components
- N8N workflow dashboard (partial view)
- One of the HTML reports open in browser
- Terminal windows showing running servers
- **Size**: 1920x1080 or similar wide format
- **Focus**: Show the complete platform ecosystem

### 2. **Architecture Diagram** (`architecture-diagram.png`)
**What to capture**: Create a diagram showing data flow
- Data sources (NVD, VulDB, CVEFind, DGSSI, etc.)
- N8N processing pipeline
- AI/LLM analysis
- Output formats (Email, Dashboard, SIEM)
- **Tool**: Use draw.io, Lucidchart, or similar
- **Size**: 1600x900 recommended

### 3. **N8N Workflow Overview** (`n8n-workflow-overview.png`)
**What to capture**: Complete N8N workflow canvas
- All nodes visible (zoom out to show full workflow)
- Clear node connections and flow
- Node names readable
- **Size**: Full workflow view, high resolution
- **Tip**: Use N8N's export/screenshot feature if available

### 4. **Executive Dashboard** (`executive-dashboard.png`)
**What to capture**: HTML report in browser
- Full page view of the generated HTML report
- Statistics cards showing CVE counts
- Risk level distribution
- Clean browser view (hide bookmarks/extensions)
- **Size**: Full page screenshot, 1920x1080+

### 5. **CVE Detailed Report** (`cve-detailed-report.png`)
**What to capture**: Detailed CVE cards section
- Individual CVE cards with priority scores
- AI-generated summaries visible
- Risk badges and CVSS scores
- Affected products information
- **Focus**: Show 3-4 CVE cards clearly

### 6. **Email Notification** (`email-notification.png`)
**What to capture**: Gmail interface showing sent report
- Email with HTML content rendered
- Subject line visible
- Recipient information (blur sensitive data)
- Report content preview
- **Size**: Standard email view

### 7. **Kibana Dashboard** (`kibana-dashboard.png`)
**What to capture**: ELK Stack visualization
- Kibana interface with threat data
- Charts/graphs showing CVE trends
- Search/filter capabilities
- Data visualization panels
- **URL**: http://localhost:5601

### 8. **API Endpoints** (`api-endpoints.png`)
**What to capture**: API responses in browser/Postman
- JSON response from one of the CVE APIs
- Clean formatting (use JSON formatter)
- Show endpoint URL
- Response structure clearly visible
- **Example**: http://localhost:5001/api/cves

### 9. **Data Collection Sources** (`data-collection-sources.png`)
**What to capture**: Multiple browser tabs/windows
- NVD website
- CVEFind.com interface
- DGSSI bulletins page
- CERT-FR RSS feed
- **Layout**: Tile/mosaic view showing all sources

### 10. **AI LLM Processing** (`ai-llm-processing.png`)
**What to capture**: N8N execution view
- LLM node execution details
- Input/output data preview
- Processing status/logs
- Groq API integration node
- **Focus**: Show AI processing in action

### 11. **Advanced Reporting** (`reporting-dashboard.png`)
**What to capture**: Report generation process
- N8N nodes for report generation
- HTML output preview
- Multiple format outputs (HTML, JSON)
- **Focus**: Show reporting pipeline

### 12. **Integration ELK Stack** (`integration-elk-stack.png`)
**What to capture**: Docker containers and services
- Docker Desktop showing running containers
- Elasticsearch, Kibana, Logstash status
- Port mappings visible
- Container logs (optional)
- **Command**: `docker-compose ps`

### 13. **Project File Structure** (`project-file-structure.png`)
**What to capture**: File explorer/IDE view
- Complete project directory structure
- All folders expanded to show files
- File types and organization clear
- **Tool**: VS Code Explorer, Windows Explorer, or terminal `tree` command

### 14. **ELK Stack Startup** (`elk-stack-startup.png`)
**What to capture**: Terminal showing Docker Compose
- `docker-compose up -d` command execution
- Container startup logs
- Success messages
- Service status confirmation
- **Size**: Terminal window, readable text

### 15. **Servers Startup Script** (`servers-startup-script.png`)
**What to capture**: Batch script execution
- `start_all_servers.bat` running
- Multiple terminal windows opening
- Server startup messages
- Port assignments visible
- **Layout**: Show multiple terminal windows

### 16. **N8N Workflow Import** (`n8n-workflow-import.png`)
**What to capture**: N8N import process
- Import dialog/interface
- Workflow file selection
- Import success confirmation
- Workflow loaded in canvas
- **Focus**: Show import process steps

## 📐 Screenshot Guidelines

### **General Requirements**
- **Resolution**: Minimum 1920x1080 for wide shots
- **Format**: PNG (preferred) or high-quality JPG
- **File Size**: Keep under 2MB each for GitHub compatibility
- **Naming**: Use exact filenames as listed above

### **Quality Standards**
- **Clarity**: Text must be readable at normal viewing size
- **Lighting**: Use consistent, bright interface themes
- **Cropping**: Remove unnecessary UI elements (taskbars, etc.)
- **Privacy**: Blur/hide sensitive information (emails, IPs, keys)

### **Browser Screenshots**
- **Clean Interface**: Hide bookmarks, extensions, personal data
- **Full Page**: Use browser extensions for full-page captures
- **Zoom Level**: 100% zoom for consistency
- **Theme**: Use light themes for better readability

### **Terminal Screenshots**
- **Font Size**: Large enough to read (14pt+)
- **Color Scheme**: High contrast (dark background, light text)
- **Window Size**: Maximize for full command visibility
- **Clean Output**: Clear terminal before important commands

## 🛠️ Recommended Tools

### **Screenshot Capture**
- **Windows**: Snipping Tool, Greenshot, ShareX
- **Mac**: Screenshot utility (Cmd+Shift+4), CleanShot X
- **Linux**: GNOME Screenshot, Flameshot
- **Browser**: Full Page Screen Capture extensions

### **Image Editing**
- **Basic**: Paint.NET, GIMP (free)
- **Advanced**: Photoshop, Canva
- **Online**: Photopea, Canva

### **Diagram Creation**
- **Free**: Draw.io, Lucidchart (free tier)
- **Advanced**: Visio, OmniGraffle
- **Code**: Mermaid diagrams

## 📝 Naming Convention

```
screenshots/
├── platform-overview.png           # Main hero image
├── architecture-diagram.png        # System architecture
├── n8n-workflow-overview.png      # Complete workflow
├── executive-dashboard.png         # HTML report
├── cve-detailed-report.png        # CVE analysis
├── email-notification.png         # Gmail integration
├── kibana-dashboard.png           # ELK visualization
├── api-endpoints.png              # REST API responses
├── data-collection-sources.png    # Source websites
├── ai-llm-processing.png          # AI analysis
├── reporting-dashboard.png        # Report generation
├── integration-elk-stack.png      # Docker containers
├── project-file-structure.png     # File organization
├── elk-stack-startup.png          # Docker startup
├── servers-startup-script.png     # Batch script
└── n8n-workflow-import.png        # Workflow import
```

## ✅ Checklist

Before committing screenshots:
- [ ] All 16 screenshots captured
- [ ] Filenames match exactly
- [ ] Image quality is high
- [ ] Sensitive data is hidden/blurred
- [ ] File sizes are reasonable (<2MB each)
- [ ] Screenshots show current/working state
- [ ] Text is readable at normal size
- [ ] Consistent styling/themes used

## 🔄 Update Process

When updating screenshots:
1. **Backup old versions** (rename with date suffix)
2. **Capture new screenshots** following this guide
3. **Test README rendering** locally
4. **Commit changes** with descriptive message
5. **Verify GitHub display** after push

---

**Note**: Screenshots should be updated whenever major UI changes occur or new features are added to maintain documentation accuracy.
