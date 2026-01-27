#!/usr/bin/env python3
"""
Snipe-IT Monitor - Automated Deployment Script
This script creates all necessary files and Docker configuration
"""

import os
import sys
import subprocess
from pathlib import Path

class Colors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'

def print_header(text):
    print(f"\n{Colors.HEADER}{Colors.BOLD}{'='*60}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}{text}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}{'='*60}{Colors.ENDC}\n")

def print_success(text):
    print(f"{Colors.OKGREEN}✓ {text}{Colors.ENDC}")

def print_error(text):
    print(f"{Colors.FAIL}✗ {text}{Colors.ENDC}")

def print_info(text):
    print(f"{Colors.OKCYAN}ℹ {text}{Colors.ENDC}")

def run_command(cmd, check=True):
    """Run a shell command"""
    try:
        result = subprocess.run(cmd, shell=True, check=check, capture_output=True, text=True)
        return result.returncode == 0
    except subprocess.CalledProcessError as e:
        print_error(f"Command failed: {cmd}")
        print(e.stderr)
        return False

def create_directory_structure(base_dir):
    """Create project directory structure"""
    print_info("Creating directory structure...")

    directories = [
        base_dir,
        f"{base_dir}/src",
        f"{base_dir}/public",
    ]

    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)
        print_success(f"Created: {directory}")

def create_dockerfile(base_dir):
    """Create Dockerfile"""
    print_info("Creating Dockerfile...")

    dockerfile_content = """# Build stage
FROM node:18-alpine as build

WORKDIR /app

# Copy package files
COPY package*.json ./

# Install dependencies
RUN npm install

# Copy source code
COPY . .

# Build the app
RUN npm run build

# Production stage
FROM nginx:alpine

# Copy built files from build stage
COPY --from=build /app/dist /usr/share/nginx/html

# Copy nginx configuration
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Expose port 80
EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
"""

    with open(f"{base_dir}/Dockerfile", "w") as f:
        f.write(dockerfile_content)

    print_success("Dockerfile created")

def create_nginx_conf(base_dir):
    """Create nginx configuration"""
    print_info("Creating nginx.conf...")

    nginx_content = """server {
    listen 80;
    server_name localhost;
    root /usr/share/nginx/html;
    index index.html;

    location / {
        try_files $uri $uri/ /index.html;
        add_header Cache-Control "no-cache";

        # CORS headers
        add_header 'Access-Control-Allow-Origin' '*' always;
        add_header 'Access-Control-Allow-Methods' 'GET, POST, PUT, DELETE, OPTIONS' always;
        add_header 'Access-Control-Allow-Headers' 'Content-Type, Authorization' always;

        # Handle preflight requests
        if ($request_method = 'OPTIONS') {
            add_header 'Access-Control-Allow-Origin' '*';
            add_header 'Access-Control-Allow-Methods' 'GET, POST, PUT, DELETE, OPTIONS';
            add_header 'Access-Control-Allow-Headers' 'Content-Type, Authorization';
            add_header 'Access-Control-Max-Age' 1728000;
            add_header 'Content-Type' 'text/plain; charset=utf-8';
            add_header 'Content-Length' 0;
            return 204;
        }
    }

    location /static {
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
}
"""

    with open(f"{base_dir}/nginx.conf", "w") as f:
        f.write(nginx_content)

    print_success("nginx.conf created")

def create_docker_compose(base_dir, snipeit_url, snipeit_token):
    """Create docker-compose.yml"""
    print_info("Creating docker-compose.yml...")

    docker_compose_content = f"""version: '3.8'

services:
  snipeit-monitor:
    build: .
    container_name: snipeit-monitor
    ports:
      - "3000:80"
    environment:
      - SNIPEIT_API_URL={snipeit_url}
      - SNIPEIT_API_TOKEN={snipeit_token}
    restart: unless-stopped
    networks:
      - snipeit-network

networks:
  snipeit-network:
    driver: bridge
"""

    with open(f"{base_dir}/docker-compose.yml", "w") as f:
        f.write(docker_compose_content)

    print_success("docker-compose.yml created")

def create_package_json(base_dir):
    """Create package.json"""
    print_info("Creating package.json...")

    package_json_content = """{
  "name": "snipeit-monitor",
  "version": "1.0.0",
  "type": "module",
  "scripts": {
    "dev": "vite",
    "build": "vite build",
    "preview": "vite preview"
  },
  "dependencies": {
    "react": "^18.2.0",
    "react-dom": "^18.2.0",
    "lucide-react": "^0.263.1"
  },
  "devDependencies": {
    "@vitejs/plugin-react": "^4.0.0",
    "vite": "^4.3.9",
    "tailwindcss": "^3.3.2",
    "postcss": "^8.4.24",
    "autoprefixer": "^10.4.14"
  }
}
"""

    with open(f"{base_dir}/package.json", "w") as f:
        f.write(package_json_content)

    print_success("package.json created")

