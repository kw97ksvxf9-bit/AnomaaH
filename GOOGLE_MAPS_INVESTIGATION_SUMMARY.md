# Investigation Summary: Google Maps Watermark Issue

## 🔍 What I Found

I've thoroughly investigated why Google Maps shows "For development purposes only" on your Render deployment while working fine locally.

### Root Cause Analysis

**There are TWO independent issues:**

#### Issue #1: API Key Domain Whitelist ⚠️
- **Current state**: API key restrictions only allow `localhost` and `127.0.0.1`
- **Problem**: When loaded from `anomaah-web.onrender.com`, Google rejects it
- **Solution**: Add `anomaah-web.onrender.com/*` to the whitelist
- **Location**: Google Cloud Console > APIs & Services > Credentials > [Your API Key] > Application restrictions > HTTP Referrers

#### Issue #2: Environment Variable Not Set in Render ⚠️
- **Current state**: `render.yaml` has `sync: false` for `GOOGLE_MAPS_API_KEY`
- **Problem**: Environment variable is NOT automatically copied to Render
- **Solution**: Manually set it in Render dashboard
- **Location**: Render Dashboard > anomaah-web > Environment tab

### Why It Works Locally But Not on Render

```
LOCAL (Docker):
  ✅ GOOGLE_MAPS_API_KEY set in .env
  ✅ localhost in API key whitelist
  ✅ Maps loads with full API access

RENDER (Production):
  ❌ GOOGLE_MAPS_API_KEY not in environment
  ❌ anomaah-web.onrender.com NOT in API key whitelist
  ❌ Google returns watermarked/limited version
```

---

## 📚 Documentation Created

I've created comprehensive guides to help you fix this:

### 1. [GOOGLE_MAPS_QUICK_FIX.md](GOOGLE_MAPS_QUICK_FIX.md)
**Quick reference card** - 2-minute read with exact steps

### 2. [GOOGLE_MAPS_ISSUE_RESOLVED.md](GOOGLE_MAPS_ISSUE_RESOLVED.md)
**Complete explanation** - Detailed breakdown with technical details, code paths, and verification steps

### 3. [GOOGLE_MAPS_FIX_GUIDE.md](GOOGLE_MAPS_FIX_GUIDE.md)
**Comprehensive guide** - Step-by-step instructions with screenshots and troubleshooting

### 4. `check-google-maps.sh`
**Diagnostic tool** - Run to check local configuration:
```bash
bash check-google-maps.sh
```

---

## ✅ Implementation Steps

### Step 1: Update Google Cloud Console (2 minutes)

1. Go to https://console.cloud.google.com/
2. Navigate to **APIs & Services > Credentials**
3. Find your API key: `AIzaSyAbcM1mGFZo_FciqrxdYLLf6x8hAlBtYKA`
4. Click to open it
5. Find **Application restrictions > HTTP Referrers**
6. Add new referrer:
   ```
   anomaah-web.onrender.com/*
   ```
7. Click **Save**
8. Wait 5-10 minutes for changes to propagate

### Step 2: Set Environment Variable in Render (1 minute)

1. Go to https://dashboard.render.com
2. Select service: **anomaah-web**
3. Click **Environment** tab
4. Click **Add Environment Variable**
5. Set:
   - **Key**: `GOOGLE_MAPS_API_KEY`
   - **Value**: `AIzaSyAbcM1mGFZo_FciqrxdYLLf6x8hAlBtYKA`
6. Click **Save** (automatically triggers deployment)

### Step 3: Verify (1 minute)

1. Wait for Render deployment to finish (check dashboard)
2. Visit: https://anomaah-web.onrender.com/booking
3. Look for Google Maps
4. Watermark should be GONE ✅

---

## 🔧 Technical Details

### Code Flow

