# Rider Mobile App (Android) - Architecture & Plan

**Status:** 🟡 PLANNING PHASE  
**Target Platform:** Android (API Level 28+)  
**Technology Stack:** Kotlin, Jetpack, Retrofit, MVVM  
**Last Updated:** January 31, 2026  

---

## 📋 Project Overview

The Rider Mobile App is the final piece of the delivery platform. It enables riders to:
- Receive order notifications
- View assigned orders with location details
- Navigate to pickup/dropoff locations
- Update order status in real-time
- View earnings and ratings
- Manage account and documents
- Communicate with merchants & support

---

## 🎯 Core Features

### 1. **Authentication**
- Phone number login (OTP verification)
- Session management
- Automatic re-authentication
- Logout functionality

### 2. **Orders Management**
- List of assigned orders
- Order details (pickup, dropoff, distance, eta, price)
- Order status tracking (PENDING → ASSIGNED → PICKED_UP → IN_TRANSIT → DELIVERED)
- Order actions (Accept, Reject, Start, Deliver, Cancel)
- Real-time order updates via WebSocket

### 3. **Navigation & Tracking**
- Google Maps integration
- Turn-by-turn directions (Google Maps API)
- GPS tracking (send location updates to server)
- Live location sharing with merchant
- ETA calculation

### 4. **Earnings Dashboard**
- Daily/Weekly/Monthly earnings
- Commission calculations
- Payout history
- Withdrawal requests
- Transaction details

### 5. **Profile & Account**
- Rider profile information
- Document management (License, Insurance, ID)
- Document upload & verification
- Account settings
- Notification preferences

### 6. **Reviews & Ratings**
- View ratings received
- Review history
- Performance metrics
- Badges and achievements

### 7. **Communication**
- In-app messaging with merchants
- Support chat
- Notifications (orders, payouts, messages)
- Push notifications

---

## 🏗️ App Architecture

```
rider-app/
├── app/
│   ├── src/
│   │   ├── main/
│   │   │   ├── java/com/delivery/rider/
│   │   │   │   ├── MainActivity.kt
│   │   │   │   ├── auth/
│   │   │   │   │   ├── LoginActivity.kt
│   │   │   │   │   └── OtpActivity.kt
│   │   │   │   ├── orders/
│   │   │   │   │   ├── OrderListFragment.kt
│   │   │   │   │   ├── OrderDetailFragment.kt
│   │   │   │   │   ├── OrderViewModel.kt
│   │   │   │   │   └── OrderAdapter.kt
│   │   │   │   ├── tracking/
│   │   │   │   │   ├── TrackingFragment.kt
│   │   │   │   │   ├── TrackingViewModel.kt
│   │   │   │   │   └── LocationService.kt
│   │   │   │   ├── earnings/
│   │   │   │   │   ├── EarningsFragment.kt
│   │   │   │   │   └── EarningsViewModel.kt
│   │   │   │   ├── profile/
│   │   │   │   │   ├── ProfileFragment.kt
│   │   │   │   │   ├── DocumentsFragment.kt
│   │   │   │   │   └── ProfileViewModel.kt
│   │   │   │   ├── data/
│   │   │   │   │   ├── api/
│   │   │   │   │   │   ├── ApiClient.kt
│   │   │   │   │   │   ├── ApiService.kt
│   │   │   │   │   │   └── Interceptors.kt
│   │   │   │   │   ├── models/
│   │   │   │   │   │   ├── Order.kt
│   │   │   │   │   │   ├── Rider.kt
│   │   │   │   │   │   ├── User.kt
│   │   │   │   │   │   └── etc.
│   │   │   │   │   ├── repository/
│   │   │   │   │   │   ├── OrderRepository.kt
│   │   │   │   │   │   ├── RiderRepository.kt
│   │   │   │   │   │   └── AuthRepository.kt
│   │   │   │   │   └── local/
│   │   │   │   │       ├── SharedPrefManager.kt
│   │   │   │   │       └── UserPreferences.kt
│   │   │   │   ├── service/
│   │   │   │   │   ├── LocationTrackingService.kt
│   │   │   │   │   ├── OrderSyncService.kt
│   │   │   │   │   └── NotificationService.kt
│   │   │   │   ├── ui/
│   │   │   │   │   └── [composable components]
│   │   │   │   └── utils/
│   │   │   │       ├── Constants.kt
│   │   │   │       ├── Extensions.kt
│   │   │   │       └── Utils.kt
│   │   │   └── res/
│   │   │       ├── layout/
│   │   │       ├── drawable/
│   │   │       ├── values/
│   │   │       └── menu/
│   │   └── test/
│   ├── build.gradle
│   └── AndroidManifest.xml
├── settings.gradle
└── build.gradle
```