def create_vite_config(base_dir):
    """Create vite.config.js"""
    print_info("Creating vite.config.js...")

    vite_config_content = """import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    host: '0.0.0.0',
    port: 3000
  }
})
"""

    with open(f"{base_dir}/vite.config.js", "w") as f:
        f.write(vite_config_content)

    print_success("vite.config.js created")

def create_tailwind_config(base_dir):
    """Create tailwind.config.js"""
    print_info("Creating tailwind.config.js...")

    tailwind_config = """/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {},
  },
  plugins: [],
}
"""

    with open(f"{base_dir}/tailwind.config.js", "w") as f:
        f.write(tailwind_config)

    print_success("tailwind.config.js created")

def create_postcss_config(base_dir):
    """Create postcss.config.js"""
    print_info("Creating postcss.config.js...")

    postcss_config = """export default {
  plugins: {
    tailwindcss: {},
    autoprefixer: {},
  },
}
"""

    with open(f"{base_dir}/postcss.config.js", "w") as f:
        f.write(postcss_config)

    print_success("postcss.config.js created")

def create_index_html(base_dir):
    """Create index.html"""
    print_info("Creating index.html...")

    index_html = """<!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>Snipe-IT Asset Monitor</title>
  </head>
  <body>
    <div id="root"></div>
    <script type="module" src="/src/main.jsx"></script>
  </body>
</html>
"""

    with open(f"{base_dir}/index.html", "w") as f:
        f.write(index_html)

    print_success("index.html created")

def create_index_css(base_dir):
    """Create src/index.css"""
    print_info("Creating src/index.css...")

    index_css = """@tailwind base;
@tailwind components;
@tailwind utilities;

* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

body {
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', 'Oxygen',
    'Ubuntu', 'Cantarell', 'Fira Sans', 'Droid Sans', 'Helvetica Neue',
    sans-serif;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
}
"""

    with open(f"{base_dir}/src/index.css", "w") as f:
        f.write(index_css)

    print_success("src/index.css created")

def create_main_jsx(base_dir):
    """Create src/main.jsx"""
    print_info("Creating src/main.jsx...")

    main_jsx = """import React from 'react'
import ReactDOM from 'react-dom/client'
import App from './App'
import './index.css'

ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
)
"""

    with open(f"{base_dir}/src/main.jsx", "w") as f:
        f.write(main_jsx)

    print_success("src/main.jsx created")

