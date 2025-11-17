### Run MCP SERVER
# Create virtual environment
python -m venv .venv

# Activate venv
.\.venv\Scripts\activate

# Upgrade pip
python -m pip install --upgrade pip

# install packages
pip install mcp yfinance pandas
pip install mcp[cli]

# run mcp server
mcp dev server.py


### Run API
pip install -r requirements.txt

# run api server
cd C:\Personal\MCP-SERVERS\options-news-platform\mcp_yahoo_options_python; C:/Personal/MCP-SERVERS/options-news-platform/mcp_yahoo_options_python/.venv/Scripts/python.exe -m uvicorn api_server:app --reload --port 8000

