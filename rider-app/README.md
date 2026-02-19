# Delivery Rider Mobile App - Android

A fully-featured Android mobile application for delivery riders to manage orders, track deliveries, and monitor earnings on the Delivery Platform.

## Architecture

The app follows **MVVM (Model-View-ViewModel)** architecture with clean separation of concerns:

- **Data Layer**: API services, repositories, local storage (encrypted SharedPreferences)
- **Domain Layer**: Business logic in repositories
- **UI Layer**: Activities, Fragments, ViewModels, LiveData

### Tech Stack

- **Language**: Kotlin (100%)
- **Minimum API**: 28 (Android 9.0)
- **Target API**: 34 (Android 14)
- **Architecture**: MVVM + Repository Pattern
- **Dependency Injection**: Hilt
- **Networking**: Retrofit 2.9.0 + OkHttp 4.11.0
- **Async**: Coroutines (kotlinx-coroutines)
- **Data Binding**: LiveData + ViewModel
- **Local Storage**: EncryptedSharedPreferences
- **Maps**: Google Maps & Location Services
- **Notifications**: Firebase Cloud Messaging (FCM)
- **Real-time**: WebSocket (nv-websocket-client)
- **Image Loading**: Glide
- **JSON**: Gson
- **UI Framework**: Material Components 3

## Project Structure

```
rider-app/
├── src/main/
│   ├── java/com/delivery/rider/
│   │   ├── RiderApplication.kt                    # Application class with Hilt setup
│   │   ├── data/
│   │   │   ├── api/
│   │   │   │   ├── ApiService.kt                 # Retrofit API interface (25+ endpoints)
│   │   │   │   ├── ApiClient.kt                  # Hilt module, OkHttpClient, interceptors
│   │   │   │   └── ApiModels.kt                  # Request/Response DTOs
│   │   │   ├── models/
│   │   │   │   └── Models.kt                     # Data classes (15+ models)
│   │   │   ├── local/
│   │   │   │   └── SharedPrefManager.kt          # Encrypted SharedPreferences manager
│   │   │   └── repository/
│   │   │       └── Repository.kt                 # 4 repository classes
│   │   │           ├── AuthRepository            # Authentication logic
│   │   │           ├── OrderRepository           # Order management
│   │   │           ├── EarningsRepository        # Earnings & payouts
│   │   │           └── RiderRepository           # Rider status & profile
│   │   ├── ui/
│   │   │   ├── auth/
│   │   │   │   ├── LoginActivity.kt              # Phone login screen
│   │   │   │   └── OtpActivity.kt                # OTP verification screen
│   │   │   ├── main/
│   │   │   │   └── MainActivity.kt               # Main app container (NavHostFragment)
│   │   │   ├── orders/
│   │   │   │   ├── OrdersFragment.kt             # Active orders list
│   │   │   │   └── OrderDetailsFragment.kt       # Order details & management
│   │   │   ├── tracking/
│   │   │   │   └── TrackingFragment.kt           # Real-time order tracking with maps
│   │   │   ├── earnings/
│   │   │   │   └── EarningsFragment.kt           # Earnings overview & history
│   │   │   ├── profile/
│   │   │   │   └── ProfileFragment.kt            # Rider profile & settings
│   │   │   └── viewmodel/
│   │   │       └── ViewModels.kt                 # 4 ViewModel classes
│   │   │           ├── AuthViewModel
│   │   │           ├── OrderViewModel
│   │   │           ├── EarningsViewModel
│   │   │           └── RiderViewModel
│   │   └── service/
│   │       ├── LocationService.kt                # Background location tracking
│   │       └── RiderMessagingService.kt          # Firebase Cloud Messaging
│   ├── res/
│   │   ├── layout/
│   │   │   ├── activity_login.xml
│   │   │   ├── activity_otp.xml
│   │   │   ├── activity_main.xml
│   │   │   ├── fragment_orders.xml
│   │   │   ├── fragment_order_details.xml
│   │   │   ├── fragment_tracking.xml
│   │   │   ├── fragment_earnings.xml
│   │   │   └── fragment_profile.xml
│   │   ├── menu/
│   │   │   └── bottom_nav_menu.xml               # Bottom navigation items
│   │   ├── navigation/
│   │   │   └── mobile_navigation.xml             # Fragment navigation graph
│   │   ├── drawable/
│   │   │   ├── edit_text_background.xml
│   │   │   └── card_background.xml
│   │   ├── values/
│   │   │   ├── colors.xml
│   │   │   ├── strings.xml
│   │   │   └── styles.xml
│   │   └── mipmap/
│   │       └── ic_launcher.png
│   └── AndroidManifest.xml
├── build.gradle                                  # App-level build configuration
├── build-root.gradle                             # Root-level build configuration
└── settings.gradle                               # Project structure definition
```