def create_app_jsx(base_dir, snipeit_url, snipeit_token):
    """Create src/App.jsx"""
    print_info("Creating src/App.jsx...")

    app_jsx = f"""import React, {{ useState, useEffect }} from 'react';
import {{ RefreshCw, CheckCircle, XCircle, Clock, Laptop, Monitor, Search, Filter }} from 'lucide-react';

const SnipeITMonitor = () => {{
  const [assets, setAssets] = useState([]);
  const [loading, setLoading] = useState(true);
  const [lastUpdate, setLastUpdate] = useState(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [filterType, setFilterType] = useState('all');
  const [stats, setStats] = useState({{
    total: 0,
    registered: 0,
    pending: 0,
    laptops: 0,
    desktops: 0
  }});

  const SNIPEIT_API_URL = '{snipeit_url}';
  const SNIPEIT_API_TOKEN = '{snipeit_token}';

  const fetchAssets = async () => {{
    try {{
      setLoading(true);
      const response = await fetch(`${{SNIPEIT_API_URL}}/hardware?limit=500`, {{
        headers: {{
          'Authorization': `Bearer ${{SNIPEIT_API_TOKEN}}`,
          'Accept': 'application/json',
          'Content-Type': 'application/json'
        }}
      }});

      if (!response.ok) {{
        throw new Error(`HTTP error! status: ${{response.status}}`);
      }}

      const data = await response.json();

      if (data && data.rows) {{
        const processedAssets = data.rows.map(asset => ({{
          id: asset.id,
          name: asset.name || 'Unknown',
          assetTag: asset.asset_tag,
          serial: asset.serial,
          model: asset.model?.name || 'Unknown Model',
          category: asset.category?.name || 'Unknown',
          status: asset.status_label?.name || 'Unknown',
          ip: asset.custom_fields?._snipeit_ip_address_1 || 'N/A',
          mac: asset.custom_fields?._snipeit_mac_address_2 || 'N/A',
          user: asset.custom_fields?._snipeit_windows_username_7 || 'N/A',
          lastUpdated: asset.updated_at?.datetime || asset.created_at?.datetime,
          isRegistered: asset.status_label?.status_meta === 'deployed' || asset.status_label?.name === 'Ready to Deploy',
          type: asset.category?.name?.toLowerCase().includes('laptop') ? 'laptop' : 'desktop'
        }}));

        setAssets(processedAssets);

        const registered = processedAssets.filter(a => a.isRegistered).length;
        const laptops = processedAssets.filter(a => a.type === 'laptop').length;
        const desktops = processedAssets.filter(a => a.type === 'desktop').length;

        setStats({{
          total: processedAssets.length,
          registered: registered,
          pending: processedAssets.length - registered,
          laptops: laptops,
          desktops: desktops
        }});
      }}

      setLastUpdate(new Date());
    }} catch (error) {{
      console.error('Error fetching assets:', error);
      alert('Failed to connect to Snipe-IT API. Please check your connection and API settings.');
    }} finally {{
      setLoading(false);
    }}
  }};

  useEffect(() => {{
    fetchAssets();
    const interval = setInterval(fetchAssets, 30000);
    return () => clearInterval(interval);
  }}, []);

  const filteredAssets = assets.filter(asset => {{
    const matchesSearch =
      asset.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
      asset.user.toLowerCase().includes(searchTerm.toLowerCase()) ||
      asset.ip.toLowerCase().includes(searchTerm.toLowerCase()) ||
      asset.mac.toLowerCase().includes(searchTerm.toLowerCase());

    const matchesFilter =
      filterType === 'all' ||
      (filterType === 'registered' && asset.isRegistered) ||
      (filterType === 'pending' && !asset.isRegistered) ||
      (filterType === 'laptop' && asset.type === 'laptop') ||
      (filterType === 'desktop' && asset.type === 'desktop');

    return matchesSearch && matchesFilter;
  }});

  const formatTime = (dateString) => {{
    if (!dateString) return 'N/A';
    const date = new Date(dateString);
    return date.toLocaleString();
  }};

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 text-white p-6">
      <div className="max-w-7xl mx-auto mb-8">
        <div className="flex items-center justify-between mb-6">
          <div>
            <h1 className="text-4xl font-bold bg-gradient-to-r from-blue-400 to-cyan-400 bg-clip-text text-transparent">
              Asset Registration Monitor
            </h1>
            <p className="text-slate-400 mt-2">Real-time tracking of staff desktop registrations</p>
          </div>

          <button
            onClick={{fetchAssets}}
            disabled={{loading}}
            className="flex items-center gap-2 px-6 py-3 bg-blue-600 hover:bg-blue-700 rounded-lg transition-colors disabled:opacity-50"
          >
            <RefreshCw className={{`w-5 h-5 ${{loading ? 'animate-spin' : ''}}`}} />
            Refresh
          </button>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-5 gap-4 mb-6">
          <div className="bg-slate-800 border border-slate-700 rounded-lg p-4">
            <div className="text-slate-400 text-sm mb-1">Total Assets</div>
            <div className="text-3xl font-bold text-white">{{stats.total}}</div>
          </div>

          <div className="bg-green-900/30 border border-green-700 rounded-lg p-4">
            <div className="text-green-400 text-sm mb-1 flex items-center gap-2">
              <CheckCircle className="w-4 h-4" />
              Registered
            </div>
            <div className="text-3xl font-bold text-green-400">{{stats.registered}}</div>
          </div>

          <div className="bg-orange-900/30 border border-orange-700 rounded-lg p-4">
            <div className="text-orange-400 text-sm mb-1 flex items-center gap-2">
              <Clock className="w-4 h-4" />
              Pending
            </div>
            <div className="text-3xl font-bold text-orange-400">{{stats.pending}}</div>
          </div>

          <div className="bg-blue-900/30 border border-blue-700 rounded-lg p-4">
            <div className="text-blue-400 text-sm mb-1 flex items-center gap-2">
              <Laptop className="w-4 h-4" />
              Laptops
            </div>
            <div className="text-3xl font-bold text-blue-400">{{stats.laptops}}</div>
          </div>

          <div className="bg-purple-900/30 border border-purple-700 rounded-lg p-4">
            <div className="text-purple-400 text-sm mb-1 flex items-center gap-2">
              <Monitor className="w-4 h-4" />
              Desktops
            </div>
            <div className="text-3xl font-bold text-purple-400">{{stats.desktops}}</div>
          </div>
        </div>

        <div className="bg-slate-800 border border-slate-700 rounded-lg p-4 mb-6">
          <div className="flex flex-col md:flex-row gap-4">
            <div className="flex-1 relative">
              <Search className="absolute left-3 top-3 w-5 h-5 text-slate-400" />
              <input
                type="text"
                placeholder="Search by name, user, IP, or MAC..."
                value={{searchTerm}}
                onChange={{(e) => setSearchTerm(e.target.value)}}
                className="w-full pl-10 pr-4 py-2 bg-slate-900 border border-slate-700 rounded-lg text-white placeholder-slate-500 focus:outline-none focus:border-blue-500"
              />
            </div>

            <div className="flex items-center gap-2">
              <Filter className="w-5 h-5 text-slate-400" />
              <select
                value={{filterType}}
                onChange={{(e) => setFilterType(e.target.value)}}
                className="px-4 py-2 bg-slate-900 border border-slate-700 rounded-lg text-white focus:outline-none focus:border-blue-500"
              >
                <option value="all">All Assets</option>
                <option value="registered">Registered</option>
                <option value="pending">Pending</option>
                <option value="laptop">Laptops</option>
                <option value="desktop">Desktops</option>
              </select>
            </div>
          </div>

          {{lastUpdate && (
            <div className="text-xs text-slate-500 mt-2">
              Last updated: {{lastUpdate.toLocaleTimeString()}}
            </div>
          )}}
        </div>

        <div className="bg-slate-800 border border-slate-700 rounded-lg overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead className="bg-slate-900 border-b border-slate-700">
                <tr>
                  <th className="px-4 py-3 text-left text-xs font-semibold text-slate-400 uppercase">Status</th>
                  <th className="px-4 py-3 text-left text-xs font-semibold text-slate-400 uppercase">Asset Tag</th>
                  <th className="px-4 py-3 text-left text-xs font-semibold text-slate-400 uppercase">Computer Name</th>
                  <th className="px-4 py-3 text-left text-xs font-semibold text-slate-400 uppercase">User</th>
                  <th className="px-4 py-3 text-left text-xs font-semibold text-slate-400 uppercase">Model</th>
                  <th className="px-4 py-3 text-left text-xs font-semibold text-slate-400 uppercase">Type</th>
                  <th className="px-4 py-3 text-left text-xs font-semibold text-slate-400 uppercase">IP Address</th>
                  <th className="px-4 py-3 text-left text-xs font-semibold text-slate-400 uppercase">MAC Address</th>
                  <th className="px-4 py-3 text-left text-xs font-semibold text-slate-400 uppercase">Last Updated</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-700">
                {{loading ? (
                  <tr>
                    <td colSpan="9" className="px-4 py-8 text-center text-slate-400">
                      <RefreshCw className="w-8 h-8 animate-spin mx-auto mb-2" />
                      Loading assets...
                    </td>
                  </tr>
                ) : filteredAssets.length === 0 ? (
                  <tr>
                    <td colSpan="9" className="px-4 py-8 text-center text-slate-400">
                      No assets found
                    </td>
                  </tr>
                ) : (
                  filteredAssets.map((asset) => (
                    <tr key={{asset.id}} className="hover:bg-slate-700/50 transition-colors">
                      <td className="px-4 py-3">
                        {{asset.isRegistered ? (
                          <div className="flex items-center gap-2 text-green-400">
                            <CheckCircle className="w-5 h-5" />
                            <span className="text-sm font-medium">Ready</span>
                          </div>
                        ) : (
                          <div className="flex items-center gap-2 text-orange-400">
                            <Clock className="w-5 h-5" />
                            <span className="text-sm font-medium">Pending</span>
                          </div>
                        )}}
                      </td>
                      <td className="px-4 py-3 text-sm font-mono text-cyan-400">{{asset.assetTag}}</td>
                      <td className="px-4 py-3 text-sm font-medium">{{asset.name}}</td>
                      <td className="px-4 py-3 text-sm">{{asset.user}}</td>
                      <td className="px-4 py-3 text-sm text-slate-300">{{asset.model}}</td>
                      <td className="px-4 py-3">
                        <span className={{`inline-flex items-center gap-1 px-2 py-1 rounded text-xs font-medium ${{
                          asset.type === 'laptop'
                            ? 'bg-blue-900/50 text-blue-400'
                            : 'bg-purple-900/50 text-purple-400'
                        }}`}}>
                          {{asset.type === 'laptop' ? <Laptop className="w-3 h-3" /> : <Monitor className="w-3 h-3" />}}
                          {{asset.type}}
                        </span>
                      </td>
                      <td className="px-4 py-3 text-sm font-mono text-slate-300">{{asset.ip}}</td>
                      <td className="px-4 py-3 text-sm font-mono text-slate-300">{{asset.mac}}</td>
                      <td className="px-4 py-3 text-xs text-slate-400">{{formatTime(asset.lastUpdated)}}</td>
                    </tr>
                  ))
                )}}
              </tbody>
            </table>
          </div>
        </div>

        <div className="text-center text-slate-500 text-sm mt-4">
          Showing {{filteredAssets.length}} of {{assets.length}} assets
        </div>
      </div>
    </div>
  );
}};

export default SnipeITMonitor;"""

    with open(f"{base_dir}/src/App.jsx", "w") as f:
        f.write(app_jsx)

    print_success("src/App.jsx created")

