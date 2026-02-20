# 🗺️ Google Maps "For Development Purposes Only" - Resolution Summary

## 🎯 Problem Identified

Your Google Maps is showing **"For development purposes only"** on Render deployment because:

### ❌ Issue #1: API Key Referrer Whitelist
- Your Google Maps API key (`AIzaSyAbcM1mGFZo_FciqrxdYLLf6x8hAlBtYKA`) is **restricted to localhost only**
- When loaded from `https://anomaah-web.onrender.com`, Google rejects it
- Result: Maps API returns watermarked/development version

### ❌ Issue #2: Environment Variable on Render
- The `GOOGLE_MAPS_API_KEY` in render.yaml has `sync: false`
- This means it's NOT automatically set in Render
- Must be manually configured in Render dashboard

---

## ✅ Solution (2 Steps)

### Step 1: Update Google Cloud API Key Restrictions ⏱️ ~2 minutes

1. **Open**: https://console.cloud.google.com/
2. **Project**: Select your delivery app project
3. **Navigate**: APIs & Services → Credentials
4. **Find**: API key `AIzaSyAbcM1mGFZo_FciqrxdYLLf6x8hAlBtYKA`
5. **Click** to open the key details
6. **Section**: "Application restrictions" → HTTP Referrers
7. **Current value**:
   ```
   localhost
   127.0.0.1
   localhost:*
   127.0.0.1:*
   ```
8. **Add this line**:
   ```
   anomaah-web.onrender.com/*
   ```
9. **Save** (takes 5-10 minutes to propagate)

---

### Step 2: Set Environment Variable in Render ⏱️ ~1 minute

1. **Open**: https://dashboard.render.com
2. **Services** → Select **anomaah-web**
3. **Environment** tab (top)
4. **Click**: Add Environment Variable
5. **Set**:
   - **Key**: `GOOGLE_MAPS_API_KEY`
   - **Value**: `AIzaSyAbcM1mGFZo_FciqrxdYLLf6x8hAlBtYKA`
6. **Save** (automatically deploys)

---

## 📊 Current Status

✅ **Local (Docker)**: Working perfectly
```
- Maps config endpoint: ✓ Accessible
- API key: ✓ Present (39 chars)
- API response: ✓ has_key: true
```

❌ **Production (Render)**: Maps restricted
```
- API key not in environment variables
- Domain not in API key whitelist
- Result: "For development purposes only" message
```

---

## 🔍 Technical Details

### How Maps Loading Works

```
1. Browser loads: https://anomaah-web.onrender.com/booking
2. JavaScript calls: GET /api/maps-config
3. Backend returns: { has_key: true, api_key: "AIzaSy..." }
4. JS creates script tag with API key
5. Google checks HTTP referrer header
6. Google compares referrer to API key restrictions
7. If matches → Full API
8. If doesn't match → Development watermarked version
```

### Current Referrer Check

```
Incoming request referrer: https://anomaah-web.onrender.com/booking
API key whitelist:         [localhost, 127.0.0.1, ...]
Match?                     ✗ NO
Result:                    Shows "For development purposes only"
```

### After Fix

```
Incoming request referrer: https://anomaah-web.onrender.com/booking
API key whitelist:         [localhost, 127.0.0.1, ..., anomaah-web.onrender.com/*]
Match?                     ✓ YES
Result:                    Full Maps API access
```

---

## 🧪 Testing After Fix

### Verify API Key Restriction Added
```bash
# Wait 5-10 minutes after saving in Google Cloud
# Then test from Render:
curl https://anomaah-web.onrender.com/api/maps-config
```

Expected response:
```json
{
  "has_key": true,
  "api_key": "AIzaSyAbcM1mGFZo_FciqrxdYLLf6x8hAlBtYKA"
}
```

### Verify Environment Variable Set
```bash
# In Render dashboard, check logs:
# Should show no errors loading maps
```

### Visual Test
1. Open: https://anomaah-web.onrender.com/booking
2. Look for map area
3. Should NOT show "For development purposes only"
4. Map should be fully functional

---

## 📝 Configuration Files Reference

### `.env` (Local)
```dotenv
GOOGLE_MAPS_API_KEY=AIzaSyAbcM1mGFZo_FciqrxdYLLf6x8hAlBtYKA
```
✅ Present and correct

### `render.yaml` (Deployment)
```yaml
- key: GOOGLE_MAPS_API_KEY
  sync: false
```
✅ Configured but not auto-synced (must set manually)

### Code Path
```
services/admin_ui/main.py:162-169
  ↓
/api/maps-config endpoint
  ↓
Returns: { has_key, api_key }
  ↓
services/admin_ui/static/booking.html:427-445
  ↓
Loads: https://maps.googleapis.com/maps/api/js?key=...
```

---

## 🎯 Why "sync: false" in render.yaml?

```yaml
- key: GOOGLE_MAPS_API_KEY
  sync: false   # ← Important!
```

**Means:**
- Won't auto-sync from `.env` to Render
- Must be set manually in Render dashboard
- More secure (keys not auto-uploaded)
- Prevents accidental exposure in version control

**Your action:**
- ✅ Set manually in Render dashboard (done in Step 2)

---

## 🚨 If Still Not Working After 10 Minutes

Check these:

1. **Did you save in Google Cloud Console?**
   - Check the API key edit page again
   - Verify the referrer was actually saved

2. **Did you wait 5-10 minutes?**
   - Google takes time to propagate restrictions
   - Try browser cache clear: Ctrl+Shift+Delete

3. **Is the environment variable set in Render?**
   - Dashboard → anomaah-web → Environment tab
   - Should show: `GOOGLE_MAPS_API_KEY = AIzaSy...`

4. **Is the service deployed?**
   - Render dashboard should show green "Live" status
   - Recent deploy timestamp should be after you set the variable

5. **Check Render logs for errors:**
   ```
   Render Dashboard → anomaah-web → Logs
   Look for any GOOGLE_MAPS or Maps API errors
   ```

---

## 📞 Diagnostic Tools

Run this to check local setup:
```bash
bash check-google-maps.sh
```

Output will show:
- ✓ API key in .env
- ✓ API key in Docker
- ✓ /api/maps-config accessible
- ✓ Configuration complete

---

## 🔐 Security Notes

This API key is currently:
- ✓ Restricted to HTTP referrers (not global)
- ✗ Visible in `.env` (not ideal for production)
- ✓ Limited to Maps/Places/Geocoding APIs

**Optional: Rotate Key After Fix**
1. Generate new key in Google Cloud
2. Update `.env` and Render
3. Delete old key
4. Benefits: Extra security if anyone saw the old key

---

## Summary

| Step | Action | Status | Time |
|------|--------|--------|------|
| 1 | Update API key referrer whitelist | ⏳ TODO | 2 min |
| 2 | Set env var in Render dashboard | ⏳ TODO | 1 min |
| 3 | Wait for propagation | ⏳ TODO | 5-10 min |
| 4 | Test at Render URL | ⏳ TODO | 1 min |
| ✅ | Done! Maps fully functional | Pending | - |

**Total time: ~15-20 minutes**