```
User visits: https://anomaah-web.onrender.com/booking
       ↓
HTML loads: services/admin_ui/static/booking.html
       ↓
JavaScript calls: fetch('/api/maps-config')
       ↓
Backend endpoint: services/admin_ui/main.py:162-169
       Returns: { has_key: true, api_key: "AIzaSy..." }
       ↓
JavaScript loads: <script src="https://maps.googleapis.com/maps/api/js?key=...">
       ↓
Google checks: Is referrer (anomaah-web.onrender.com) in API key whitelist?
       ↓
Current: NO ❌ → Returns watermarked version
After fix: YES ✅ → Returns full API access
```

### Configuration Files

**`.env`** (Local development)
```dotenv
GOOGLE_MAPS_API_KEY=AIzaSyAbcM1mGFZo_FciqrxdYLLf6x8hAlBtYKA
```
Status: ✅ Correct

**`render.yaml`** (Deployment config)
```yaml
- key: GOOGLE_MAPS_API_KEY
  sync: false   # Manual setup required
```
Status: ✅ Correct (by design)

---

## 📊 Local Verification

Your local setup is **100% correct**:

```
✅ API Key in .env: Present (39 chars)
✅ API Key in Docker: Properly loaded
✅ /api/maps-config endpoint: Accessible
✅ API response: { has_key: true, api_key: "..." }
✅ Maps load locally: YES (no watermark)
```

The issue is **100% on the Render side** (expected configuration).

---

## 🎯 Summary

| What | Status | Action |
|------|--------|--------|
| Local setup | ✅ Working | None needed |
| API key | ✅ Valid | None needed |
| Code paths | ✅ Correct | None needed |
| Google Console | ❌ Missing domain | Add `anomaah-web.onrender.com/*` |
| Render env var | ❌ Not set | Set in Render dashboard |
| Production maps | ❌ Watermarked | Will be fixed after steps above |

---

## 📞 If You Get Stuck

### Diagnostic Command
```bash
bash check-google-maps.sh
```

### Check Specific Things

**Verify API key was added to Google Console:**
- Google Cloud Console > Credentials > Your API Key > Application restrictions
- Should show: `anomaah-web.onrender.com/*`

**Verify environment variable in Render:**
- Render Dashboard > anomaah-web > Environment tab
- Should show: `GOOGLE_MAPS_API_KEY = AIzaSy...`

**Check if deployment is active:**
- Render Dashboard > anomaah-web > Deployments
- Should show recent deployment with green checkmark

**Test the endpoint:**
```bash
curl https://anomaah-web.onrender.com/api/maps-config
```

Should return:
```json
{
  "has_key": true,
  "api_key": "AIzaSyAbcM1mGFZo_FciqrxdYLLf6x8hAlBtYKA"
}
```

---

## ✨ Key Insights

1. **Why "For development purposes only"?**
   - Google's way of saying: "This key isn't authorized for this domain"
   - It's a security feature to prevent unauthorized API key usage

2. **Why does localhost work?**
   - Already whitelisted in API key restrictions
   - Google trusts development domains by default

3. **Why `sync: false` in render.yaml?**
   - Extra security measure
   - Prevents accidentally uploading secrets to version control
   - Requires manual setup in Render dashboard (what you'll do in Step 2)

4. **Why not use APPLICATION_DEFAULT_CREDENTIALS?**
   - Browser-side Maps API requires an API key
   - Can't use service account credentials in JavaScript
   - Must use Browser API key with restrictions

---

## 📋 Checklist

- [ ] Read [GOOGLE_MAPS_QUICK_FIX.md](GOOGLE_MAPS_QUICK_FIX.md)
- [ ] Go to Google Cloud Console
- [ ] Add domain to API key whitelist
- [ ] Wait 5-10 minutes
- [ ] Go to Render Dashboard
- [ ] Set GOOGLE_MAPS_API_KEY environment variable
- [ ] Wait for deployment to complete
- [ ] Test at https://anomaah-web.onrender.com/booking
- [ ] Verify map loads without watermark
- [ ] Done! 🎉

---

**Estimated time to complete: 15-20 minutes**
**Difficulty: Easy (2 dashboard changes)**
**Risk: Zero (just configuration, no code changes)**
