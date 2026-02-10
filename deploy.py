#!/usr/bin/env python3
"""
Snipe-IT Monitor v2.1
"""

import os
import sys
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

def create_directory_structure(base_dir):
    """Create project directory structure"""
    print_info("Creating directory structure...")
    directories = [base_dir, f"{base_dir}/src", f"{base_dir}/server", f"{base_dir}/public", f"{base_dir}/data"]
    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)
        print_success(f"Created: {directory}")

def create_proxy_server(base_dir, snipeit_url, snipeit_token):
    """Create Express proxy server with FIXED CORS"""
    print_info("Creating proxy server with FIXED CORS (server.js)...")

    server_js = """const express = require('express');
const cors = require('cors');
const fs = require('fs');
const path = require('path');
const {{ createProxyMiddleware }} = require('http-proxy-middleware');

const app = express();
const PORT = process.env.PORT || 3001;

const SNIPEIT_API_URL = process.env.SNIPEIT_API_URL || '{snipeit_url}';
const SNIPEIT_API_TOKEN = process.env.SNIPEIT_API_TOKEN || '{snipeit_token}';

// Path to store staff list (persists across browsers!)
const STAFF_LIST_FILE = path.join(__dirname, '../data/staff-list.json');

// Ensure data directory exists
const dataDir = path.join(__dirname, '../data');
if (!fs.existsSync(dataDir)) {{
  fs.mkdirSync(dataDir, {{ recursive: true }});
  console.log('📁 Created data directory');
}}

// FIXED: Enhanced CORS configuration
const corsOptions = {{
  origin: '*',
  methods: ['GET', 'POST', 'PUT', 'DELETE', 'PATCH', 'OPTIONS'],
  allowedHeaders: ['Content-Type', 'Authorization', 'Accept'],
  exposedHeaders: ['Content-Type'],
  credentials: true,
  preflightContinue: false,
  optionsSuccessStatus: 204
}};

app.use(cors(corsOptions));

// Handle preflight OPTIONS requests for all routes
app.options('*', cors(corsOptions));

// Parse JSON bodies BEFORE routes
app.use(express.json({{ limit: '50mb' }}));

// Additional CORS headers middleware
app.use((req, res, next) => {{
  res.header('Access-Control-Allow-Origin', '*');
  res.header('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, PATCH, OPTIONS');
  res.header('Access-Control-Allow-Headers', 'Content-Type, Authorization, Accept');
  res.header('Access-Control-Expose-Headers', 'Content-Type');

  // Handle OPTIONS method
  if (req.method === 'OPTIONS') {{
    res.sendStatus(204);
    return;
  }}
  next();
}});

app.get('/health', (req, res) => {{
  res.json({{
    status: 'ok',
    timestamp: new Date().toISOString(),
    snipeitUrl: SNIPEIT_API_URL,
    staffListExists: fs.existsSync(STAFF_LIST_FILE),
    cors: 'enabled'
  }});
}});

// GET staff list from server
app.get('/staff-list', (req, res) => {{
  try {{
    console.log('📥 GET /staff-list request received');

    if (fs.existsSync(STAFF_LIST_FILE)) {{
      const data = fs.readFileSync(STAFF_LIST_FILE, 'utf8');
      const staffData = JSON.parse(data);
      console.log(`✅ Loaded staff list: ${{staffData.names.length}} names`);

      res.setHeader('Content-Type', 'application/json');
      res.status(200).json(staffData);
    }} else {{
      console.log('ℹ️ No staff list file found');
      res.setHeader('Content-Type', 'application/json');
      res.status(200).json({{ names: [], timestamp: null }});
    }}
  }} catch (error) {{
    console.error('❌ Error reading staff list:', error.message);
    res.status(500).json({{ error: 'Failed to read staff list', message: error.message }});
  }}
}});

// POST/UPDATE staff list on server
app.post('/staff-list', (req, res) => {{
  try {{
    console.log('📥 POST /staff-list request received');
    const {{ names }} = req.body;

    if (!Array.isArray(names)) {{
      return res.status(400).json({{ error: 'Names must be an array' }});
    }}

    const staffData = {{
      names: names,
      timestamp: new Date().toISOString(),
      count: names.length
    }};

    fs.writeFileSync(STAFF_LIST_FILE, JSON.stringify(staffData, null, 2), 'utf8');
    console.log(`✅ Saved staff list: ${{names.length}} names to ${{STAFF_LIST_FILE}}`);

    res.setHeader('Content-Type', 'application/json');
    res.status(200).json({{
      success: true,
      count: names.length,
      timestamp: staffData.timestamp
    }});
  }} catch (error) {{
    console.error('❌ Error saving staff list:', error.message);
    res.status(500).json({{ error: 'Failed to save staff list', message: error.message }});
  }}
}});

// DELETE staff list from server - FIXED VERSION
app.delete('/staff-list', (req, res) => {{
  try {{
    console.log('📥 DELETE /staff-list request received');
    console.log('📂 Staff list file path:', STAFF_LIST_FILE);
    console.log('📂 File exists before delete:', fs.existsSync(STAFF_LIST_FILE));

    if (fs.existsSync(STAFF_LIST_FILE)) {{
      fs.unlinkSync(STAFF_LIST_FILE);
      console.log('✅ Deleted staff list file');
      console.log('📂 File exists after delete:', fs.existsSync(STAFF_LIST_FILE));
    }} else {{
      console.log('ℹ️ Staff list file does not exist');
    }}

    res.setHeader('Content-Type', 'application/json');
    res.status(200).json({{
      success: true,
      deleted: true,
      fileExists: fs.existsSync(STAFF_LIST_FILE)
    }});
  }} catch (error) {{
    console.error('❌ Error deleting staff list:', error.message);
    res.status(500).json({{ error: 'Failed to delete staff list', message: error.message }});
  }}
}});

const proxyOptions = {{
  target: SNIPEIT_API_URL.replace('/api/v1', ''),
  changeOrigin: true,
  pathRewrite: {{ '^/api': '/api/v1' }},
  onProxyReq: (proxyReq, req, res) => {{
    proxyReq.setHeader('Authorization', `Bearer ${{SNIPEIT_API_TOKEN}}`);
    proxyReq.setHeader('Accept', 'application/json');
    proxyReq.setHeader('Content-Type', 'application/json');
    proxyReq.removeHeader('if-none-match');
    proxyReq.removeHeader('if-modified-since');
    console.log(`[${{new Date().toISOString()}}] Proxying: ${{req.method}} ${{req.path}}`);
  }},
  onProxyRes: (proxyRes, req, res) => {{
    proxyRes.headers['Access-Control-Allow-Origin'] = '*';
    proxyRes.headers['Access-Control-Allow-Methods'] = 'GET, POST, PUT, DELETE, PATCH, OPTIONS';
    proxyRes.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization';
    proxyRes.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate';
    proxyRes.headers['Pragma'] = 'no-cache';
    proxyRes.headers['Expires'] = '0';
    console.log(`[${{new Date().toISOString()}}] Response: ${{proxyRes.statusCode}} for ${{req.path}}`);
  }},
  onError: (err, req, res) => {{
    console.error(`[${{new Date().toISOString()}}] Proxy Error:`, err.message);
    res.status(500).json({{ error: 'Proxy error', message: err.message }});
  }},
  logLevel: 'debug'
}};

app.use('/api', createProxyMiddleware(proxyOptions));

app.listen(PORT, '0.0.0.0', () => {{
  console.log('='.repeat(60));
  console.log('🚀 Snipe-IT Proxy Server Started');
  console.log('='.repeat(60));
  console.log(`Port: ${{PORT}}`);
  console.log(`Target API: ${{SNIPEIT_API_URL}}`);
  console.log(`Health Check: http://localhost:${{PORT}}/health`);
  console.log(`Staff List Storage: ${{STAFF_LIST_FILE}}`);
  console.log(`CORS: ENABLED (All origins allowed)`);
  console.log('='.repeat(60));
}});
""".format(snipeit_url=snipeit_url, snipeit_token=snipeit_token)

    with open(f"{base_dir}/server/server.js", "w") as f:
        f.write(server_js)
    print_success("server/server.js created with FIXED DELETE!")


def create_dockerfile(base_dir):
    """Create Dockerfile with data volume"""
    print_info("Creating Dockerfile...")

    dockerfile_content = """# Build stage for React app
FROM node:18-alpine AS frontend-build
WORKDIR /app
COPY package*.json ./
RUN npm install --legacy-peer-deps
COPY . .
RUN npm run build

# Final stage
FROM node:18-alpine
WORKDIR /app
RUN npm install -g serve
COPY server ./server
WORKDIR /app/server
RUN npm install --production
WORKDIR /app
COPY --from=frontend-build /app/dist ./dist

# Create data directory for persistent storage
RUN mkdir -p /app/data && chmod 777 /app/data

RUN echo '#!/bin/sh' > /app/start.sh && \\
    echo 'echo "Starting proxy server on port 3001..."' >> /app/start.sh && \\
    echo 'cd /app/server && node server.js &' >> /app/start.sh && \\
    echo 'sleep 2' >> /app/start.sh && \\
    echo 'echo "Starting frontend on port 80..."' >> /app/start.sh && \\
    echo 'serve -s /app/dist -l 80' >> /app/start.sh && \\
    chmod +x /app/start.sh

EXPOSE 80 3001
CMD ["/app/start.sh"]
"""

    with open(f"{base_dir}/Dockerfile", "w") as f:
        f.write(dockerfile_content)
    print_success("Dockerfile created")

