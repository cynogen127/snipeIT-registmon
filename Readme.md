# Snipe-IT Management Monitor v2.0

<div align="center">

![Version](https://img.shields.io/badge/version-2.0-blue.svg)
![Python](https://img.shields.io/badge/python-3.6+-green.svg)
![Docker](https://img.shields.io/badge/docker-required-blue.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)

**A modern, real-time dashboard for Snipe-IT asset and license management**
<img width="1919" height="993" alt="image" src="https://github.com/user-attachments/assets/455e704d-5705-48a9-a4f7-47f1563ec590" />
[Features](#-features) • [Quick Start](#-quick-start) • [Installation](#-installation) • [Screenshots](#-screenshots) • [Configuration](#%EF%B8%8F-configuration) • [Troubleshooting](#-troubleshooting)

</div>

---

## 🎯 Overview

Snipe-IT Management Monitor is a **100% self-contained deployment script** that creates a complete web-based monitoring dashboard for your Snipe-IT instance. Track hardware assets, manage software licenses, and monitor staff registrations - all with a beautiful, responsive interface.

### What Makes This Special?

- **🚀 One-Command Deployment** - Single Python script creates everything
- **🔄 Zero CORS Issues** - Built-in proxy server handles all API calls
- **📦 100% Self-Contained** - No external files or dependencies needed
- **🐳 Docker Ready** - Complete containerized deployment
- **🎨 Modern UI** - Beautiful Tailwind CSS interface with real-time updates

---

## ✨ Features

### Asset Management
- ✅ Real-time hardware asset tracking
- ✅ Automatic device type detection (Laptops, Desktops, UPS, Monitors, etc.)
- ✅ Staff registration monitoring with upload/download capabilities
- ✅ Advanced search and filtering
- ✅ Network information (IP/MAC addresses)
- ✅ Auto-refresh every 30 seconds

### License Management (NEW in v2.0!)
- ✅ Software license tracking and monitoring
- ✅ Seat availability and usage statistics
- ✅ Expiration date tracking with alerts
- ✅ Detailed license information (Product keys, costs, suppliers)
- ✅ Seat assignment tracking (users/assets)
- ✅ Visual usage indicators and progress bars

### Staff Monitoring
- ✅ Upload staff lists for tracking
- ✅ Automatic comparison with registered assets
- ✅ Download lists of unregistered staff
- ✅ Persistent storage across sessions
- ✅ Real-time registration statistics

---

## 🚀 Quick Start

### Prerequisites
- Python 3.6 or higher
- Docker and Docker Compose
- Access to a Snipe-IT instance with API token

### Installation

1. **Download the script:**
```bash
wget https://raw.githubusercontent.com/yourusername/snipeit-monitor/main/deploy.py
# OR
curl -O https://raw.githubusercontent.com/yourusername/snipeit-monitor/main/deploy.py
```

2. **Run the deployment script:**
```bash
python3 deploy.py
```

3. **Follow the prompts:**
```
Project directory name [snipeit-monitor]: my-monitor
Snipe-IT API URL [http://192.168.0.126:8000/api/v1]: https://your-snipeit.com/api/v1
Snipe-IT API Token: your_api_token_here
```

4. **Deploy with Docker:**
```bash
cd my-monitor
sudo docker-compose up -d --build
```

5. **Verify deployment:**
```bash
# Check proxy server health
curl http://localhost:3001/health

# Check if services are running
docker-compose ps
```

6. **Access the dashboard:**
```
Open your browser to: http://localhost:3000
```

---

## 📸 Screenshots

### Assets Dashboard
- View all hardware assets with status indicators
- Filter by type (Laptops, Desktops, UPS, etc.)
- Search by name, IP, MAC, or staff name
- Track registration status

### License Management
- Overview of all software licenses
- Seat availability and usage tracking
- Expiration date monitoring
- Detailed license information modal

### Staff Monitoring
- Upload staff lists for tracking
- Real-time comparison with registered assets
- Download lists of unregistered staff

---

## 🗂️ Project Structure

The deployment script creates the following structure:

```
snipeit-monitor/
├── docker-compose.yml          # Docker orchestration
├── Dockerfile                  # Container definition
├── package.json               # Frontend dependencies
├── vite.config.js             # Vite configuration
├── tailwind.config.js         # Tailwind CSS setup
├── postcss.config.js          # PostCSS configuration
├── index.html                 # Main HTML file
├── README.md                  # Project documentation
├── staff.txt.sample           # Sample staff list
├── server/
│   ├── server.js              # Express proxy server
│   └── package.json           # Server dependencies
├── src/
│   ├── main.jsx               # React entry point
│   ├── App.jsx                # Main application component
│   └── index.css              # Global styles
└── public/                    # Static assets
```

---

## ⚙️ Configuration

### Environment Variables

You can modify these in `docker-compose.yml`:

```yaml
environment:
  - SNIPEIT_API_URL=https://your-snipeit.com/api/v1
  - SNIPEIT_API_TOKEN=your_token_here
  - PORT=3001
```

### Port Configuration

Default ports:
- **Frontend Dashboard:** `3000` → `80` (container)
- **Proxy Server:** `3001`

To change ports, edit `docker-compose.yml`:

```yaml
ports:
  - "8080:80"      # Frontend on port 8080
  - "8081:3001"    # Proxy on port 8081
```

### Custom Fields

The application automatically detects Snipe-IT custom fields. If your custom field names differ, update the field detection in `src/App.jsx`:

```javascript
const staffName = getCustomField([
  'Staff Name',
  'staff name',
  '_snipeit_staff_name_25',
  // Add your custom field names here
]);
```

---

## 🔧 Troubleshooting

### Proxy Server Issues

**Problem:** Cannot connect to Snipe-IT API

```bash
# Check proxy server health
curl http://localhost:3001/health

# View proxy server logs
docker-compose logs -f snipeit-monitor

# Test direct API access
curl http://localhost:3001/api/hardware?limit=1
```

### No Assets/Licenses Showing

1. **Verify API Token:**
```bash
# Test API token directly
curl -H "Authorization: Bearer YOUR_TOKEN" \
     https://your-snipeit.com/api/v1/hardware?limit=1
```

2. **Check API URL Format:**
   - Should end with `/api/v1`
   - Example: `https://snipeit.example.com/api/v1`

3. **Review Browser Console:**
   - Open Developer Tools (F12)
   - Check Console tab for errors
   - Check Network tab for failed requests

### Docker Issues

```bash
# Restart containers
docker-compose restart

# Rebuild from scratch
docker-compose down
docker-compose up -d --build

# View all logs
docker-compose logs -f

# Check container status
docker-compose ps
```

### Staff List Not Persisting

Staff lists are saved to browser localStorage. If cleared:

1. Re-upload your `staff.txt` file
2. Data persists across browser sessions but not across different browsers/devices

---

## 📋 Staff List Format

Create a `staff.txt` file with one name per line:

```
John Doe
Jane Smith
Ahmad Abdullah
Sarah Johnson
Michael Chen
```

Upload via the "Upload Staff List" button in the Assets tab.

---

## 🔄 API Endpoints

The proxy server exposes these endpoints:

| Endpoint | Description |
|----------|-------------|
| `/api/hardware` | Get all hardware assets |
| `/api/licenses` | Get all software licenses |
| `/api/licenses/:id/seats` | Get seats for specific license |
| `/health` | Health check endpoint |

---

## 🚦 System Requirements

### Minimum
- **CPU:** 1 core
- **RAM:** 512 MB
- **Disk:** 500 MB
- **Network:** Access to Snipe-IT instance

### Recommended
- **CPU:** 2 cores
- **RAM:** 1 GB
- **Disk:** 1 GB
- **Network:** Low-latency connection to Snipe-IT

---

## 🛠️ Development

### Local Development (without Docker)

1. **Install dependencies:**
```bash
# Frontend
npm install

# Proxy server
cd server && npm install
```

2. **Set environment variables:**
```bash
export SNIPEIT_API_URL="https://your-snipeit.com/api/v1"
export SNIPEIT_API_TOKEN="your_token_here"
```

3. **Start development servers:**
```bash
# Terminal 1: Proxy server
cd server && npm start

# Terminal 2: Frontend
npm run dev
```

4. **Access:**
   - Frontend: `http://localhost:3000`
   - Proxy: `http://localhost:3001`

---

## 📊 Feature Roadmap

- [ ] Email notifications for expiring licenses
- [ ] Export reports to PDF/CSV
- [ ] Advanced analytics and charts
- [ ] Multi-tenant support
- [ ] Mobile app
- [ ] Webhook integrations

---

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

---

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 🙏 Acknowledgments

- Built with [React](https://reactjs.org/) and [Vite](https://vitejs.dev/)
- Styled with [Tailwind CSS](https://tailwindcss.com/)
- Icons by [Lucide](https://lucide.dev/)
- Integrates with [Snipe-IT](https://snipeitapp.com/)

---

## 📞 Support

- **Issues:** [GitHub Issues](https://github.com/yourusername/snipeit-monitor/issues)
- **Discussions:** [GitHub Discussions](https://github.com/yourusername/snipeit-monitor/discussions)
- **Email:** your.email@example.com

---

## 🌟 Star History

If you find this project useful, please consider giving it a star! ⭐

---

<div align="center">

**Made with ❤️ for the Snipe-IT Community**

[⬆ Back to Top](#snipe-it-management-monitor-v20)

</div>