def create_dockerignore(base_dir):
    """Create .dockerignore"""
    print_info("Creating .dockerignore...")

    dockerignore = """node_modules
npm-debug.log
.git
.gitignore
README.md
.env
.DS_Store
"""

    with open(f"{base_dir}/.dockerignore", "w") as f:
        f.write(dockerignore)

    print_success(".dockerignore created")

def create_readme(base_dir):
    """Create README.md"""
    print_info("Creating README.md...")

    readme = """# Snipe-IT Asset Monitor

Real-time monitoring dashboard for tracking staff desktop registrations in Snipe-IT.

## Quick Start

### Using Docker Compose (Recommended)

```bash
# Build and start the container
docker-compose up -d

# View logs
docker-compose logs -f

# Stop the container
docker-compose down
```

Access the dashboard at: http://localhost:3000

### Manual Build

```bash
# Install dependencies
npm install

# Development mode
npm run dev

# Build for production
npm run build
```

## Configuration

Edit the API URL and Token in `src/App.jsx` or pass as environment variables.

## Features

- Real-time asset tracking
- Auto-refresh every 30 seconds
- Search and filter capabilities
- Registration status monitoring
- Device type categorization

## Requirements

- Docker & Docker Compose
- Or Node.js 18+ for manual installation
"""

    with open(f"{base_dir}/README.md", "w") as f:
        f.write(readme)

    print_success("README.md created")