## API Integration

### Authentication Flow

1. **Login**: Phone number → OTP sent
2. **Verify OTP**: 6-digit code → Bearer token + Rider data
3. **Token Management**: Automatically injected in all API requests via AuthInterceptor
4. **Token Refresh**: Automatic refresh on 401 response

### API Endpoints

**Authentication** (3)
- `POST /auth/login` - Send OTP
- `POST /auth/verify-otp` - Verify OTP and get token
- `POST /auth/logout` - Logout

**Orders** (5)
- `GET /riders/{riderId}/orders` - Get rider's orders
- `GET /orders/{orderId}` - Get order details
- `PUT /orders/{orderId}/status` - Update order status
- `POST /orders/{orderId}/accept` - Accept order
- `POST /orders/{orderId}/cancel` - Cancel order

**Tracking** (2)
- `POST /tracking/location` - Update location
- `GET /orders/{orderId}/tracking` - Get live tracking data

**Rider Status** (1)
- `PUT /riders/{riderId}/status` - Update online/offline status

**Earnings** (3)
- `GET /riders/{riderId}/earnings` - Get earnings summary
- `GET /riders/{riderId}/payouts` - Get payout history
- `POST /riders/{riderId}/payout/request` - Request payout

**Reviews** (2)
- `GET /riders/{riderId}/reviews` - Get rider reviews
- `POST /reviews` - Submit review/rating

**Documents** (2)
- `GET /riders/{riderId}/documents` - Get required documents
- `POST /documents/upload` - Upload document (multipart)

## Features Implemented

### Phase 1: Core Infrastructure ✅
- [x] Project structure with Gradle, Kotlin, Hilt
- [x] API client with Retrofit + OkHttp
- [x] Data models (15+ classes)
- [x] Repository pattern (4 repositories)
- [x] ViewModels with LiveData (4 ViewModels)
- [x] Encrypted SharedPreferences for token/data storage
- [x] Network interceptors (auth, error, logging)
- [x] DI setup with Hilt

### Phase 2: Authentication ✅
- [x] Login activity (phone entry)
- [x] OTP verification activity
- [x] Automatic token management
- [x] Session persistence
- [x] Error handling

### Phase 3: Order Management 🟡 (In Progress)
- [x] Fragment structure created
- [x] ViewModel and repository setup
- [x] API service definitions
- [ ] Order list UI with RecyclerView adapter
- [ ] Order details screen with maps
- [ ] Order status update dialog
- [ ] Order cancellation flow

### Phase 4: Tracking 🟡 (In Progress)
- [x] Fragment structure
- [x] MapView integration
- [ ] Real-time location updates
- [ ] Order tracking on map
- [ ] Location service setup

### Phase 5: Earnings 🟡 (In Progress)
- [x] Fragment structure
- [x] ViewModel and repository
- [ ] Earnings card UI
- [ ] Period filter
- [ ] Payout request dialog
- [ ] Payout history list

### Phase 6: Profile 🟡 (In Progress)
- [x] Fragment structure
- [x] Profile display
- [x] Online/offline toggle
- [ ] Profile edit dialog
- [ ] Document upload
- [ ] Settings screen

### Phase 7: Advanced Features ⏳ (Not Started)
- [ ] WebSocket integration for real-time updates
- [ ] Firebase Cloud Messaging (FCM)
- [ ] Background location tracking service
- [ ] In-app messaging
- [ ] Push notifications
- [ ] Document upload with camera
- [ ] Ratings and reviews

## Setup Instructions

### Prerequisites
- Android Studio (latest)
- Kotlin 1.9+
- Java 17+
- Android SDK 34+
- Google Maps API key