---

## 📱 Key Activities & Fragments

### 1. **Authentication Flow**
- **LoginActivity** - Phone number input
- **OtpActivity** - OTP verification
- **SplashActivity** - Auto-login if token exists

### 2. **Main Navigation** (Bottom Tab Navigation)
- **Orders Tab** → OrderListFragment → OrderDetailFragment
- **Tracking Tab** → TrackingFragment (Active order)
- **Earnings Tab** → EarningsFragment
- **Profile Tab** → ProfileFragment

### 3. **Supporting Screens**
- **NotificationsFragment** - Push notifications history
- **SupportFragment** - Chat with support
- **SettingsFragment** - App settings
- **DocumentsFragment** - Document management

---

## 🔌 API Integration Points

### Order Service (8500)
```
GET  /orders/rider/{rider_id}           - List rider's orders
GET  /orders/{order_id}                 - Get order details
POST /orders/{order_id}/update-status   - Update order status
POST /orders/{order_id}/cancel          - Cancel order
```

### Tracking Service (8300)
```
POST /tracking/start                    - Start tracking
POST /tracking/location                 - Send GPS update
GET  /tracking/order/{order_id}         - Get tracking info
```

### Notification Service (8400)
```
POST /notify/event                      - Push notification
GET  /notifications                     - Get notification history
POST /notifications/{id}/read           - Mark as read
```

### Review Service (8700)
```
GET  /reviews/rider/{rider_id}          - Get rider reviews
GET  /ratings/rider/{rider_id}          - Get rating details
```

### Rider Status Service (8800)
```
POST /status/update                     - Update online/offline status
GET  /status/{rider_id}                 - Get rider status
POST /docs/upload                       - Upload documents
```

### Payment Service (8200)
```
GET  /earnings/{rider_id}               - Get earnings data
GET  /payouts/{rider_id}                - Get payout history
POST /payouts/request                   - Request payout
```

---

## 📦 Dependencies

```gradle
dependencies {
    // Core
    implementation 'androidx.core:core-ktx:1.10.1'
    implementation 'androidx.appcompat:appcompat:1.6.1'
    implementation 'androidx.activity:activity-ktx:1.7.2'
    implementation 'androidx.fragment:fragment-ktx:1.6.1'
    
    // Material Design
    implementation 'com.google.android.material:material:1.9.0'
    implementation 'androidx.constraintlayout:constraintlayout:2.1.4'
    
    // Jetpack
    implementation 'androidx.lifecycle:lifecycle-viewmodel-ktx:2.6.1'
    implementation 'androidx.lifecycle:lifecycle-runtime-ktx:2.6.1'
    implementation 'androidx.lifecycle:lifecycle-livedata-ktx:2.6.1'
    implementation 'androidx.datastore:datastore-preferences:1.0.0'
    
    // Networking
    implementation 'com.squareup.retrofit2:retrofit:2.9.0'
    implementation 'com.squareup.retrofit2:converter-gson:2.9.0'
    implementation 'com.squareup.okhttp3:okhttp:4.11.0'
    implementation 'com.squareup.okhttp3:logging-interceptor:4.11.0'
    
    // JSON Parsing
    implementation 'com.google.code.gson:gson:2.10.1'
    
    // Dependency Injection
    implementation 'com.google.dagger:hilt-android:2.46'
    kapt 'com.google.dagger:hilt-compiler:2.46'
    
    // Maps
    implementation 'com.google.android.gms:play-services-maps:18.2.0'
    implementation 'com.google.android.gms:play-services-location:21.0.1'
    
    // Location
    implementation 'com.google.android.gms:play-services-location:21.0.1'
    
    // WebSocket
    implementation 'com.neovisionaries:nv-websocket-client:2.14'
    
    // Notifications
    implementation 'com.google.firebase:firebase-messaging:23.2.1'
    
    // Image Loading
    implementation 'com.github.bumptech.glide:glide:4.15.1'
    kapt 'com.github.bumptech.glide:compiler:4.15.1'
    
    // Date/Time
    implementation 'joda-time:joda-time:2.12.5'
    
    // Testing
    testImplementation 'junit:junit:4.13.2'
    androidTestImplementation 'androidx.test.ext:junit:1.1.5'
    androidTestImplementation 'androidx.test.espresso:espresso-core:3.5.1'
}
```

