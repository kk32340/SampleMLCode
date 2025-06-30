# Microsoft Teams Digital Agent

An AI-powered digital agent for Microsoft Teams that uses Google's Gemini AI to provide intelligent assistance, document analysis, and conversational support.

## Features

- 🤖 **AI-Powered Conversations**: Uses Google Gemini for natural language understanding
- 📄 **Document Processing**: Analyzes PDF, Word, Excel, CSV, JSON, and text files
- 💬 **Context Awareness**: Maintains conversation history for better interactions
- ⚡ **Real-time Responses**: Fast and responsive within Teams chat
- 🔧 **Customizable**: Easy to extend with additional capabilities

## Prerequisites

- Python 3.9 or higher
- Microsoft Teams account
- Google Gemini API key
- Azure Bot Service registration (for production deployment)

## Quick Start (Development)

### 1. Clone and Setup

```bash
git clone <your-repo>
cd ML2
pip install -r requirements.txt
```

### 2. Configure Environment

Copy the example environment file:
```bash
copy .env.example .env
```

Edit `.env` and add your API keys:
```env
GEMINI_API_KEY=your_actual_gemini_api_key
```

### 3. Run the Bot Locally

```bash
python teams_bot.py
```

The bot will start on `http://localhost:3978`

### 4. Test with Bot Framework Emulator

1. Download [Bot Framework Emulator](https://github.com/Microsoft/BotFramework-Emulator/releases)
2. Connect to `http://localhost:3978/api/messages`
3. Start chatting with your bot!

## Production Deployment

### 1. Azure Bot Service Setup

1. Go to [Azure Portal](https://portal.azure.com)
2. Create a new "Azure Bot" resource
3. Note down the App ID and App Password
4. Update your `.env` file:

```env
MICROSOFT_APP_ID=your_app_id
MICROSOFT_APP_PASSWORD=your_app_password
MICROSOFT_APP_TENANT_ID=your_tenant_id
```

### 2. Deploy to Azure App Service

```bash
# Create App Service
az webapp create --resource-group myResourceGroup --plan myAppServicePlan --name myTeamsBot --runtime "python|3.9"

# Deploy your code
az webapp deployment source config --name myTeamsBot --resource-group myResourceGroup --repo-url <your-repo> --branch main
```

### 3. Configure Teams App

1. Update `manifest.json` with your bot's App ID
2. Create app package with manifest and icons
3. Upload to Teams Admin Center or sideload for testing

## Usage

### Basic Commands

- `/help` - Show available commands and capabilities
- `/clear` - Clear conversation history
- `/status` - Check bot health and status

### Natural Conversation

Just chat naturally with the bot:
```
User: What is machine learning?
Bot: Machine learning is a subset of artificial intelligence (AI) that focuses on...

User: Can you explain it in simpler terms?
Bot: Sure! Think of machine learning like teaching a computer to recognize patterns...
```

### Document Analysis

Share files in Teams chat and the bot will analyze them:
- PDF documents
- Word documents (.docx)
- Excel spreadsheets (.xlsx)
- CSV files
- JSON files
- Text files

## Project Structure

```
ML2/
├── teams_bot.py              # Main bot application
├── document_processor.py     # Document processing utilities
├── minimal_gemeni.py         # Gemini AI integration
├── config.py                 # Configuration management
├── requirements.txt          # Python dependencies
├── manifest.json            # Teams app manifest
├── .env.example             # Environment variables template
└── README.md               # This file
```

## Configuration Options

### Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `GEMINI_API_KEY` | Yes | - | Google Gemini API key |
| `MICROSOFT_APP_ID` | Production | - | Azure Bot Service App ID |
| `MICROSOFT_APP_PASSWORD` | Production | - | Azure Bot Service App Password |
| `PORT` | No | 3978 | Server port |
| `GEMINI_MODEL` | No | gemini-1.5-flash-latest | Gemini model to use |
| `MAX_CONVERSATION_HISTORY` | No | 20 | Max conversation messages to remember |

### Bot Capabilities

The bot can be customized to:
- Process different document types
- Integrate with other AI models
- Connect to databases or APIs
- Provide specialized domain knowledge
- Handle file uploads and analysis

## Development

### Adding New Features

1. **New Commands**: Add command handlers in `TeamsDigitalAgent._process_message()`
2. **Document Types**: Extend `DocumentProcessor` class
3. **AI Models**: Modify `_initialize_gemini()` or add new model integrations

### Testing

```bash
# Install test dependencies
pip install pytest pytest-asyncio

# Run tests
pytest tests/
```

### Debugging

Enable debug logging by setting:
```env
LOG_LEVEL=DEBUG
```

## API Keys Setup

### Google Gemini API Key

1. Go to [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Create a new API key
3. Add to your `.env` file

### Microsoft Bot Framework (Production)

1. Go to [Azure Portal](https://portal.azure.com)
2. Create "Azure Bot" resource
3. Get App ID and Password from Configuration
4. Add to your `.env` file

## Troubleshooting

### Common Issues

1. **Bot not responding**: Check if Gemini API key is valid
2. **Authentication errors**: Verify Microsoft App credentials
3. **File processing errors**: Check file size and format
4. **Memory issues**: Reduce `MAX_CONVERSATION_HISTORY`

### Logs

Check application logs for detailed error information:
```bash
# View logs in Azure
az webapp log tail --name myTeamsBot --resource-group myResourceGroup
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

This project is licensed under the MIT License.

## Support

For support and questions:
- Check the troubleshooting section
- Review Azure Bot Service documentation
- Consult Microsoft Teams development docs 