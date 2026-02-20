#!/bin/bash
#
# Google Maps Diagnostic Script
# Helps identify why Google Maps shows "for development purposes only"
#

set -e

echo "╔══════════════════════════════════════════════════════════╗"
echo "║  Google Maps Configuration Diagnostic Tool              ║"
echo "╚══════════════════════════════════════════════════════════╝"
echo ""

# Color codes
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Check 1: Local environment variable
echo -e "${BLUE}[1]${NC} Checking local environment..."
if grep -q "GOOGLE_MAPS_API_KEY=" .env 2>/dev/null; then
    KEY=$(grep "GOOGLE_MAPS_API_KEY=" .env | cut -d'=' -f2)
    echo -e "${GREEN}✓${NC} API Key found in .env: ${KEY:0:20}..."
    
    if [ ${#KEY} -gt 10 ]; then
        echo -e "${GREEN}✓${NC} API Key length valid (${#KEY} chars)"
    else
        echo -e "${RED}✗${NC} API Key too short (${#KEY} chars, need > 10)"
    fi
else
    echo -e "${RED}✗${NC} No GOOGLE_MAPS_API_KEY in .env"
fi
echo ""

# Check 2: Docker environment
echo -e "${BLUE}[2]${NC} Checking Docker environment..."
if docker ps | grep -q "admin-ui\|admin_ui"; then
    KEY=$(docker exec -e "GOOGLE_MAPS_API_KEY=${GOOGLE_MAPS_API_KEY}" \
        $(docker ps | grep "admin-ui\|admin_ui" | awk '{print $1}') \
        env | grep GOOGLE_MAPS_API_KEY || echo "NOT_SET")
    
    if [ "$KEY" != "NOT_SET" ]; then
        echo -e "${GREEN}✓${NC} API Key set in Docker container"
        echo "   $KEY"
    else
        echo -e "${RED}✗${NC} API Key NOT set in Docker container"
    fi
else
    echo -e "${YELLOW}!${NC} Docker container not running"
fi
echo ""

# Check 3: Local API endpoint
echo -e "${BLUE}[3]${NC} Testing local API endpoint..."
if curl -s http://localhost:9000/api/maps-config 2>/dev/null | grep -q "api_key"; then
    echo -e "${GREEN}✓${NC} /api/maps-config endpoint accessible"
    
    RESPONSE=$(curl -s http://localhost:9000/api/maps-config)
    HAS_KEY=$(echo $RESPONSE | grep -o '"has_key":[^,}]*' | cut -d':' -f2)
    
    if [ "$HAS_KEY" = "true" ]; then
        echo -e "${GREEN}✓${NC} has_key: true (API key will be sent)"
    else
        echo -e "${RED}✗${NC} has_key: false (API key missing or invalid)"
    fi
else
    echo -e "${RED}✗${NC} Cannot reach http://localhost:9000/api/maps-config"
fi
echo ""

# Check 4: Google Cloud Console requirements
echo -e "${BLUE}[4]${NC} Required Google Cloud Console Setup..."
echo "    ☐ Maps JavaScript API - Enabled?"
echo "    ☐ Distance Matrix API - Enabled?"
echo "    ☐ Places API - Enabled?"
echo "    ☐ Geocoding API - Enabled?"
echo ""

# Check 5: API Key restrictions
echo -e "${BLUE}[5]${NC} API Key HTTP Referrer Restrictions..."
echo "    Current allowed referrers (in Google Cloud Console):"
echo "    Should include:"
echo -e "    ${YELLOW}✓ localhost${NC}"
echo -e "    ${YELLOW}✓ 127.0.0.1${NC}"
echo -e "    ${YELLOW}✓ localhost:*${NC}"
echo "    ${YELLOW}✓ anomaah-web.onrender.com/*${NC} (for production)"
echo ""

# Check 6: Render deployment status
echo -e "${BLUE}[6]${NC} Render Deployment Environment..."
if [ -f "render.yaml" ]; then
    echo -e "${GREEN}✓${NC} render.yaml exists"
    
    if grep -q "GOOGLE_MAPS_API_KEY" render.yaml; then
        echo -e "${GREEN}✓${NC} GOOGLE_MAPS_API_KEY configured in render.yaml"
        
        if grep -A1 "GOOGLE_MAPS_API_KEY" render.yaml | grep -q "sync: false"; then
            echo -e "${YELLOW}!${NC} sync: false - Must set manually in Render dashboard"
        fi
    else
        echo -e "${RED}✗${NC} GOOGLE_MAPS_API_KEY not in render.yaml"
    fi
else
    echo -e "${RED}✗${NC} render.yaml not found"
fi
echo ""

# Check 7: Summary and next steps
echo "╔══════════════════════════════════════════════════════════╗"
echo "║  RECOMMENDED ACTIONS                                     ║"
echo "╚══════════════════════════════════════════════════════════╝"
echo ""
echo "1. Go to: https://console.cloud.google.com/"
echo "2. Find API key: AIzaSyAbcM1mGFZo_FciqrxdYLLf6x8hAlBtYKA"
echo "3. Edit API key restrictions"
echo "4. Add HTTP Referrer: anomaah-web.onrender.com/*"
echo "5. Save changes (wait 5-10 minutes)"
echo ""
echo "6. Go to: https://dashboard.render.com"
echo "7. Select service: anomaah-web"
echo "8. Environment tab > Add variable:"
echo "   Key: GOOGLE_MAPS_API_KEY"
echo "   Value: AIzaSyAbcM1mGFZo_FciqrxdYLLf6x8hAlBtYKA"
echo "9. Deploy service"
echo ""
echo "10. Test at: https://anomaah-web.onrender.com/booking"
echo ""
