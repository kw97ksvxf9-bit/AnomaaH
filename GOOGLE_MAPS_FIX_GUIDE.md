# 🗺️ Google Maps "For Development Purposes Only" - Issue & Solution

## 🔍 Root Cause Analysis

The "For development purposes only" message appears because:

1. **API Key Restrictions** - Your Google Maps API key (`AIzaSyAbcM1mGFZo_FciqrxdYLLf6x8hAlBtYKA`) is restricted to:
   - ✗ localhost
   - ✗ 127.0.0.1
   - ✗ Possibly your local development domains only

2. **Environment Variable Not Set on Render** - The `GOOGLE_MAPS_API_KEY` environment variable may not be properly set in the Render deployment

3. **Browser Key Restrictions** - Google restricts Browser API keys by:
   - HTTP referrer (domain whitelist)
   - Only allows certain domains

---

## ✅ Solution: Update Google Cloud Console

### Step 1: Check Current API Key Restrictions

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Select your project
3. Navigate to **APIs & Services > Credentials**
4. Find your API key: `AIzaSyAbcM1mGFZo_FciqrxdYLLf6x8hAlBtYKA`
5. Click to open it

### Step 2: Configure HTTP Referrers

In the **API key** settings, find **Application restrictions** section:

**Current (Development Only):**
```
localhost
127.0.0.1
localhost:*
127.0.0.1:*
```

**What You Need (Add Your Render Domain):**
```
localhost
127.0.0.1
localhost:*
127.0.0.1:*
anomaah-web.onrender.com/*
anomaah-web.onrender.com
*.onrender.com
```

### Step 3: Enable Required APIs

Ensure these are **enabled** in your Google Cloud project:
- ✅ Maps JavaScript API
- ✅ Distance Matrix API
- ✅ Places API
- ✅ Geocoding API

### Step 4: Set Environment Variable on Render

1. Go to your **Render Dashboard**
2. Select **anomaah-web** service
3. Click **Environment**
4. Add/Update variable:
   ```
   Key: GOOGLE_MAPS_API_KEY
   Value: AIzaSyAbcM1mGFZo_FciqrxdYLLf6x8hAlBtYKA
   ```
5. Deploy/redeploy the service

---

## 🔧 How It Works Locally vs Production

### Local Development (Docker)
```
- API loads from: http://localhost:8750/api/maps-config
- Returns API key if GOOGLE_MAPS_API_KEY env var is set
- Maps loads via: https://maps.googleapis.com/maps/api/js?key=YOUR_KEY
- Works because localhost is whitelisted
```

### Production (Render)
```
- Service URL: https://anomaah-web.onrender.com
- Maps loads via: https://maps.googleapis.com/maps/api/js?key=YOUR_KEY
- FAILS because anomaah-web.onrender.com is NOT in referrer whitelist
- Shows: "For development purposes only"
```

---

## 🐛 Code Flow

### 1. Frontend requests config
```javascript
// booking.html line 427
const r = await fetch('/api/maps-config');
const d = await r.json();
```

### 2. Backend returns API key
```python
# services/admin_ui/main.py line 162-169
@app.get("/api/maps-config")
def maps_config():
    api_key = os.environ.get("GOOGLE_MAPS_API_KEY", "").strip()
    has_key = bool(api_key) and len(api_key) > 10
    return {
        "has_key": has_key,
        "api_key": api_key if has_key else None
    }
```

### 3. Frontend loads Maps API
```javascript
script.src='https://maps.googleapis.com/maps/api/js?key='+d.api_key
```

### 4. Google checks referrer
```
Referrer: https://anomaah-web.onrender.com/booking
Allowed: localhost, *.onrender.com
Result: ✅ ALLOWED
```

---

## 📋 Render Environment Variables Setup

Currently in `render.yaml`:
```yaml
- key: GOOGLE_MAPS_API_KEY
  sync: false
```

**`sync: false`** means:
- ✗ Won't auto-sync from environment
- ✓ Must be set manually in Render dashboard
- ✓ Prevents accidental exposure in git

### Steps to Set on Render:

1. **Open Render Dashboard**: https://dashboard.render.com
2. **Select Service**: anomaah-web
3. **Click Environment** tab
4. **Add Variable**:
   - Key: `GOOGLE_MAPS_API_KEY`
   - Value: `AIzaSyAbcM1mGFZo_FciqrxdYLLf6x8hAlBtYKA`
5. **Save** and **Deploy**

---

## ✅ Quick Checklist

- [ ] Go to [Google Cloud Console](https://console.cloud.google.com/)
- [ ] Select your project
- [ ] Navigate to APIs & Services > Credentials
- [ ] Edit API key `AIzaSyAbcM1mGFZo_FciqrxdYLLf6x8hAlBtYKA`
- [ ] Add HTTP Referrer: `anomaah-web.onrender.com/*`
- [ ] Save changes (wait 5-10 minutes for propagation)
- [ ] Go to Render Dashboard
- [ ] Set environment variable: `GOOGLE_MAPS_API_KEY=AIzaSyAbcM1mGFZo_FciqrxdYLLf6x8hAlBtYKA`
- [ ] Deploy service
- [ ] Test at: https://anomaah-web.onrender.com/booking

---

## 🚀 Testing After Fix

### Local Test
```bash
curl http://localhost:9000/api/maps-config
```

Expected response:
```json
{
  "has_key": true,
  "api_key": "AIzaSyAbcM1mGFZo_FciqrxdYLLf6x8hAlBtYKA"
}
```

### Production Test
```bash
curl https://anomaah-web.onrender.com/api/maps-config
```

Should return the same. If it doesn't, the environment variable isn't set on Render.

---

## 🔐 Important Notes

1. **API Key Security**
   - This key is in `.env` and visible in repo (not ideal)
   - Consider rotating this key after fixing
   - Use API key restrictions to limit damage if compromised

2. **API Key Rotation** (Optional but recommended)
   - Generate new key in Google Cloud
   - Update in `.env` and Render
   - Delete old key

3. **Alternative: Use Application Default Credentials**
   - More secure for server-side
   - Frontend still needs key for browser access

---

## 📊 Common Issues & Solutions

| Issue | Cause | Fix |
|-------|-------|-----|
| "For development only" | Referrer not whitelisted | Add domain to API key restrictions |
| API key rejected | Wrong key format | Check key length > 10 chars |
| Maps doesn't load | API disabled | Enable in Google Cloud Console |
| Blank map | No API key | Set GOOGLE_MAPS_API_KEY env var |
| 403 error | Missing permissions | Check project has Maps API enabled |

---

## 📞 Support Resources

- [Google Maps API Documentation](https://developers.google.com/maps/documentation)
- [API Key Restrictions](https://cloud.google.com/docs/authentication/api-keys)
- [Maps JavaScript API Reference](https://developers.google.com/maps/documentation/javascript)
