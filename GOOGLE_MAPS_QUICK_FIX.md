# ⚡ Quick Reference: Google Maps Fix

## Problem
Maps shows "For development purposes only" on Render (but works locally)

## Root Cause
1. API key not whitelisted for `anomaah-web.onrender.com`
2. Environment variable not set in Render

## Fix (2 Easy Steps)

### 📍 Step 1: Google Cloud Console
1. Go to: https://console.cloud.google.com/
2. APIs & Services → Credentials
3. Click: `AIzaSyAbcM1mGFZo_FciqrxdYLLf6x8hAlBtYKA`
4. Find: **Application restrictions** → **HTTP Referrers**
5. Add: `anomaah-web.onrender.com/*`
6. **Save**

⏱️ Takes 2 minutes + 5-10 min propagation

### 🎛️ Step 2: Render Dashboard
1. Go to: https://dashboard.render.com
2. Select: **anomaah-web** service
3. Click: **Environment** tab
4. **Add Variable**:
   ```
   Key:   GOOGLE_MAPS_API_KEY
   Value: AIzaSyAbcM1mGFZo_FciqrxdYLLf6x8hAlBtYKA
   ```
5. **Save** (auto-deploys)

⏱️ Takes 1 minute

### ✅ Verify
- Open: https://anomaah-web.onrender.com/booking
- Look for map watermark
- Should be GONE ✓

## Files Reference
- 📖 Detailed guide: [GOOGLE_MAPS_FIX_GUIDE.md](GOOGLE_MAPS_FIX_GUIDE.md)
- 📖 Full analysis: [GOOGLE_MAPS_ISSUE_RESOLVED.md](GOOGLE_MAPS_ISSUE_RESOLVED.md)
- 🔧 Diagnostic tool: `bash check-google-maps.sh`

## Code Involved
- `services/admin_ui/main.py` → `/api/maps-config` endpoint
- `services/admin_ui/static/booking.html` → Maps loader
- `.env` → Local API key storage
- `render.yaml` → Deployment config

---

**Status**: ✅ Ready to fix
**Time needed**: ~20 minutes total
**Difficulty**: Easy (2 UI steps)
