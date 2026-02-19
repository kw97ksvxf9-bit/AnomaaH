# Rider Mobile App - Quick Reference Guide

## Development Status

**Current Phase**: Phase 1 - Core Infrastructure (95% Complete)
**Completion**: ~15% of full app

### Completed Components
- ✅ Project structure (Gradle, Kotlin setup)
- ✅ Build configuration (40+ dependencies)
- ✅ Data models (15+ classes)
- ✅ API client with Hilt DI
- ✅ Repository pattern (4 repos)
- ✅ ViewModels (4 ViewModels)
- ✅ Authentication activities (Login, OTP)
- ✅ Main container activity
- ✅ Fragment scaffolding (4 main fragments)
- ✅ Basic layouts (9 XML layouts)
- ✅ Resources (colors, strings, styles)

### In-Progress Components
- 🟡 Order list RecyclerView adapter
- 🟡 Order details UI implementation
- 🟡 Map integration for tracking
- 🟡 Earnings UI completion

### Not Started
- ⏳ Location service
- ⏳ Firebase Cloud Messaging
- ⏳ WebSocket integration
- ⏳ Document upload
- ⏳ Unit & UI tests

## Quick Commands

### Build & Run
```bash
# Build debug APK
./gradlew assembleDebug

# Run on device
./gradlew installDebug

# Clean build
./gradlew clean build

# View gradle dependencies
./gradlew dependencies
```

### Code Generation
```bash
# Hilt dependency injection compilation
# (automatic on build)

# Kotlin compilation
./gradlew compileDebugKotlin
```

### Testing
```bash
# Run unit tests
./gradlew testDebug

# Run instrumented tests (Android device)
./gradlew connectedAndroidTest

# Generate test report
./gradlew testDebugUnitTest --info
```

## Key Files Reference

### Configuration
- `build.gradle` - App dependencies and build config
- `AndroidManifest.xml` - Permissions, activities, services
- `gradle.properties` - Build properties

### Core Components
- `RiderApplication.kt` - App initialization, Hilt setup
- `ApiClient.kt` - Network client, interceptors, Hilt module
- `SharedPrefManager.kt` - Encrypted local storage

### Repositories
- `AuthRepository` - Login, logout, token management
- `OrderRepository` - Order CRUD operations
- `EarningsRepository` - Earnings and payout management
- `RiderRepository` - Rider profile and status

### ViewModels
- `AuthViewModel` - Authentication state management
- `OrderViewModel` - Order list and details state
- `EarningsViewModel` - Earnings data management
- `RiderViewModel` - Rider profile and status state

### UI Activities
- `LoginActivity` - Phone number entry
- `OtpActivity` - OTP verification
- `MainActivity` - Main app container with navigation

### UI Fragments
- `OrdersFragment` - Active orders list
- `OrderDetailsFragment` - Selected order details
- `TrackingFragment` - Live order tracking with maps
- `EarningsFragment` - Earnings summary and history
- `ProfileFragment` - Rider profile and settings

## API Endpoint Quick Reference

```
Authentication
  POST /auth/login                          → Send OTP
  POST /auth/verify-otp                     → Verify OTP + get token
  POST /auth/logout                         → Logout

Orders (5 endpoints)
  GET /riders/{riderId}/orders              → Get orders list
  GET /orders/{orderId}                     → Get order details
  PUT /orders/{orderId}/status              → Update status
  POST /orders/{orderId}/accept             → Accept order
  POST /orders/{orderId}/cancel             → Cancel order

Tracking (2 endpoints)
  POST /tracking/location                   → Send location
  GET /orders/{orderId}/tracking            → Get tracking data

Status (1 endpoint)
  PUT /riders/{riderId}/status              → Update online/offline

Earnings (3 endpoints)
  GET /riders/{riderId}/earnings            → Get earnings summary
  GET /riders/{riderId}/payouts             → Get payout history
  POST /riders/{riderId}/payout/request     → Request payout

Reviews (2 endpoints)
  GET /riders/{riderId}/reviews             → Get reviews
  POST /reviews                             → Submit review

Documents (2 endpoints)
  GET /riders/{riderId}/documents           → Get documents
  POST /documents/upload                    → Upload document

Total: 25+ endpoints
```

## Data Models

```
Core Models:
  - Rider (rider info, rating, status)
  - Order (order details, locations, price)
  - User (customer basic info)
  - Auth (token, refresh token)
  - Earnings (daily, weekly, monthly totals)
  - Review (rating, comment, date)
  - Tracking (latitude, longitude, timestamp)
  - Notification (message, type, status)
  - Payout (amount, date, status)
  - Document (type, url, verification status)

+ 5 more specialized models
Total: 15+ data classes with JSON serialization
```

## Navigation Structure

```
MainActivity (NavHostFragment)
  ├── OrdersFragment
  │   └── OrderDetailsFragment
  ├── TrackingFragment
  ├── EarningsFragment
  └── ProfileFragment

Initial Navigation:
  LoginActivity → OtpActivity → MainActivity

Bottom Navigation Menu:
  Orders | Tracking | Earnings | Profile
```

## Authentication Flow