def create_server_package_json(base_dir):
    """Create package.json for the proxy server"""
    print_info("Creating server/package.json...")

    server_package = """{
  "name": "snipeit-proxy-server",
  "version": "1.0.0",
  "description": "Proxy server to bypass CORS for Snipe-IT API",
  "main": "server.js",
  "scripts": {
    "start": "node server.js",
    "dev": "nodemon server.js"
  },
  "dependencies": {
    "express": "^4.18.2",
    "cors": "^2.8.5",
    "http-proxy-middleware": "^2.0.6"
  },
  "devDependencies": {
    "nodemon": "^3.0.1"
  }
}
"""

    with open(f"{base_dir}/server/package.json", "w") as f:
        f.write(server_package)
    print_success("server/package.json created")

def create_docker_compose(base_dir, snipeit_url, snipeit_token):
    """Create docker-compose.yml with persistent volume"""
    print_info("Creating docker-compose.yml with persistent volume...")

    docker_compose_content = """version: '3.8'

services:
  snipeit-monitor:
    build: .
    container_name: snipeit-monitor
    ports:
      - "3000:80"
      - "3001:3001"
    environment:
      - SNIPEIT_API_URL={url}
      - SNIPEIT_API_TOKEN={token}
      - PORT=3001
    volumes:
      - ./staff-data:/app/data
    restart: unless-stopped
    networks:
      - snipeit-network

networks:
  snipeit-network:
    driver: bridge

volumes:
  staff-data:
    driver: local
""".format(url=snipeit_url, token=snipeit_token)

    with open(f"{base_dir}/docker-compose.yml", "w") as f:
        f.write(docker_compose_content)
    print_success("docker-compose.yml created with persistent volume!")

def create_package_json(base_dir):
    """Create package.json for React app"""
    print_info("Creating package.json...")

    package_json_content = """{
  "name": "snipeit-monitor",
  "version": "2.1.0",
  "type": "module",
  "scripts": {
    "dev": "vite",
    "build": "vite build",
    "preview": "vite preview"
  },
  "dependencies": {
    "react": "^18.3.1",
    "react-dom": "^18.3.1",
    "lucide-react": "^0.263.1"
  },
  "devDependencies": {
    "@vitejs/plugin-react": "^4.3.4",
    "vite": "^5.4.11",
    "tailwindcss": "^3.4.17",
    "postcss": "^8.4.49",
    "autoprefixer": "^10.4.20"
  }
}
"""

    with open(f"{base_dir}/package.json", "w") as f:
        f.write(package_json_content)
    print_success("package.json created")

def create_vite_config(base_dir):
    """Create vite.config.js"""
    print_info("Creating vite.config.js...")

    vite_config = """import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    host: '0.0.0.0',
    port: 3000,
    proxy: {
      '/api': {
        target: 'http://localhost:3001',
        changeOrigin: true,
        secure: false
      },
      '/staff-list': {
        target: 'http://localhost:3001',
        changeOrigin: true,
        secure: false
      }
    }
  }
})
"""

    with open(f"{base_dir}/vite.config.js", "w") as f:
        f.write(vite_config)
    print_success("vite.config.js created")

def create_tailwind_config(base_dir):
    """Create tailwind.config.js"""
    print_info("Creating tailwind.config.js...")

    tailwind_config = """/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,ts,jsx,tsx}"],
  theme: { extend: {} },
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
    <title>Master Sofa Asset Management Monitoring</title> <i className="fa fa-chart-line"></i>
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
    'Ubuntu', 'Cantarell', 'Fira Sans', 'Droid Sans', 'Helvetica Neue', sans-serif;
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


def create_app_jsx(base_dir):
    """Create src/App.jsx with FIXED clear staff list"""
    print_info("Creating src/App.jsx with FIXED clear staff list...")

    app_jsx = """import React, { useState, useEffect } from 'react';
import { RefreshCw, CheckCircle, Clock, Laptop, Monitor, Search, Filter, Upload, UserCheck, UserX, Users, Download, Zap, Key, Calendar, AlertCircle, X, FileText, ChevronRight , Printer } from 'lucide-react';