def main():
    print_header("Snipe-IT Monitor - Automated Deployment")

    # Get user inputs
    print(f"{Colors.BOLD}Please provide the following information:{Colors.ENDC}\n")

    project_name = input(f"{Colors.OKCYAN}Project directory name [{Colors.ENDC}snipeit-monitor{Colors.OKCYAN}]: {Colors.ENDC}").strip() or "snipeit-monitor"

    default_url = "http://192.168.0.126:8000/api/v1"
    snipeit_url = input(f"{Colors.OKCYAN}Snipe-IT API URL [{Colors.ENDC}{default_url}{Colors.OKCYAN}]: {Colors.ENDC}").strip() or default_url

    snipeit_token = input(f"{Colors.OKCYAN}Snipe-IT API Token: {Colors.ENDC}").strip()

    if not snipeit_token:
        print_error("API Token is required!")
        sys.exit(1)

    # Get base directory
    base_dir = os.path.join(os.getcwd(), project_name)

    print_header("Creating Project Structure")

    # Create all files
    create_directory_structure(base_dir)
    create_package_json(base_dir)
    create_vite_config(base_dir)
    create_tailwind_config(base_dir)
    create_postcss_config(base_dir)
    create_index_html(base_dir)
    create_index_css(base_dir)
    create_main_jsx(base_dir)
    create_app_jsx(base_dir, snipeit_url, snipeit_token)
    create_dockerfile(base_dir)
    create_nginx_conf(base_dir)
    create_docker_compose(base_dir, snipeit_url, snipeit_token)
    create_dockerignore(base_dir)
    create_readme(base_dir)

    print_header("Installation Complete!")

    print_info("Next steps:")
    print(f"\n1. Change to project directory:")
    print(f"   {Colors.BOLD}cd {project_name}{Colors.ENDC}")

    print(f"\n2. Build and start with Docker Compose:")
    print(f"   {Colors.BOLD}docker-compose up -d{Colors.ENDC}")

    print(f"\n3. View logs:")
    print(f"   {Colors.BOLD}docker-compose logs -f{Colors.ENDC}")

    print(f"\n4. Access the dashboard:")
    print(f"   {Colors.BOLD}http://localhost:3000{Colors.ENDC}")

    print(f"\n{Colors.OKGREEN}✓ All files created successfully!{Colors.ENDC}\n")

if __name__ == "__main__":
    main()