```
1. User enters phone → LoginActivity
   ↓
2. POST /auth/login (phone) → OTP sent
   ↓
3. User enters OTP → OtpActivity
   ↓
4. POST /auth/verify-otp (phone, otp) → Token + Rider data
   ↓
5. Save token in EncryptedSharedPreferences
   ↓
6. Navigate to MainActivity
   ↓
7. All API calls have Bearer token (via AuthInterceptor)
```

## Fragment Implementation Checklist

For each fragment, typically need:

```
1. ViewModel initialization with @HiltViewModel
2. Fragment layout XML with:
   - RecyclerView or list component
   - ProgressBar for loading states
   - Empty state text view
   - Action buttons (if applicable)
3. LiveData observers for:
   - Data state (loading, success, error)
   - Data list/item updates
4. RecyclerView adapter and ViewHolder
5. Click listeners for items
6. Navigation to detail screens (if needed)
```

## Common Tasks

### Add New Fragment
1. Create `MyFragment.kt` in `ui/myfragment/`
2. Create `fragment_my.xml` in `res/layout/`
3. Add to `mobile_navigation.xml`
4. Add to `bottom_nav_menu.xml` (if main screen)
5. Implement with ViewModel and LiveData

### Add New API Endpoint
1. Add suspend function in `ApiService.kt`
2. Create request/response models in `ApiModels.kt`
3. Add method in appropriate `Repository`
4. Use in `ViewModel` with `viewModelScope.launch`

### Add New ViewModel
1. Create class with `@HiltViewModel` annotation
2. Inject repositories in constructor
3. Create LiveData for UI state
4. Create methods for operations
5. Use `viewModelScope.launch` for async operations

### Update UI State
1. Observe LiveData in Fragment
2. Handle states: Loading, Success, Error
3. Update UI views accordingly
4. Show progress bar during loading
5. Show error messages on failure

## Dependencies Overview

```
Essential (included in build.gradle):
  - Androidx AppCompat, Lifecycle, Navigation
  - Material Components 3
  - Hilt DI framework
  - Retrofit 2 + OkHttp 3
  - Kotlin Coroutines
  - Gson for JSON parsing
  - Google Play Services (Maps, Location)
  - Firebase (Cloud Messaging)
  - Glide for images
  - EncryptedSharedPreferences
  - WebSocket client

Total: 40+ dependencies
All production-grade, well-maintained packages
```

## Testing Strategy

### Unit Tests (TODO)
- Repository logic
- ViewModel state management
- Data models serialization

### UI Tests (TODO)
- Fragment navigation
- Button clicks
- Form validation
- Error message display

### Integration Tests (TODO)
- End-to-end user flows
- API communication
- Local storage

## Performance Targets

- **App startup**: < 2 seconds
- **API response time**: < 2 seconds
- **Screen transition**: < 500ms
- **List scrolling**: 60 FPS
- **Memory usage**: < 100MB
- **Battery drain**: Minimal (location service optimized)

## Code Quality Standards

- **Kotlin style**: Official Kotlin style guide
- **Naming conventions**: 
  - Classes: PascalCase
  - Functions: camelCase
  - Constants: UPPER_CASE
  - Resources: snake_case
- **Comments**: JavaDoc for public APIs
- **Error handling**: Try-catch with meaningful messages
- **Null safety**: Use nullable types explicitly

## Next Immediate Tasks

### Priority 1 (Core functionality)
- [ ] Create OrderAdapter for RecyclerView
- [ ] Implement order list UI binding
- [ ] Create OrderDetailsFragment maps integration
- [ ] Implement status update dialog

### Priority 2 (Supporting features)
- [ ] Create PayoutAdapter for earnings history
- [ ] Implement earnings period filter
- [ ] Add location tracking service
- [ ] Implement Firebase messaging service

### Priority 3 (Polish & testing)
- [ ] Add input validation dialogs
- [ ] Implement error handling dialogs
- [ ] Add unit tests
- [ ] Performance optimization

## Debugging Tips

### Network Issues
```kotlin
// In ApiClient.kt, add logging:
HttpLoggingInterceptor().apply {
    level = HttpLoggingInterceptor.Level.BODY
}
```

### View Binding Issues
```kotlin
// Use findViewById if View Binding not working
val view = findViewById<TextView>(R.id.my_text)
```

### ViewModel Lifecycle
```kotlin
// Check if ViewModel data persists across config changes
// It should - this is the point of ViewModel
```

### LiveData Issues
```kotlin
// Always observe in UI (Activity/Fragment)
// Use viewLifecycleOwner for Fragment observers
viewModel.data.observe(viewLifecycleOwner) { /* ... */ }
```

## Resource Links

- [Android Developers](https://developer.android.com/)
- [Kotlin Documentation](https://kotlinlang.org/docs/)
- [Hilt Documentation](https://dagger.dev/hilt/)
- [Retrofit Documentation](https://square.github.io/retrofit/)
- [Android Architecture Components](https://developer.android.com/jetpack/guide)
- [Material Design 3](https://m3.material.io/)

## Contact & Support

For questions about implementation, refer to:
1. Code comments and KDoc
2. RIDER_APP_ARCHITECTURE.md for detailed design
3. README.md for comprehensive guide
4. Official Android documentation

---

**Last Updated**: [Current Date]
**Status**: 🟡 In Active Development
**Maintainer**: Development Team