const SnipeITMonitor = () => {
  const [assets, setAssets] = useState([]);
  const [licenses, setLicenses] = useState([]);
  const [printers, setPrinters] = useState([]);
  const [loadingPrinters, setLoadingPrinters] = useState(false);
  const [printerSearchTerm, setPrinterSearchTerm] = useState('');
  const [selectedLicense, setSelectedLicense] = useState(null);
  const [licenseSeats, setLicenseSeats] = useState([]);
  const [loading, setLoading] = useState(true);
  const [loadingLicenses, setLoadingLicenses] = useState(false);
  const [loadingSeats, setLoadingSeats] = useState(false);
  const [lastUpdate, setLastUpdate] = useState(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [licenseSearchTerm, setLicenseSearchTerm] = useState('');
  const [filterType, setFilterType] = useState('all');
  const [activeTab, setActiveTab] = useState('assets');
  const [staffList, setStaffList] = useState([]);
  const [registeredStaff, setRegisteredStaff] = useState([]);
  const [notRegisteredStaff, setNotRegisteredStaff] = useState([]);
  const [error, setError] = useState(null);
  const [stats, setStats] = useState({
    total: 0,
    registered: 0,
    pending: 0,
    laptops: 0,
    desktops: 0,
    ups: 0,
    other: 0,
    staffRegistered: 0,
    staffNotRegistered: 0
  });
  const [licenseStats, setLicenseStats] = useState({
    total: 0,
    available: 0,
    inUse: 0,
    expiringSoon: 0
  });
  const [printerStats, setPrinterStats] = useState({
    total: 0,
    deployed: 0,
    available: 0,
    lowToner: 0
  });

  const API_BASE_URL = window.location.hostname === 'localhost'
    ? 'http://localhost:3001/api'
    : `http://${window.location.hostname}:3001/api`;

  const STAFF_LIST_URL = window.location.hostname === 'localhost'
    ? 'http://localhost:3001/staff-list'
    : `http://${window.location.hostname}:3001/staff-list`;

  const parseTonerStatus = (notes) => {
    if (!notes) return null;
    const tonerRegex = /(BLACK|CYAN|MAGENTA|YELLOW):\s*(-?[0-9.]+)%/gi;
    const toners = {};
    let match;
    while ((match = tonerRegex.exec(notes)) !== null) {
      toners[match[1].toUpperCase()] = parseFloat(match[2]);
    }
    return Object.keys(toners).length > 0 ? toners : null;
  };

  const getTonerBarColor = (percentage, color) => {
    if (percentage < 20) return 'bg-red-500';
    if (percentage < 40) return 'bg-orange-500';
    switch(color) {
      case 'BLACK': return 'bg-gray-700';
      case 'CYAN': return 'bg-cyan-500';
      case 'MAGENTA': return 'bg-pink-500';
      case 'YELLOW': return 'bg-yellow-500';
      default: return 'bg-blue-500';
    }
  };

  const extractTotalPages = (notes) => {
    if (!notes) return 'N/A';
    const match = notes.match(/Total Pages:\s*([0-9,]+)/i);
    return match ? match[1] : 'N/A';
  };

  // Load staff list from SERVER on component mount
  const loadStaffListFromServer = async () => {
    try {
      console.log('🔄 Loading staff list from server...');
      const response = await fetch(STAFF_LIST_URL);

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();

      if (data.names && Array.isArray(data.names) && data.names.length > 0) {
        setStaffList(data.names);
        console.log('✅ Staff list loaded from server:', data.names.length, 'names');
        console.log('📅 Last saved:', data.timestamp);
      } else {
        console.log('ℹ️ No staff list found on server');
        setStaffList([]);
      }
    } catch (error) {
      console.error('❌ Error loading staff list from server:', error);
      setStaffList([]);
    }
  };

  // Save staff list to SERVER
  const saveStaffListToServer = async (names) => {
    try {
      console.log('💾 Saving staff list to server...');
      const response = await fetch(STAFF_LIST_URL, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ names: names })
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      console.log('✅ Staff list saved to server:', data.count, 'names');
      return true;
    } catch (error) {
      console.error('❌ Error saving staff list to server:', error);
      return false;
    }
  };

  // FIXED: Delete staff list from SERVER
  const deleteStaffListFromServer = async () => {
    try {
      console.log('🗑️ Deleting staff list from server...');
      const response = await fetch(STAFF_LIST_URL, {
        method: 'DELETE',
        headers: {
          'Content-Type': 'application/json'
        }
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      console.log('✅ Server response:', data);
      console.log('✅ Staff list deleted from server');
      return true;
    } catch (error) {
      console.error('❌ Error deleting staff list from server:', error);
      return false;
    }
  };

  // File upload handler
  const handleFileUpload = async (event) => {
    const file = event.target.files[0];
    if (file) {
      const reader = new FileReader();
      reader.onload = async (e) => {
        const text = e.target.result;
        const names = text.split('\\n')
          .map(name => name.trim())
          .filter(name => name.length > 0);

        const saved = await saveStaffListToServer(names);

        if (saved) {
          setStaffList(names);
          alert(`✅ Successfully saved ${names.length} staff members to server!\\n\\nThis list is now available across ALL browsers and devices!`);
        } else {
          alert('⚠️ Error: Could not save staff list to server. Please check the console and try again.');
        }
      };
      reader.onerror = (error) => {
        console.error('❌ Error reading file:', error);
        alert('❌ Error reading file. Please try again.');
      };
      reader.readAsText(file);
    }
  };

  const downloadNotRegistered = () => {
    const csv = notRegisteredStaff.join('\\n');
    const blob = new Blob([csv], { type: 'text/plain' });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `not-registered-staff-${new Date().toISOString().split('T')[0]}.txt`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    window.URL.revokeObjectURL(url);
  };

  // FIXED: Clear staff list - properly deletes from server
  const clearStaffList = async () => {
    if (window.confirm('⚠️ Are you sure you want to clear the staff list from the SERVER?\\n\\nThis will:\\n• Delete the file from the server\\n• Affect ALL users and browsers\\n• Cannot be undone')) {
      try {
        // Step 1: Delete from server FIRST
        console.log('Step 1: Deleting from server...');
        const deleted = await deleteStaffListFromServer();

        if (deleted) {
          // Step 2: Clear all local state
          console.log('Step 2: Clearing local state...');
          setStaffList([]);
          setNotRegisteredStaff([]);
          setRegisteredStaff([]);
          setStats(prev => ({
            ...prev,
            staffRegistered: 0,
            staffNotRegistered: 0
          }));

          console.log('✅ Staff list cleared successfully!');
          alert('✅ Staff list cleared successfully from server!\\n\\nRefresh the page to confirm.');
        } else {
          console.error('❌ Server deletion failed');
          alert('⚠️ Error: Could not delete staff list from server.\\n\\nPlease check the server logs.');
        }
      } catch (error) {
        console.error('❌ Error in clearStaffList:', error);
        alert('⚠️ Error: ' + error.message);
      }
    }
  };

  const detectDeviceType = (asset) => {
    const category = (asset.category?.name || '').toLowerCase();
    const name = (asset.name || '').toLowerCase();
    const model = (asset.model?.name || '').toLowerCase();

    if (category.includes('ups') || name.includes('ups') || model.includes('ups') || name.includes('power')) {
      return 'ups';
    }

    if (category.includes('laptop') || category.includes('notebook')) {
      return 'laptop';
    }

    if (category.includes('desktop') || category.includes('computer') || category.includes('pc')) {
      return 'desktop';
    }

    if (category.includes('monitor') || category.includes('display') || category.includes('screen')) {
      return 'monitor';
    }

    if (category.includes('server')) {
      return 'server';
    }

    if (category.includes('printer')) {
      return 'printer';
    }

    return 'other';
  };

  const fetchLicenses = async () => {
    try {
      setLoadingLicenses(true);
      setError(null);

      console.log('Fetching licenses from proxy:', `${API_BASE_URL}/licenses?limit=500`);

      const response = await fetch(`${API_BASE_URL}/licenses?limit=500`, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json'
        }
      });

      console.log('Licenses response status:', response.status);

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();

      let licensesData = [];
      if (data && data.rows && Array.isArray(data.rows)) {
        licensesData = data.rows;
      } else if (Array.isArray(data)) {
        licensesData = data;
      } else {
        console.error('Unexpected licenses data structure:', data);
        throw new Error('Invalid licenses API response structure');
      }

      console.log('Found licenses:', licensesData.length);

      const processedLicenses = licensesData.map(license => {
        const totalSeats = license.seats || 0;
        const availableSeats = license.available_seats_count || license.availableSeats || 0;
        const usedSeats = totalSeats - availableSeats;

        const expirationDate = license.expiration_date?.date || license.expiration_date;
        const isExpiringSoon = expirationDate ?
          (new Date(expirationDate) - new Date()) / (1000 * 60 * 60 * 24) <= 30 : false;

        return {
          id: license.id,
          name: license.name || 'Unknown License',
          productKey: license.product_key || license.serial || 'N/A',
          manufacturer: license.manufacturer?.name || 'N/A',
          category: license.category?.name || 'N/A',
          totalSeats: totalSeats,
          availableSeats: availableSeats,
          usedSeats: usedSeats,
          expirationDate: expirationDate,
          isExpiringSoon: isExpiringSoon,
          purchaseDate: license.purchase_date?.date || license.purchase_date,
          purchaseCost: license.purchase_cost || 'N/A',
          orderNumber: license.order_number || 'N/A',
          notes: license.notes || '',
          supplier: license.supplier?.name || 'N/A',
          maintainer: license.maintainer || 'N/A',
          terminated: license.terminated_date !== null
        };
      });

      setLicenses(processedLicenses);

      const available = processedLicenses.reduce((sum, lic) => sum + lic.availableSeats, 0);
      const inUse = processedLicenses.reduce((sum, lic) => sum + lic.usedSeats, 0);
      const expiringSoon = processedLicenses.filter(lic => lic.isExpiringSoon && !lic.terminated).length;

      setLicenseStats({
        total: processedLicenses.length,
        available: available,
        inUse: inUse,
        expiringSoon: expiringSoon
      });

    } catch (error) {
      console.error('Error fetching licenses:', error);
      setError(`Failed to fetch licenses: ${error.message}`);
    } finally {
      setLoadingLicenses(false);
    }
  };

  const fetchLicenseSeats = async (licenseId) => {
    try {
      setLoadingSeats(true);
      console.log(`Fetching seats for license ${licenseId}`);

      const response = await fetch(`${API_BASE_URL}/licenses/${licenseId}/seats`, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json'
        }
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();

      let seatsData = [];
      if (data && data.rows && Array.isArray(data.rows)) {
        seatsData = data.rows;
      } else if (Array.isArray(data)) {
        seatsData = data;
      }

      console.log('Found seats:', seatsData.length);
      setLicenseSeats(seatsData);

    } catch (error) {
      console.error('Error fetching license seats:', error);
      setLicenseSeats([]);
    } finally {
      setLoadingSeats(false);
    }
  };

  const fetchPrinters = async () => {
    try {
      setLoadingPrinters(true);
      setError(null);
      const response = await fetch(`${API_BASE_URL}/hardware?limit=500`, {
        method: 'GET',
        headers: { 'Content-Type': 'application/json' }
      });
      if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
      const data = await response.json();
      let assetsData = [];
      // Handle different API response formats
      if (data && data.rows && Array.isArray(data.rows)) {
        assetsData = data.rows;
      } else if (data && data.data && Array.isArray(data.data)) {
        assetsData = data.data;
      } else if (Array.isArray(data)) {
        assetsData = data;
      } else if (typeof data === 'object' && data !== null) {
        const firstArray = Object.values(data).find(val => Array.isArray(val));
        assetsData = firstArray || [];
      }


const printerAssets = assetsData.filter(asset => {
        const category = (asset.category?.name || '').toLowerCase();
        const name = (asset.name || '').toLowerCase();
        return category.includes('printer') ||
               category.includes('mfp') ||
               category.includes('office equipment') ||
               name.includes('printer');
      });
      const processedPrinters = printerAssets.map(printer => {
        const customFields = printer.custom_fields || {};
        const getCustomField = (possibleNames) => {
          // Handle both direct values and nested objects
          for (const fieldName of possibleNames) {
            if (customFields[fieldName]) {
              const field = customFields[fieldName];

              // If it's a string, return it directly
              if (typeof field === 'string') return field;

              // If it's an object, check multiple possible value keys
              if (typeof field === 'object' && field !== null) {
                if (field.value) return field.value;
                if (field.field) return field.field;
                if (field._value) return field._value;
                if (field.text) return field.text;
              }
            }
          }
          return 'N/A';
        };
        const ipAddress = getCustomField(['IP Address', 'ip address', '_snipeit_ip_address_1', '_snipeit_ip_address_2', 'ip_address']);
        const notes = printer.notes || '';
        const tonerStatus = parseTonerStatus(notes);
        let lowestToner = 100;
        if (tonerStatus) {
          lowestToner = Math.min(...Object.values(tonerStatus));
        }
        return {
          id: printer.id,
          name: printer.name || 'Unknown',
          assetTag: printer.asset_tag || 'N/A',
          model: printer.model?.name || 'Unknown Model',
          status: printer.status_label?.name || 'Unknown',
          ip: ipAddress,
          notes: notes,
          tonerStatus: tonerStatus,
          lowestToner: lowestToner,
          isDeployed: printer.status_label?.status_meta === 'deployed',
          totalPages: extractTotalPages(notes)
        };
      });
      setPrinters(processedPrinters);
      const deployed = processedPrinters.filter(p => p.isDeployed).length;
      const lowToner = processedPrinters.filter(p => p.lowestToner < 20).length;
      setPrinterStats({
        total: processedPrinters.length,
        deployed: deployed,
        available: processedPrinters.length - deployed,
        lowToner: lowToner
      });
    } catch (error) {
      console.error('Error fetching printers:', error);
      setError(`Failed to fetch printers: ${error.message}`);
    } finally {
      setLoadingPrinters(false);
    }
  };

    const handleViewLicenseDetails = (license) => {
    setSelectedLicense(license);
    fetchLicenseSeats(license.id);
  };

  const closeLicenseDetails = () => {
    setSelectedLicense(null);
    setLicenseSeats([]);
  };

  const fetchAssets = async () => {
    try {
      setLoading(true);
      setError(null);

      console.log('Fetching from proxy:', `${API_BASE_URL}/hardware?limit=500`);

      const response = await fetch(`${API_BASE_URL}/hardware?limit=500`, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json'
        }
      });

      console.log('Response status:', response.status);

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();

      let assetsData = [];
      // Handle different API response formats
      if (data && data.rows && Array.isArray(data.rows)) {
        assetsData = data.rows;
      } else if (data && data.data && Array.isArray(data.data)) {
        assetsData = data.data;
      } else if (Array.isArray(data)) {
        assetsData = data;
      } else if (typeof data === 'object' && data !== null) {
        const firstArray = Object.values(data).find(val => Array.isArray(val));
        assetsData = firstArray || [];
      } else {
        console.error('Unexpected data structure:', data);
        throw new Error('Invalid API response structure');
      }

      console.log('Found assets:', assetsData.length);

      if (assetsData.length > 0) {
        console.log('Sample asset:', assetsData[0]);
        console.log('Sample asset custom_fields:', assetsData[0].custom_fields);
      }

      const processedAssets = assetsData.map(asset => {
        const customFields = asset.custom_fields || {};

        const getCustomField = (possibleNames) => {
          // Handle both direct values and nested objects
          for (const fieldName of possibleNames) {
            if (customFields[fieldName]) {
              const field = customFields[fieldName];

              // If it's a string, return it directly
              if (typeof field === 'string') return field;

              // If it's an object, check multiple possible value keys
              if (typeof field === 'object' && field !== null) {
                if (field.value) return field.value;
                if (field.field) return field.field;
                if (field._value) return field._value;
                if (field.text) return field.text;
              }
            }
          }
          return 'N/A';
        };

        const staffName = getCustomField([
          'Staff Name',
          'staff name',
          '_snipeit_staff_name_25',
          '_snipeit_staff_name_1',
          '_snipeit_staff_name_2',
          '_snipeit_staff_name_3',
          '_snipeit_staff_name_4',
          '_snipeit_staff_name_5',
          'staff_name',
        ]);

        const ipAddress = getCustomField([
          'IP Address',
          'ip address',
          '_snipeit_ip_address_1',
          '_snipeit_ip_address_2',
          'ip_address'
        ]);

        const macAddress = getCustomField([
          'MAC Address',
          'mac address',
          '_snipeit_mac_address_2',
          '_snipeit_mac_address_1',
          'mac_address'
        ]);

        const windowsUser = getCustomField([
          'Windows Username',
          'windows username',
          '_snipeit_windows_username_7',
          '_snipeit_windows_username_1',
          'windows_username'
        ]);

        if (asset.id === assetsData[0].id) {
          console.log('=== CUSTOM FIELD DEBUG ===');
          console.log('Asset ID:', asset.id);
          console.log('All custom field keys:', Object.keys(customFields));
          console.log('Extracted Staff Name:', staffName);
          console.log('Extracted IP:', ipAddress);
          console.log('Extracted MAC:', macAddress);
          console.log('Extracted User:', windowsUser);
          console.log('========================');
        }

        const deviceType = detectDeviceType(asset);

        if (asset.name?.toLowerCase().includes('ups')) {
          console.log('=== UPS DETECTION DEBUG ===');
          console.log('Asset Name:', asset.name);
          console.log('Category:', asset.category?.name);
          console.log('Model:', asset.model?.name);
          console.log('Detected Type:', deviceType);
          console.log('========================');
        }

        return {
          id: asset.id,
          name: asset.name || 'Unknown',
          assetTag: asset.asset_tag || 'N/A',
          serial: asset.serial || 'N/A',
          model: asset.model?.name || 'Unknown Model',
          category: asset.category?.name || 'Unknown',
          status: asset.status_label?.name || 'Unknown',
          ip: ipAddress,
          mac: macAddress,
          user: windowsUser,
          staffName: staffName,
          lastUpdated: asset.updated_at?.datetime || asset.created_at?.datetime,
          isRegistered: asset.status_label?.status_meta === 'deployed' ||
                       asset.status_label?.status_meta === 'deployable' ||
                       asset.status_label?.name === 'Ready to Deploy',
          type: deviceType
        };
      });

      console.log('Processed assets:', processedAssets);

      setAssets(processedAssets);

      const registeredNames = processedAssets
        .map(a => a.staffName)
        .filter(name => name && name !== 'N/A' && name.trim() !== '');

      console.log('Registered staff names found:', registeredNames);
      setRegisteredStaff(registeredNames);

      const registered = processedAssets.filter(a => a.isRegistered).length;
      const laptops = processedAssets.filter(a => a.type === 'laptop').length;
      const desktops = processedAssets.filter(a => a.type === 'desktop').length;
      const ups = processedAssets.filter(a => a.type === 'ups').length;
      const other = processedAssets.filter(a => !['laptop', 'desktop', 'ups'].includes(a.type)).length;

      setStats({
        total: processedAssets.length,
        registered: registered,
        pending: processedAssets.length - registered,
        laptops: laptops,
        desktops: desktops,
        ups: ups,
        other: other,
        staffRegistered: registeredNames.length,
        staffNotRegistered: 0
      });

      setLastUpdate(new Date());
    } catch (error) {
      console.error('Error fetching assets:', error);
      setError(`Failed to fetch assets: ${error.message}`);
      alert(`Failed to fetch assets: ${error.message}\\n\\nCheck:\\n1. Proxy server running (port 3001)\\n2. Snipe-IT API accessible\\n3. Docker logs: docker-compose logs -f`);
    } finally {
      setLoading(false);
    }
  };

  // Load staff list from SERVER on mount
  useEffect(() => {
    console.log('🔄 Component mounted - loading from SERVER...');
    loadStaffListFromServer();
  }, []);

  useEffect(() => {
    fetchAssets();
    const interval = setInterval(fetchAssets, 30000);
    return () => clearInterval(interval);
  }, []);

  useEffect(() => {
    if (activeTab === 'licenses' && licenses.length === 0) {
      fetchLicenses();
    }
  }, [activeTab]);
  useEffect(() => { if (activeTab === 'printers' && printers.length === 0) fetchPrinters(); }, [activeTab]);

  useEffect(() => {
    if (staffList.length > 0) {
      const notRegistered = staffList.filter(staffName =>
        !registeredStaff.some(regName =>
          regName.toLowerCase().trim() === staffName.toLowerCase().trim()
        )
      );
      setNotRegisteredStaff(notRegistered);

      setStats(prev => ({
        ...prev,
        staffNotRegistered: notRegistered.length
      }));

      console.log('📊 Staff comparison:');
      console.log('  - Total in list:', staffList.length);
      console.log('  - Registered:', registeredStaff.length);
      console.log('  - Not registered:', notRegistered.length);
    } else {
      // If staff list is empty, clear the not registered list
      setNotRegisteredStaff([]);
      setStats(prev => ({
        ...prev,
        staffNotRegistered: 0
      }));
    }
  }, [staffList, registeredStaff]);

  const filteredAssets = assets.filter(asset => {
    const matchesSearch =
      asset.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
      asset.user.toLowerCase().includes(searchTerm.toLowerCase()) ||
      asset.staffName.toLowerCase().includes(searchTerm.toLowerCase()) ||
      asset.ip.toLowerCase().includes(searchTerm.toLowerCase()) ||
      asset.mac.toLowerCase().includes(searchTerm.toLowerCase());

    const matchesFilter =
      filterType === 'all' ||
      (filterType === 'registered' && asset.isRegistered) ||
      (filterType === 'pending' && !asset.isRegistered) ||
      (filterType === 'laptop' && asset.type === 'laptop') ||
      (filterType === 'desktop' && asset.type === 'desktop') ||
      (filterType === 'ups' && asset.type === 'ups') ||
      (filterType === 'other' && !['laptop', 'desktop', 'ups'].includes(asset.type));

    return matchesSearch && matchesFilter;
  });

  const filteredLicenses = licenses.filter(license => {
    const matchesSearch =
      license.name.toLowerCase().includes(licenseSearchTerm.toLowerCase()) ||
      license.manufacturer.toLowerCase().includes(licenseSearchTerm.toLowerCase()) ||
      license.category.toLowerCase().includes(licenseSearchTerm.toLowerCase()) ||
      license.productKey.toLowerCase().includes(licenseSearchTerm.toLowerCase());

    return matchesSearch;
  });

  const filteredPrinters = printers.filter(printer =>
    printer.name.toLowerCase().includes(printerSearchTerm.toLowerCase()) ||
    printer.model.toLowerCase().includes(printerSearchTerm.toLowerCase()) ||
    printer.ip.toLowerCase().includes(printerSearchTerm.toLowerCase()) ||
    printer.assetTag.toLowerCase().includes(printerSearchTerm.toLowerCase())
  );

  const formatTime = (dateString) => {
    if (!dateString) return 'N/A';
    const date = new Date(dateString);
    return date.toLocaleString();
  };

  const formatDate = (dateString) => {
    if (!dateString) return 'N/A';
    const date = new Date(dateString);
    return date.toLocaleDateString();
  };

  const getTypeDisplay = (type) => {
    switch(type) {
      case 'laptop':
        return {
          icon: <Laptop className="w-3 h-3" />,
          label: 'Laptop',
          className: 'bg-blue-900/50 text-blue-400'
        };
      case 'desktop':
        return {
          icon: <Monitor className="w-3 h-3" />,
          label: 'Desktop',
          className: 'bg-purple-900/50 text-purple-400'
        };
      case 'ups':
        return {
          icon: <Zap className="w-3 h-3" />,
          label: 'UPS',
          className: 'bg-yellow-900/50 text-yellow-400'
        };
      case 'monitor':
        return {
          icon: <Monitor className="w-3 h-3" />,
          label: 'Monitor',
          className: 'bg-cyan-900/50 text-cyan-400'
        };
      case 'server':
        return {
          icon: <Monitor className="w-3 h-3" />,
          label: 'Server',
          className: 'bg-red-900/50 text-red-400'
        };
      default:
        return {
          icon: <Monitor className="w-3 h-3" />,
          label: 'Other',
          className: 'bg-gray-900/50 text-gray-400'
        };
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 text-white p-6">
      <div className="max-w-7xl mx-auto mb-8">
        <div className="flex items-center justify-between mb-6">
          <div>
            <h1 className="text-4xl font-bold bg-gradient-to-r from-blue-400 to-cyan-400 bg-clip-text text-transparent">
              Snipe-IT Management Monitor
            </h1>
            <p className="text-slate-400 mt-2">Real-time tracking of assets and licenses</p>
          </div>

          <div className="flex gap-3">
            {activeTab === 'assets' && (
              <>
                <label className="flex items-center gap-2 px-6 py-3 bg-purple-600 hover:bg-purple-700 rounded-lg transition-colors cursor-pointer">
                  <Upload className="w-5 h-5" />
                  Upload Staff List
                  {staffList.length > 0 && (
                    <span className="ml-1 px-2 py-0.5 bg-purple-800 rounded-full text-xs">
                      {staffList.length}
                    </span>
                  )}
                  <input
                    type="file"
                    accept=".txt"
                    onChange={handleFileUpload}
                    className="hidden"
                  />
                </label>

                {staffList.length > 0 && (
                  <button
                    onClick={clearStaffList}
                    className="flex items-center gap-2 px-6 py-3 bg-red-600 hover:bg-red-700 rounded-lg transition-colors"
                    title="Clear saved staff list from server"
                  >
                    <UserX className="w-5 h-5" />
                    Clear List
                  </button>
                )}
              </>
            )}

            <button
              onClick={activeTab === 'assets' ? fetchAssets : activeTab === 'licenses' ? fetchLicenses : fetchPrinters}
              disabled={loading || loadingLicenses || loadingPrinters}
              className="flex items-center gap-2 px-6 py-3 bg-blue-600 hover:bg-blue-700 rounded-lg transition-colors disabled:opacity-50"
            >
              <RefreshCw className={`w-5 h-5 ${(loading || loadingLicenses || loadingPrinters) ? 'animate-spin' : ''}`} />
              Refresh
            </button>
          </div>
        </div>

        {/* Tab Navigation */}
        <div className="flex gap-2 mb-6 border-b border-slate-700">
          <button
            onClick={() => setActiveTab('assets')}
            className={`px-6 py-3 font-semibold transition-colors border-b-2 ${
              activeTab === 'assets'
                ? 'border-blue-500 text-blue-400'
                : 'border-transparent text-slate-400 hover:text-slate-300'
            }`}
          >
            <div className="flex items-center gap-2">
              <Laptop className="w-5 h-5" />
              Assets
              <span className="px-2 py-0.5 bg-slate-700 rounded-full text-xs">
                {stats.total}
              </span>
            </div>
          </button>
          <button
            onClick={() => setActiveTab('licenses')}
            className={`px-6 py-3 font-semibold transition-colors border-b-2 ${
              activeTab === 'licenses'
                ? 'border-blue-500 text-blue-400'
                : 'border-transparent text-slate-400 hover:text-slate-300'
            }`}
          >
            <div className="flex items-center gap-2">
              <Key className="w-5 h-5" />
              Licenses
              <span className="px-2 py-0.5 bg-slate-700 rounded-full text-xs">
                {licenseStats.total}
              </span>
            </div>
          </button>
          <button
            onClick={() => setActiveTab('printers')}
            className={`px-6 py-3 font-semibold transition-colors border-b-2 ${
              activeTab === 'printers'
                ? 'border-blue-500 text-blue-400'
                : 'border-transparent text-slate-400 hover:text-slate-300'
            }`}
          >
            <div className="flex items-center gap-2">
              <Printer className="w-5 h-5" />
              Printers
              <span className="px-2 py-0.5 bg-slate-700 rounded-full text-xs">
                {printerStats.total}
              </span>
            </div>
          </button>
        </div>

        {error && (
          <div className="bg-red-900/30 border border-red-700 rounded-lg p-4 mb-6 text-red-300">
            <p className="font-semibold">Error:</p>
            <p>{error}</p>
          </div>
        )}

        {/* Assets View */}
        {activeTab === 'assets' && (
          <>
            <div className="grid grid-cols-1 md:grid-cols-4 lg:grid-cols-8 gap-4 mb-6">
              <div className="bg-slate-800 border border-slate-700 rounded-lg p-4">
                <div className="text-slate-400 text-sm mb-1">Total Assets</div>
                <div className="text-3xl font-bold text-white">{stats.total}</div>
              </div>

              <div className="bg-green-900/30 border border-green-700 rounded-lg p-4">
                <div className="text-green-400 text-sm mb-1 flex items-center gap-2">
                  <CheckCircle className="w-4 h-4" />
                  Registered
                </div>
                <div className="text-3xl font-bold text-green-400">{stats.registered}</div>
              </div>

              <div className="bg-orange-900/30 border border-orange-700 rounded-lg p-4">
                <div className="text-orange-400 text-sm mb-1 flex items-center gap-2">
                  <Clock className="w-4 h-4" />
                  Pending
                </div>
                <div className="text-3xl font-bold text-orange-400">{stats.pending}</div>
              </div>

              <div className="bg-blue-900/30 border border-blue-700 rounded-lg p-4">
                <div className="text-blue-400 text-sm mb-1 flex items-center gap-2">
                  <Laptop className="w-4 h-4" />
                  Laptops
                </div>
                <div className="text-3xl font-bold text-blue-400">{stats.laptops}</div>
              </div>

              <div className="bg-purple-900/30 border border-purple-700 rounded-lg p-4">
                <div className="text-purple-400 text-sm mb-1 flex items-center gap-2">
                  <Monitor className="w-4 h-4" />
                  Desktops
                </div>
                <div className="text-3xl font-bold text-purple-400">{stats.desktops}</div>
              </div>

              <div className="bg-yellow-900/30 border border-yellow-700 rounded-lg p-4">
                <div className="text-yellow-400 text-sm mb-1 flex items-center gap-2">
                  <Zap className="w-4 h-4" />
                  UPS
                </div>
                <div className="text-3xl font-bold text-yellow-400">{stats.ups}</div>
              </div>
              <div className="bg-emerald-900/30 border border-emerald-700 rounded-lg p-4">
                <div className="text-emerald-400 text-sm mb-1 flex items-center gap-2">
                  <UserCheck className="w-4 h-4" />
                  Staff Done
                </div>
                <div className="text-3xl font-bold text-emerald-400">{stats.staffRegistered}</div>
              </div>

              <div className="bg-red-900/30 border border-red-700 rounded-lg p-4">
                <div className="text-red-400 text-sm mb-1 flex items-center gap-2">
                  <UserX className="w-4 h-4" />
                  Staff Pending
                </div>
                <div className="text-3xl font-bold text-red-400">{stats.staffNotRegistered}</div>
              </div>
            </div>

            {staffList.length > 0 && (
              <div className="bg-slate-800 border border-slate-700 rounded-lg p-4 mb-6">
                <div className="flex items-center justify-between mb-3">
                  <div className="flex items-center gap-2">
                    <Users className="w-5 h-5 text-cyan-400" />
                    <h2 className="text-lg font-semibold text-cyan-400">Staff Not Registered Yet</h2>
                    <span className="text-sm text-slate-400">
                      ({notRegisteredStaff.length} / {staffList.length} remaining)
                    </span>
                  </div>
                  {notRegisteredStaff.length > 0 && (
                    <button
                      onClick={downloadNotRegistered}
                      className="flex items-center gap-2 px-4 py-2 bg-cyan-600 hover:bg-cyan-700 rounded-lg text-sm transition-colors"
                    >
                      <Download className="w-4 h-4" />
                      Download List
                    </button>
                  )}
                </div>
                {notRegisteredStaff.length > 0 ? (
                  <div className="flex flex-wrap gap-2">
                    {notRegisteredStaff.map((name, idx) => (
                      <span key={idx} className="px-3 py-1 bg-red-900/30 border border-red-700 rounded text-red-400 text-sm">
                        {name}
                      </span>
                    ))}
                  </div>
                ) : (
                  <div className="text-green-400 flex items-center gap-2">
                    <CheckCircle className="w-5 h-5" />
                    All staff have registered!
                  </div>
                )}
              </div>
            )}

            <div className="bg-slate-800 border border-slate-700 rounded-lg p-4 mb-6">
              <div className="flex flex-col md:flex-row gap-4">
                <div className="flex-1 relative">
                  <Search className="absolute left-3 top-3 w-5 h-5 text-slate-400" />
                  <input
                    type="text"
                    placeholder="Search by name, staff name, user, IP, or MAC..."
                    value={searchTerm}
                    onChange={(e) => setSearchTerm(e.target.value)}
                    className="w-full pl-10 pr-4 py-2 bg-slate-900 border border-slate-700 rounded-lg text-white placeholder-slate-500 focus:outline-none focus:border-blue-500"
                  />
                </div>

                <div className="flex items-center gap-2">
                  <Filter className="w-5 h-5 text-slate-400" />
                  <select
                    value={filterType}
                    onChange={(e) => setFilterType(e.target.value)}
                    className="px-4 py-2 bg-slate-900 border border-slate-700 rounded-lg text-white focus:outline-none focus:border-blue-500"
                  >
                    <option value="all">All Assets</option>
                    <option value="registered">Registered</option>
                    <option value="pending">Pending</option>
                    <option value="laptop">Laptops</option>
                    <option value="desktop">Desktops</option>
                    <option value="ups">UPS Devices</option>
                    <option value="other">Other Equipment</option>
                  </select>
                </div>
              </div>

              {lastUpdate && (
                <div className="text-xs text-slate-500 mt-2">
                  Last updated: {lastUpdate.toLocaleTimeString()}
                </div>
              )}
            </div>

            <div className="bg-slate-800 border border-slate-700 rounded-lg overflow-hidden">
              <div className="overflow-x-auto">
                <table className="w-full">
                  <thead className="bg-slate-900 border-b border-slate-700">
                    <tr>
                      <th className="px-4 py-3 text-left text-xs font-semibold text-slate-400 uppercase">Status</th>
                      <th className="px-4 py-3 text-left text-xs font-semibold text-slate-400 uppercase">Asset Tag</th>
                      <th className="px-4 py-3 text-left text-xs font-semibold text-slate-400 uppercase">Computer Name</th>
                      <th className="px-4 py-3 text-left text-xs font-semibold text-slate-400 uppercase">Staff Name</th>
                      <th className="px-4 py-3 text-left text-xs font-semibold text-slate-400 uppercase">User</th>
                      <th className="px-4 py-3 text-left text-xs font-semibold text-slate-400 uppercase">Model</th>
                      <th className="px-4 py-3 text-left text-xs font-semibold text-slate-400 uppercase">Type</th>
                      <th className="px-4 py-3 text-left text-xs font-semibold text-slate-400 uppercase">IP Address</th>
                      <th className="px-4 py-3 text-left text-xs font-semibold text-slate-400 uppercase">MAC Address</th>
                      <th className="px-4 py-3 text-left text-xs font-semibold text-slate-400 uppercase">Last Updated</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-700">
                    {loading ? (
                      <tr>
                        <td colSpan="10" className="px-4 py-8 text-center text-slate-400">
                          <RefreshCw className="w-8 h-8 animate-spin mx-auto mb-2" />
                          Loading assets...
                        </td>
                      </tr>
                    ) : filteredAssets.length === 0 ? (
                      <tr>
                        <td colSpan="10" className="px-4 py-8 text-center text-slate-400">
                          {assets.length === 0 ? 'No assets found in Snipe-IT' : 'No assets match your search/filter'}
                        </td>
                      </tr>
                    ) : (
                      filteredAssets.map((asset) => {
                        const typeDisplay = getTypeDisplay(asset.type);
                        return (
                          <tr key={asset.id} className="hover:bg-slate-700/50 transition-colors">
                            <td className="px-4 py-3">
                              {asset.isRegistered ? (
                                <div className="flex items-center gap-2 text-green-400">
                                  <CheckCircle className="w-5 h-5" />
                                  <span className="text-sm font-medium">Ready</span>
                                </div>
                              ) : (
                                <div className="flex items-center gap-2 text-orange-400">
                                  <Clock className="w-5 h-5" />
                                  <span className="text-sm font-medium">Pending</span>
                                </div>
                              )}
                            </td>
                            <td className="px-4 py-3 text-sm font-mono text-cyan-400">{asset.assetTag}</td>
                            <td className="px-4 py-3 text-sm font-medium">{asset.name}</td>
                            <td className="px-4 py-3 text-sm font-semibold text-cyan-300">{asset.staffName}</td>
                            <td className="px-4 py-3 text-sm">{asset.user}</td>
                            <td className="px-4 py-3 text-sm text-slate-300">{asset.model}</td>
                            <td className="px-4 py-3">
                              <span className={`inline-flex items-center gap-1 px-2 py-1 rounded text-xs font-medium ${typeDisplay.className}`}>
                                {typeDisplay.icon}
                                {typeDisplay.label}
                              </span>
                            </td>
                            <td className="px-4 py-3 text-sm font-mono text-slate-300">{asset.ip}</td>
                            <td className="px-4 py-3 text-sm font-mono text-slate-300">{asset.mac}</td>
                            <td className="px-4 py-3 text-xs text-slate-400">{formatTime(asset.lastUpdated)}</td>
                          </tr>
                        );
                      })
                    )}
                  </tbody>
                </table>
              </div>
            </div>

            <div className="text-center text-slate-500 text-sm mt-4">
              Showing {filteredAssets.length} of {assets.length} assets
            </div>
          </>
        )}

        {/* Licenses View */}
        {activeTab === 'licenses' && (
          <>
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
              <div className="bg-slate-800 border border-slate-700 rounded-lg p-4">
                <div className="text-slate-400 text-sm mb-1 flex items-center gap-2">
                  <Key className="w-4 h-4" />
                  Total Licenses
                </div>
                <div className="text-3xl font-bold text-white">{licenseStats.total}</div>
              </div>

              <div className="bg-green-900/30 border border-green-700 rounded-lg p-4">
                <div className="text-green-400 text-sm mb-1 flex items-center gap-2">
                  <CheckCircle className="w-4 h-4" />
                  Available Seats
                </div>
                <div className="text-3xl font-bold text-green-400">{licenseStats.available}</div>
              </div>

              <div className="bg-blue-900/30 border border-blue-700 rounded-lg p-4">
                <div className="text-blue-400 text-sm mb-1 flex items-center gap-2">
                  <Users className="w-4 h-4" />
                  Seats In Use
                </div>
                <div className="text-3xl font-bold text-blue-400">{licenseStats.inUse}</div>
              </div>

              <div className="bg-orange-900/30 border border-orange-700 rounded-lg p-4">
                <div className="text-orange-400 text-sm mb-1 flex items-center gap-2">
                  <AlertCircle className="w-4 h-4" />
                  Expiring Soon
                </div>
                <div className="text-3xl font-bold text-orange-400">{licenseStats.expiringSoon}</div>
              </div>
            </div>

            <div className="bg-slate-800 border border-slate-700 rounded-lg p-4 mb-6">
              <div className="relative">
                <Search className="absolute left-3 top-3 w-5 h-5 text-slate-400" />
                <input
                  type="text"
                  placeholder="Search licenses by name, manufacturer, category, or product key..."
                  value={licenseSearchTerm}
                  onChange={(e) => setLicenseSearchTerm(e.target.value)}
                  className="w-full pl-10 pr-4 py-2 bg-slate-900 border border-slate-700 rounded-lg text-white placeholder-slate-500 focus:outline-none focus:border-blue-500"
                />
              </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {loadingLicenses ? (
                <div className="col-span-full flex flex-col items-center justify-center py-12">
                  <RefreshCw className="w-12 h-12 animate-spin text-blue-400 mb-4" />
                  <p className="text-slate-400">Loading licenses...</p>
                </div>
              ) : filteredLicenses.length === 0 ? (
                <div className="col-span-full text-center py-12 text-slate-400">
                  {licenses.length === 0 ? 'No licenses found in Snipe-IT' : 'No licenses match your search'}
                </div>
              ) : (
                filteredLicenses.map((license) => (
                  <div
                    key={license.id}
                    className="bg-slate-800 border border-slate-700 rounded-lg p-5 hover:border-blue-500 transition-colors cursor-pointer"
                    onClick={() => handleViewLicenseDetails(license)}
                  >
                    <div className="flex items-start justify-between mb-3">
                      <div className="flex-1">
                        <h3 className="text-lg font-semibold text-white mb-1">{license.name}</h3>
                        <p className="text-sm text-slate-400">{license.manufacturer}</p>
                      </div>
                      <ChevronRight className="w-5 h-5 text-slate-400" />
                    </div>

                    <div className="space-y-2 mb-4">
                      <div className="flex items-center justify-between text-sm">
                        <span className="text-slate-400">Category:</span>
                        <span className="text-white">{license.category}</span>
                      </div>
                      <div className="flex items-center justify-between text-sm">
                        <span className="text-slate-400">Total Seats:</span>
                        <span className="text-white font-semibold">{license.totalSeats}</span>
                      </div>
                    </div>

                    <div className="grid grid-cols-2 gap-2 mb-4">
                      <div className="bg-green-900/30 border border-green-700 rounded p-2">
                        <div className="text-xs text-green-400 mb-1">Available</div>
                        <div className="text-xl font-bold text-green-400">{license.availableSeats}</div>
                      </div>
                      <div className="bg-blue-900/30 border border-blue-700 rounded p-2">
                        <div className="text-xs text-blue-400 mb-1">In Use</div>
                        <div className="text-xl font-bold text-blue-400">{license.usedSeats}</div>
                      </div>
                    </div>

                    {license.expirationDate && (
                      <div className={`flex items-center gap-2 text-xs p-2 rounded ${
                        license.isExpiringSoon
                          ? 'bg-orange-900/30 border border-orange-700 text-orange-400'
                          : 'bg-slate-700 text-slate-300'
                      }`}>
                        <Calendar className="w-3 h-3" />
                        <span>Expires: {formatDate(license.expirationDate)}</span>
                      </div>
                    )}

                    {license.terminated && (
                      <div className="flex items-center gap-2 text-xs p-2 rounded bg-red-900/30 border border-red-700 text-red-400 mt-2">
                        <AlertCircle className="w-3 h-3" />
                        <span>Terminated</span>
                      </div>
                    )}
                  </div>
                ))
              )}
            </div>

            <div className="text-center text-slate-500 text-sm mt-4">
                          <div className="text-center text-slate-500 text-sm mt-4">
              Showing {filteredLicenses.length} of {licenses.length} licenses
            </div>
          </>
        )}

        {/* Printers View */}
        {activeTab === 'printers' && (
          <>
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
              <div className="bg-slate-800 border border-slate-700 rounded-lg p-4">
                <div className="text-slate-400 text-sm mb-1 flex items-center gap-2">
                  <Printer className="w-4 h-4" />
                  Total Printers
                </div>
                <div className="text-3xl font-bold text-white">{printerStats.total}</div>
              </div>

              <div className="bg-green-900/30 border border-green-700 rounded-lg p-4">
                <div className="text-green-400 text-sm mb-1 flex items-center gap-2">
                  <CheckCircle className="w-4 h-4" />
                  Deployed
                </div>
                <div className="text-3xl font-bold text-green-400">{printerStats.deployed}</div>
              </div>

              <div className="bg-blue-900/30 border border-blue-700 rounded-lg p-4">
                <div className="text-blue-400 text-sm mb-1 flex items-center gap-2">
                  <Laptop className="w-4 h-4" />
                  Available
                </div>
                <div className="text-3xl font-bold text-blue-400">{printerStats.available}</div>
              </div>

              <div className="bg-orange-900/30 border border-orange-700 rounded-lg p-4">
                <div className="text-orange-400 text-sm mb-1 flex items-center gap-2">
                  <AlertCircle className="w-4 h-4" />
                  Low Toner
                </div>
                <div className="text-3xl font-bold text-orange-400">{printerStats.lowToner}</div>
              </div>
            </div>

            <div className="bg-slate-800 border border-slate-700 rounded-lg p-4 mb-6">
              <div className="relative">
                <Search className="absolute left-3 top-3 w-5 h-5 text-slate-400" />
                <input
                  type="text"
                  placeholder="Search printers by name, model, IP, or asset tag..."
                  value={printerSearchTerm}
                  onChange={(e) => setPrinterSearchTerm(e.target.value)}
                  className="w-full pl-10 pr-4 py-2 bg-slate-900 border border-slate-700 rounded-lg text-white placeholder-slate-500 focus:outline-none focus:border-blue-500"
                />
              </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {loadingPrinters ? (
                <div className="col-span-full flex flex-col items-center justify-center py-12">
                  <RefreshCw className="w-12 h-12 animate-spin text-blue-400 mb-4" />
                  <p className="text-slate-400">Loading printers...</p>
                </div>
              ) : filteredPrinters.length === 0 ? (
                <div className="col-span-full text-center py-12 text-slate-400">
                  {printers.length === 0 ? 'No printers found in Snipe-IT' : 'No printers match your search'}
                </div>
              ) : (
                filteredPrinters.map((printer) => (
                  <div
                    key={printer.id}
                    className="bg-slate-800 border border-slate-700 rounded-lg p-5 hover:border-blue-500 transition-colors"
                  >
                    <h3 className="text-lg font-semibold text-white mb-2">{printer.name}</h3>
                    <div className="space-y-1 text-sm">
                      <p className="text-slate-400">Asset: {printer.assetTag}</p>
                      <p className="text-slate-300">Model: {printer.model}</p>
                      <p className="text-slate-300">IP: {printer.ip}</p>
                      <p className="text-slate-300">Status: {printer.status}</p>
                    </div>
                    {printer.tonerStatus && Object.keys(printer.tonerStatus).length > 0 && (
                      <div className="mt-3 space-y-2">
                        {Object.entries(printer.tonerStatus).map(([color, percentage]) => (
                          <div key={color}>
                            <div className="flex justify-between text-xs mb-1">
                              <span className="text-slate-400">{color}:</span>
                              <span className={percentage < 20 ? 'text-red-400' : 'text-slate-300'}>{percentage.toFixed(1)}%</span>
                            </div>
                            <div className="w-full bg-slate-700 rounded h-1.5">
                              <div className={percentage < 20 ? 'bg-red-500' : 'bg-green-500'} style={{width: `${percentage}%`}}></div>
                            </div>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                ))
              )}
            </div>

            <div className="text-center text-slate-500 text-sm mt-4">
              Showing {filteredPrinters.length} of {printers.length} printers
            </div>
          </>
        )}
            </div>
          </>
        )}
      </div>

      {/* License Details Modal */}
      {selectedLicense && (
        <div className="fixed inset-0 bg-black/70 flex items-center justify-center p-4 z-50" onClick={closeLicenseDetails}>
          <div className="bg-slate-800 border border-slate-700 rounded-lg max-w-4xl w-full max-h-[90vh] overflow-y-auto" onClick={(e) => e.stopPropagation()}>
            <div className="sticky top-0 bg-slate-900 border-b border-slate-700 p-6 flex items-center justify-between">
              <div>
                <h2 className="text-2xl font-bold text-white">{selectedLicense.name}</h2>
                <p className="text-slate-400 mt-1">{selectedLicense.manufacturer}</p>
              </div>
              <button
                onClick={closeLicenseDetails}
                className="p-2 hover:bg-slate-700 rounded-lg transition-colors"
              >
                <X className="w-6 h-6 text-slate-400" />
              </button>
            </div>

            <div className="p-6">
              {/* License Information */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-6">
                <div>
                  <h3 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
                    <FileText className="w-5 h-5" />
                    License Details
                  </h3>
                  <div className="space-y-3">
                    <div>
                      <div className="text-xs text-slate-400 mb-1">Product Key</div>
                      <div className="text-sm font-mono text-white bg-slate-900 p-2 rounded border border-slate-700">
                        {selectedLicense.productKey}
                      </div>
                    </div>
                    <div>
                      <div className="text-xs text-slate-400 mb-1">Category</div>
                      <div className="text-sm text-white">{selectedLicense.category}</div>
                    </div>
                    <div>
                      <div className="text-xs text-slate-400 mb-1">Supplier</div>
                      <div className="text-sm text-white">{selectedLicense.supplier}</div>
                    </div>
                    <div>
                      <div className="text-xs text-slate-400 mb-1">Order Number</div>
                      <div className="text-sm text-white">{selectedLicense.orderNumber}</div>
                    </div>
                  </div>
                </div>

                <div>
                  <h3 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
                    <Calendar className="w-5 h-5" />
                    Dates & Costs
                  </h3>
                  <div className="space-y-3">
                    <div>
                      <div className="text-xs text-slate-400 mb-1">Purchase Date</div>
                      <div className="text-sm text-white">{formatDate(selectedLicense.purchaseDate)}</div>
                    </div>
                    <div>
                      <div className="text-xs text-slate-400 mb-1">Expiration Date</div>
                      <div className={`text-sm ${selectedLicense.isExpiringSoon ? 'text-orange-400 font-semibold' : 'text-white'}`}>
                        {formatDate(selectedLicense.expirationDate)}
                        {selectedLicense.isExpiringSoon && ' (Expiring Soon!)'}
                      </div>
                    </div>
                    <div>
                      <div className="text-xs text-slate-400 mb-1">Purchase Cost</div>
                      <div className="text-sm text-white">{selectedLicense.purchaseCost}</div>
                    </div>
                  </div>
                </div>
              </div>

              {/* Seat Usage */}
              <div className="mb-6">
                <h3 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
                  <Users className="w-5 h-5" />
                  Seat Usage
                </h3>
                <div className="grid grid-cols-3 gap-4">
                  <div className="bg-slate-900 border border-slate-700 rounded-lg p-4">
                    <div className="text-slate-400 text-sm mb-1">Total Seats</div>
                    <div className="text-2xl font-bold text-white">{selectedLicense.totalSeats}</div>
                  </div>
                  <div className="bg-green-900/30 border border-green-700 rounded-lg p-4">
                    <div className="text-green-400 text-sm mb-1">Available</div>
                    <div className="text-2xl font-bold text-green-400">{selectedLicense.availableSeats}</div>
                  </div>
                  <div className="bg-blue-900/30 border border-blue-700 rounded-lg p-4">
                    <div className="text-blue-400 text-sm mb-1">In Use</div>
                    <div className="text-2xl font-bold text-blue-400">{selectedLicense.usedSeats}</div>
                  </div>
                </div>

                {/* Progress Bar */}
                <div className="mt-4">
                  <div className="w-full bg-slate-700 rounded-full h-3 overflow-hidden">
                    <div
                      className="bg-blue-500 h-full transition-all duration-300"
                      style={{ width: `${(selectedLicense.usedSeats / selectedLicense.totalSeats) * 100}%` }}
                    ></div>
                  </div>
                  <div className="text-xs text-slate-400 mt-1 text-center">
                    {selectedLicense.usedSeats} / {selectedLicense.totalSeats} seats used
                    ({Math.round((selectedLicense.usedSeats / selectedLicense.totalSeats) * 100)}%)
                  </div>
                </div>
              </div>

              {/* Assigned Seats */}
              <div>
                <h3 className="text-lg font-semibold text-white mb-4">Assigned To</h3>
                {loadingSeats ? (
                  <div className="flex items-center justify-center py-8">
                    <RefreshCw className="w-6 h-6 animate-spin text-blue-400" />
                  </div>
                ) : licenseSeats.length === 0 ? (
                  <div className="text-center py-8 text-slate-400">
                    No seats assigned yet
                  </div>
                ) : (
                  <div className="bg-slate-900 border border-slate-700 rounded-lg overflow-hidden">
                    <table className="w-full">
                      <thead className="bg-slate-800 border-b border-slate-700">
                        <tr>
                          <th className="px-4 py-3 text-left text-xs font-semibold text-slate-400 uppercase">User/Asset</th>
                          <th className="px-4 py-3 text-left text-xs font-semibold text-slate-400 uppercase">Type</th>
                          <th className="px-4 py-3 text-left text-xs font-semibold text-slate-400 uppercase">Assigned Date</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-slate-700">
                        {licenseSeats.map((seat, index) => (
                          <tr key={index} className="hover:bg-slate-700/50">
                            <td className="px-4 py-3 text-sm text-white">
                              {seat.assigned_user?.name || seat.assigned_asset?.name || 'N/A'}
                            </td>
                            <td className="px-4 py-3 text-sm text-slate-400">
                              {seat.assigned_user ? 'User' : seat.assigned_asset ? 'Asset' : 'N/A'}
                            </td>
                            <td className="px-4 py-3 text-sm text-slate-400">
                              {formatDate(seat.created_at?.datetime || seat.created_at)}
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                )}
              </div>

              {/* Notes */}
              {selectedLicense.notes && (
                <div className="mt-6">
                  <h3 className="text-lg font-semibold text-white mb-2">Notes</h3>
                  <div className="bg-slate-900 border border-slate-700 rounded-lg p-4 text-sm text-slate-300">
                    {selectedLicense.notes}
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default SnipeITMonitor;
"""

    with open(f"{base_dir}/src/App.jsx", "w") as f:
        f.write(app_jsx)
    print_success("src/App.jsx created with Assets, Licenses AND Printers!")

def create_dockerignore(base_dir):
    """Create .dockerignore"""
    print_info("Creating .dockerignore...")

    dockerignore = """node_modules
npm-debug.log
.git
.gitignore
.env
.DS_Store
dist
.vscode
*.log
data/staff-list.json
"""

    with open(f"{base_dir}/.dockerignore", "w") as f:
        f.write(dockerignore)
    print_success(".dockerignore created")

def create_readme(base_dir):
    """Create README.md"""
    print_info("Creating README.md...")

    readme = """# Snipe-IT Management Monitor v2.1

## 🎉 NEW in v2.1 - FIXED Clear Staff List!
- ✅ **CLEAR LIST NOW WORKS!** - Properly deletes from server
- ✅ No more "ghost data" after refresh
- ✅ Confirmed deletion with better logging
- ✅ Staff list properly persists across browsers

## Features
- ✅ **LICENSE MANAGEMENT** - View and track software licenses
- ✅ **SERVER-SIDE PERSISTENCE** - Data saved to server (works across ALL browsers!)
- ✅ **FIXED CORS** - No more CORS errors!
- ✅ License seat usage and expiration tracking
- ✅ Asset tracking with staff registration monitoring
- ✅ Real-time updates every 30 seconds
- ✅ Docker deployment with persistent volume
- ✅ Printer list and toner status - need to run printer.py script using cronjob 

## Quick Start
```bash
python3 deploy_final_FIXED.py
cd snipeit-monitor
sudo docker-compose up -d --build
```

## Access
- Dashboard: http://localhost:3000
- Health Check: http://localhost:3001/health
- Staff List API: http://localhost:3001/staff-list

## Testing Clear Staff List
```bash
# Upload a staff list via the UI
# Click "Clear List"
# Refresh the page - list should be GONE!

# Check server logs
docker-compose logs -f | grep "DELETE /staff-list"

# Verify file deletion
docker exec -it snipeit-monitor ls -la /app/data/
```

## Troubleshooting
```bash
# Check logs
docker-compose logs -f

# Test CORS
curl http://localhost:3001/health

# Check staff list
curl http://localhost:3001/staff-list

# Manual delete test
curl -X DELETE http://localhost:3001/staff-list
```
"""

    with open(f"{base_dir}/README.md", "w") as f:
        f.write(readme)
    print_success("README.md created")

def create_sample_staff_file(base_dir):
    """Create sample staff.txt"""
    print_info("Creating staff.txt.sample...")

    sample_staff = """John Doe
Jane Smith
Ahmad Abdullah
Sarah Johnson
Michael Chen
"""

    with open(f"{base_dir}/staff.txt.sample", "w") as f:
        f.write(sample_staff)
    print_success("staff.txt.sample created")

def main():
    print_header("Snipe-IT Monitor v2.1 - CLEAR LIST FIXED!")

    print(f"{Colors.BOLD}🎉 What's Fixed:{Colors.ENDC}")
    print(f"{Colors.OKGREEN}  ✓ Clear Staff List Now Works Properly!{Colors.ENDC}")
    print(f"{Colors.OKGREEN}  ✓ No More Ghost Data After Refresh{Colors.ENDC}")
    print(f"{Colors.OKGREEN}  ✓ Better Deletion Confirmation{Colors.ENDC}")
    print(f"{Colors.OKGREEN}  ✓ Enhanced Server Logging{Colors.ENDC}")
    print()

    project_name = input(f"{Colors.OKCYAN}Project directory name [{Colors.ENDC}snipeit-monitor{Colors.OKCYAN}]: {Colors.ENDC}").strip() or "snipeit-monitor"

    default_url = "http://192.168.0.66:8000/api/v1"
    snipeit_url = input(f"{Colors.OKCYAN}Snipe-IT API URL [{Colors.ENDC}{default_url}{Colors.OKCYAN}]: {Colors.ENDC}").strip() or default_url

    snipeit_token = input(f"{Colors.OKCYAN}Snipe-IT API Token: {Colors.ENDC}").strip()

    if not snipeit_token:
        print_error("API Token is required!")
        sys.exit(1)

    base_dir = os.path.join(os.getcwd(), project_name)

    print_header("Creating Project")

    create_directory_structure(base_dir)
    create_package_json(base_dir)
    create_server_package_json(base_dir)
    create_proxy_server(base_dir, snipeit_url, snipeit_token)
    create_vite_config(base_dir)
    create_tailwind_config(base_dir)
    create_postcss_config(base_dir)
    create_index_html(base_dir)
    create_index_css(base_dir)
    create_main_jsx(base_dir)
    create_app_jsx(base_dir)
    create_dockerfile(base_dir)
    create_docker_compose(base_dir, snipeit_url, snipeit_token)
    create_dockerignore(base_dir)
    create_readme(base_dir)
    create_sample_staff_file(base_dir)

    print_header("Installation Complete!")

    print(f"\n{Colors.BOLD}Next steps:{Colors.ENDC}")
    print(f"\n1. {Colors.OKCYAN}cd {project_name}{Colors.ENDC}")
    print(f"\n2. {Colors.OKCYAN}sudo docker-compose up -d --build{Colors.ENDC}")
    print(f"\n3. {Colors.OKCYAN}http://localhost:3000{Colors.ENDC}")
    print(f"\n{Colors.OKGREEN}✓ v2.1 - CLEAR STAFF LIST NOW WORKS!{Colors.ENDC}")
    print(f"\n{Colors.WARNING}📌 Test it: Upload list → Clear → Refresh → GONE!{Colors.ENDC}\n")

if __name__ == "__main__":
    main()
