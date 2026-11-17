# GitHub Developer Intelligence MCP

A GitHub Developer Intelligence server built using the **Model Context Protocol (MCP)** and Python. It enables AI assistants such as Claude Desktop to interact with GitHub repositories through structured tools, resources, and prompts.

Instead of manually navigating GitHub, users can ask an AI assistant to analyze repositories, explore programming languages, inspect commit history, discover contributors, and search source code using natural language.

## Features

### MCP Tools

The server currently provides seven tools:

| Tool                       | Description                                                  |
| -------------------------- | ------------------------------------------------------------ |
| `search_repositories`      | Search GitHub repositories using a query.                    |
| `get_repo_details`         | Retrieve detailed information about a repository.            |
| `get_repository_languages` | Get programming languages and their percentage distribution. |
| `get_commit_history`       | Retrieve recent commits, authors, messages, and dates.       |
| `get_contributors`         | Retrieve repository contributors and contribution counts.    |
| `get_readme`               | Fetch and decode a repository's README file.                 |
| `search_code`              | Search source code across GitHub repositories.               |

### MCP Resources

Resources expose repository information through standardized URIs.

| Resource           | URI                                          |
| ------------------ | -------------------------------------------- |
| Repository Details | `github://repository/{owner}/{repo}/details` |
| Repository README  | `github://repository/{owner}/{repo}/readme`  |

### MCP Prompts

Reusable prompt templates for repository analysis:

- `analyze_repository` – Helps an AI assistant analyze a repository's structure, technologies, and development activity.
- `review_repository` – Provides a reusable starting point for reviewing a repository.

## Architecture

```text
              User
               |
               v
         Claude Desktop
          (MCP Client)
               |
               | MCP Protocol
               v
        GitHub MCP Server
          (FastMCP)
               |
               v
         GitHub Client
            (HTTPX)
               |
               | HTTPS Requests
               v
          GitHub REST API
               |
               v
         Repository Data
```

The LLM interprets the user's request and decides which available MCP tools to invoke. The MCP server handles tool execution and communicates with the GitHub REST API.

## Technology Stack

- **Python 3.11+**
- **MCP Python SDK** – MCP server implementation
- **FastMCP** – Tool, resource, and prompt registration
- **HTTPX** – Asynchronous HTTP requests
- **Pydantic** – Data validation
- **python-dotenv** – Environment variable management
- **pytest** – Automated testing
- **uv** – Python package and project management

## Project Structure

```text
github-developer-intelligence-mcp/
│
├── src/
│   └── github_mcp/
│       ├── __init__.py
│       ├── server.py
│       ├── github_client.py
│       └── config.py
│
├── tests/
│
├── .env
├── .env.example
├── .gitignore
├── pyproject.toml
├── uv.lock
└── README.md
```

## Getting Started

### 1. Prerequisites

Install the following:

- Python 3.11 or higher
- uv
- Git
- Claude Desktop (for local integration)

### 2. Clone the Repository

```bash
git clone https://github.com/YOUR_USERNAME/github-developer-intelligence-mcp.git

cd github-developer-intelligence-mcp
```

Replace `YOUR_USERNAME` with your GitHub username after publishing the project.

### 3. Install Dependencies

```bash
uv sync
```

### 4. Configure Environment Variables

Create a `.env` file in the project root:

```env
GITHUB_TOKEN=your_github_personal_access_token
```

A GitHub token is recommended for authenticated API requests and access to endpoints that require authentication.

Never commit your actual `.env` file or expose your token publicly.

### 5. Configure Python Path

For Windows PowerShell, run:

```powershell
$env:PYTHONPATH = "$PWD\src"
```

### 6. Run the MCP Server

```bash
uv run python -m github_mcp.server
```

The server uses the standard input/output (STDIO) transport. It may appear to wait without displaying anything when started directly. This is expected behavior.

## Claude Desktop Integration

Add the following MCP server configuration to your Claude Desktop MCP configuration file.

```json
{
  "mcpServers": {
    "github-intelligence": {
      "command": "C:\\PATH\\TO\\uv.exe",
      "args": [
        "--directory",
        "C:\\PATH\\TO\\github-developer-intelligence-mcp",
        "run",
        "python",
        "-m",
        "github_mcp.server"
      ],
      "env": {
        "PYTHONPATH": "C:\\PATH\\TO\\github-developer-intelligence-mcp\\src"
      }
    }
  }
}
```

Replace the paths with your actual Windows paths.

After saving the configuration:

1. Restart Claude Desktop or reload its MCP configuration.
2. Open the connected MCP server.
3. Verify that the GitHub tools are available.
4. Ask Claude to analyze a public GitHub repository.

## Example Usage

Try asking Claude:

```text
Analyze the fastapi/fastapi repository.

Fetch:
1. Repository details
2. Programming languages
3. Latest five commits
4. Top five contributors

Present the results in a structured format.
```

Claude can select and invoke the relevant MCP tools and combine their results into a single response.

## Testing

The project includes automated tests for validation, GitHub API communication, MCP tools, resources, and prompts.

Run the test suite:

```powershell
$env:PYTHONPATH = "$PWD\src"
uv run pytest -v
```

The current test suite contains 46 test cases.

## Error Handling and Reliability

The project includes:

- Custom GitHub API error handling.
- HTTP status code handling.
- Network and timeout error handling.
- Structured logging.
- GitHub API rate-limit awareness.
- Input validation for repository names and search queries.
- Pagination support for collection tools.
- README response size limiting and truncation handling.

## Future Improvements

- Remote deployment using Streamable HTTP transport.
- Additional GitHub analytics tools.
- Improved repository intelligence and code analysis.
- More automated tests and integration coverage.

## License

This project is open source. A license will be added when the repository is published.