---

## 🔐 Permissions Required

```xml
<!-- AndroidManifest.xml -->

<!-- Location -->
<uses-permission android:name="android.permission.ACCESS_FINE_LOCATION" />
<uses-permission android:name="android.permission.ACCESS_COARSE_LOCATION" />

<!-- Internet -->
<uses-permission android:name="android.permission.INTERNET" />

<!-- Background Location (Android 10+) -->
<uses-permission android:name="android.permission.ACCESS_BACKGROUND_LOCATION" />

<!-- Phone State -->
<uses-permission android:name="android.permission.READ_PHONE_STATE" />

<!-- Notifications -->
<uses-permission android:name="com.google.android.c2dm.permission.RECEIVE" />

<!-- Camera (for document upload) -->
<uses-permission android:name="android.permission.CAMERA" />

<!-- Storage (for document upload) -->
<uses-permission android:name="android.permission.READ_EXTERNAL_STORAGE" />
<uses-permission android:name="android.permission.WRITE_EXTERNAL_STORAGE" />

<!-- Wake Lock (background tracking) -->
<uses-permission android:name="android.permission.WAKE_LOCK" />
```

---

## 🎨 UI/UX Design

### Color Scheme
- Primary: #0EA5E9 (Sky Blue)
- Secondary: #10B981 (Emerald)
- Danger: #EF4444 (Red)
- Background: #F8FAFC (Light Gray)
- Text Primary: #1E293B (Dark)
- Text Secondary: #64748B (Gray)

### Typography
- Heading: 24sp, Bold, Primary Color
- Subheading: 18sp, SemiBold, Dark
- Body: 14sp, Regular, Gray
- Caption: 12sp, Regular, Light Gray

### Spacing
- XXSmall: 4dp
- XSmall: 8dp
- Small: 12dp
- Medium: 16dp
- Large: 24dp
- XLarge: 32dp

---

## 📊 Data Models

### Core Models
```kotlin
data class Rider(
    val id: String,
    val name: String,
    val phone: String,
    val email: String,
    val profilePicUrl: String?,
    val companyId: String,
    val rating: Float,
    val totalDeliveries: Int,
    val totalEarnings: Float,
    val status: String, // online, offline, busy
    val createdAt: Long
)

data class Order(
    val id: String,
    val pickupAddress: String,
    val pickupLat: Double,
    val pickupLng: Double,
    val dropoffAddress: String,
    val dropoffLat: Double,
    val dropoffLng: Double,
    val distanceKm: Float,
    val etaMin: Int,
    val priceGhs: Float,
    val status: String,
    val assignedRiderId: String?,
    val createdAt: Long,
    val assignedAt: Long?,
    val deliveredAt: Long?
)

data class Earnings(
    val date: String,
    val amount: Float,
    val orders: Int,
    val distance: Float
)

data class Review(
    val id: String,
    val rating: Int,
    val comment: String,
    val merchantName: String,
    val createdAt: Long
)
```

---

## 🔄 State Management

Using **MVVM + LiveData** pattern:
- **ViewModel** - Manages UI state and business logic
- **LiveData** - Reactive data binding
- **Repository** - Data access abstraction
- **ApiService** - Network calls

Example:
```kotlin
class OrderViewModel : ViewModel() {
    private val orderRepository = OrderRepository()
    
    private val _orders = MutableLiveData<List<Order>>()
    val orders: LiveData<List<Order>> = _orders
    
    private val _isLoading = MutableLiveData<Boolean>()
    val isLoading: LiveData<Boolean> = _isLoading
    
    fun loadOrders(riderId: String) {
        _isLoading.value = true
        viewModelScope.launch {
            try {
                val orders = orderRepository.getOrders(riderId)
                _orders.value = orders
            } catch (e: Exception) {
                // Handle error
            } finally {
                _isLoading.value = false
            }
        }
    }
}
```

