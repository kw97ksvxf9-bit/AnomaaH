# Local Development Server Setup - Complete

## 🚀 Services Running

Your complete local development environment is now running with all microservices and the APK download server.

### Frontend & UI
- **Admin Dashboard**: http://localhost:9000
- **APK Download Center**: http://localhost:8750

### API Services  
- **API Gateway**: http://localhost:8000
- **Auth Service**: http://localhost:8600
- **Booking Service**: http://localhost:8100
- **Payment Service**: http://localhost:8200
- **Tracking Service**: http://localhost:8300
- **Notification Service**: http://localhost:8400
- **Review Service**: http://localhost:8700
- **Order Service**: http://localhost:8500
- **Rider Status Service**: http://localhost:8800
- **Assignment Service**: http://localhost:8900

### Database
- **PostgreSQL**: localhost:5432
  - User: postgres
  - Password: postgres
  - Database: delivery

---

## 📱 APK Download Server

### Access the Download Page
```
http://localhost:8750/
```

### Available APK Files
- **Anomaah Rider App** (9.45 MB)
  - Status: Debug Build
  - Download URL: `/download/anomaah-rider-app.apk`

### API Endpoints
```
GET /api/files              - List available APK files
GET /download/{filename}    - Download APK file
GET /health                 - Health check
GET /                       - Download page UI
```

### Health Check
```bash
curl http://localhost:8750/health
# Response: {"status": "healthy"}
```

---

## 📥 Download Instructions

### Via Browser
1. Open http://localhost:8750/
2. Click the download button
3. File saves as `anomaah-rider-app.apk`

### Via API (Programmatic)
```bash
# Get file list
curl http://localhost:8750/api/files

# Download APK
curl -O http://localhost:8750/download/anomaah-rider-app.apk
```

### Via curl
```bash
curl -O http://localhost:8750/download/anomaah-rider-app.apk
```

---

## 🔧 Docker Compose Commands

### View all logs
```bash
docker-compose logs -f
```

### View downloads server logs
```bash
docker-compose logs -f downloads-server
```

### Stop all services
```bash
docker-compose down
```

### Restart services
```bash
docker-compose restart
```

### Remove everything (including data)
```bash
docker-compose down -v
```

---

## 📋 System Requirements for APK Installation

- Android 8.0 or higher
- Minimum 50 MB free storage
- Active internet connection
- Allow installation from unknown sources (in Android settings)

---

## 🐳 Docker Container Status

To check status of all services:
```bash
docker-compose ps
```

To check if downloads server is healthy:
```bash
docker ps | grep downloads-server
curl http://localhost:8750/health
```

---

## 📂 APK File Location

The APK file is stored at:
```
/home/packnet777/R1/services/downloads_server/apk/anomaah-rider-app.apk
```

To add new APK files, place them in the `apk/` directory and they'll automatically appear on the download page.

---

## 🔐 Security Notes

- The download server validates filenames to prevent directory traversal
- Only `.apk` files are served
- All downloads use proper MIME types

---

## 💡 Troubleshooting

### Port already in use?
Check what's using the port:
```bash
lsof -i :8750
```

### Container won't start?
Check logs:
```bash
docker-compose logs downloads-server
```

### Downloads not appearing?
Verify APK exists:
```bash
ls -la services/downloads_server/apk/
```

Verify it's being served:
```bash
curl http://localhost:8750/api/files
```

---

**Setup completed**: ✅ All services running
**APK hosting**: ✅ Active on port 8750
**Ready for**: ✅ Development and testing