### Build Configuration

1. **Update `local.properties`**:
   ```
   sdk.dir=/path/to/android/sdk
   ```

2. **Add Google Maps API Key** in `local.properties`:
   ```
   MAPS_API_KEY=your_api_key_here
   ```

3. **Configure API Base URL** in code:
   - Update `ApiClient.kt` with backend API URL
   - Default: `http://localhost:8000` (development)

### Build and Run

```bash
# Debug build
./gradlew assembleDebug

# Release build
./gradlew assembleRelease

# Run on emulator/device
./gradlew installDebug
```

## Testing

### Manual Testing Checklist

- [ ] Login with phone number
- [ ] OTP verification
- [ ] Automatic token refresh
- [ ] View active orders
- [ ] Accept/reject orders
- [ ] Update order status
- [ ] Track order on map
- [ ] View earnings
- [ ] Request payout
- [ ] Update profile
- [ ] Change online status
- [ ] Logout and re-login

### Automated Testing (TODO)

- [ ] Unit tests for repositories
- [ ] UI tests with Espresso
- [ ] Integration tests

## Security

- **Authentication**: Bearer token (JWT)
- **Encryption**: 
  - AES256-GCM for local storage
  - HTTPS for network communication
  - Certificate pinning (optional)
- **Permissions**: Runtime permissions for location, camera, storage
- **Data**: No credentials stored in logs or analytics

## Performance Optimization

- **Network**: Retrofit with connection pooling
- **Images**: Glide with caching strategy
- **Database**: Encrypted SharedPreferences (minimal)
- **Coroutines**: Async operations without blocking UI
- **Navigation**: Fragment transactions with backstack management

## Debugging

### Enable Network Logging

In `ApiClient.kt`, set:
```kotlin
HttpLoggingInterceptor.Level.BODY // Verbose
HttpLoggingInterceptor.Level.HEADERS // Headers only
```

### View Local Storage

```bash
adb shell
cd /data/data/com.delivery.rider/shared_prefs
cat shared_preferences.xml
```

## Dependencies

See `build.gradle` for complete dependency list. Key packages:
- `androidx.appcompat:appcompat:1.7.0`
- `androidx.lifecycle:lifecycle-viewmodel-ktx:2.7.0`
- `com.google.android.gms:play-services-maps:18.2.0`
- `com.retrofit2:retrofit:2.9.0`
- `com.google.hilt:hilt-android:2.48.1`
- `com.google.firebase:firebase-messaging:23.3.1`
- `com.squareup.okhttp3:okhttp:4.11.0`
- `org.jetbrains.kotlinx:kotlinx-coroutines-android:1.7.3`

## Environment Configuration

### Development
- Base URL: `http://192.168.1.x:8000/api`
- Logging: BODY (verbose)
- Debug: Enabled

### Staging
- Base URL: `https://staging-api.delivery.com/api`
- Logging: HEADERS
- Debug: Limited

### Production
- Base URL: `https://api.delivery.com/api`
- Logging: NONE
- Debug: Disabled
- Certificate Pinning: Enabled

## Troubleshooting

### "Network error" on login
- Check API base URL in `ApiClient.kt`
- Verify backend service is running
- Check network connectivity
- Check API response format

### "OTP verification failed"
- Verify OTP format (6 digits)
- Check backend OTP validation logic
- Check token generation

### "Map not loading"
- Verify Google Maps API key
- Check AndroidManifest.xml has API key
- Verify API key has Maps SDK enabled
- Check device has Google Play Services

### "Location permission denied"
- Implement runtime permission request
- Check targetSdk compatibility
- Test on Android 6.0+ device

## Next Steps

1. **Implement RecyclerView Adapters** for orders and payouts list
2. **Create Dialogs** for status updates, cancellations, payouts
3. **Implement Location Service** for background tracking
4. **Setup Firebase** for cloud messaging
5. **Add WebSocket** for real-time order updates
6. **Implement Camera** for document uploads
7. **Add Unit/UI Tests**
8. **Performance Testing** and optimization

## Support

For issues, bugs, or feature requests, contact the development team.

## License

Proprietary - Delivery Platform