---

## 🚀 Implementation Phases

### Phase 1: Core Infrastructure (Week 1)
- [ ] Project setup & build.gradle configuration
- [ ] API client setup (Retrofit)
- [ ] Authentication (login/logout)
- [ ] Data models & repository
- [ ] Local storage (SharedPreferences/DataStore)

### Phase 2: Core Features (Week 2)
- [ ] Order list screen
- [ ] Order details screen
- [ ] Order status updates
- [ ] Navigation & Maps integration
- [ ] Bottom navigation

### Phase 3: Advanced Features (Week 3)
- [ ] Location tracking service
- [ ] GPS updates to server
- [ ] Real-time order sync (WebSocket)
- [ ] Earnings dashboard
- [ ] Profile & document management

### Phase 4: Polish & Testing (Week 4)
- [ ] UI/UX refinement
- [ ] Error handling & edge cases
- [ ] Performance optimization
- [ ] Testing (unit & integration)
- [ ] Documentation

---

## 📝 Development Checklist

### Week 1: Foundation
- [ ] Gradle setup with all dependencies
- [ ] API client (Retrofit configuration)
- [ ] Authentication flow (login/otp)
- [ ] Token management & auto-refresh
- [ ] SharedPreferences manager
- [ ] Basic error handling

### Week 2: Core UX
- [ ] Splash screen
- [ ] Login/OTP screens
- [ ] Main activity with bottom nav
- [ ] Orders list fragment
- [ ] Order details fragment
- [ ] Basic styling & theming

### Week 3: Functionality
- [ ] Order operations (accept, start, deliver)
- [ ] Location permission handling
- [ ] GPS tracking integration
- [ ] Map display with directions
- [ ] Real-time location updates
- [ ] Earnings fragment with data

### Week 4: Polish
- [ ] Profile fragment
- [ ] Documents fragment
- [ ] Settings screen
- [ ] Notification handling
- [ ] Error messages & UX improvements
- [ ] Testing & debugging

---

## 🔒 Security Considerations

1. **Token Storage**
   - Use encrypted SharedPreferences
   - Or DataStore with encryption

2. **API Security**
   - HTTPS only
   - Token in Authorization header
   - Request signing (optional)

3. **Location Privacy**
   - Only collect when order active
   - Clear location after delivery
   - User consent prompt

4. **Data Validation**
   - Validate all API responses
   - Sanitize user inputs
   - Handle corrupted data gracefully

---

## 📊 Testing Strategy

### Unit Tests
- ViewModel logic
- Repository methods
- Utility functions
- Data models

### Integration Tests
- API client tests
- Database access tests
- End-to-end flows

### UI Tests
- Fragment navigation
- User interactions
- Error states

### Performance Tests
- Location tracking memory usage
- Network optimization
- Battery consumption

---

## 🎯 Success Criteria

✅ **Functionality**
- All core features working (orders, tracking, earnings)
- Smooth navigation & transitions
- No crashes (< 0.1% crash rate)

✅ **Performance**
- App starts in < 3 seconds
- Scroll @ 60 FPS
- Location updates < 100ms latency

✅ **User Experience**
- Intuitive navigation
- Clear error messages
- Responsive UI

✅ **Reliability**
- Handles poor connectivity
- Graceful degradation
- Background sync working

---

## 📚 Documentation

Will include:
1. **Setup & Installation** - How to build & run
2. **Architecture** - System design & components
3. **API Integration** - Endpoint usage
4. **Contributing** - Development guidelines
5. **Deployment** - Release process

---

## 🚀 Ready to Start?

This plan covers:
- ✅ Complete app architecture
- ✅ Feature breakdown
- ✅ Tech stack & dependencies
- ✅ UI/UX guidelines
- ✅ Implementation phases
- ✅ Testing strategy
- ✅ Security considerations

**Next Step:** Implement Phase 1 - Core Infrastructure

Would you like me to:
1. Start building Phase 1 (project structure, API client, auth)?
2. Create the project skeleton with all directories?
3. Build specific features first?
4. Something else?

Let me know how you'd like to proceed! 🚀
