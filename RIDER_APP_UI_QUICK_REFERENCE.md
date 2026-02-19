# Rider App UI - Quick Reference

## Fragment Implementation Summary

### 1. OrdersFragment ✅
**Location**: `ui/orders/OrdersFragment.kt`
**Purpose**: Display list of active orders
**Key Methods**:
- `initializeViews()` - Setup RecyclerView with OrderAdapter
- `observeViewModel()` - Listen for order list updates
- Click listener navigates to OrderDetailsFragment

**Code Snippet**:
```kotlin
adapter = OrderAdapter { order ->
    viewModel.loadOrderDetails(order.id)
    findNavController().navigate(R.id.action_orders_to_details)
}
```

---

### 2. OrderDetailsFragment ✅
**Location**: `ui/orders/OrderDetailsFragment.kt`
**Purpose**: Show full order details and actions
**Key Methods**:
- `showStatusUpdateDialog()` - AlertDialog with status spinner
- `showCancelDialog()` - AlertDialog with cancellation reason
- Both validate input before submitting

**Dialog Features**:
- Status Update: Spinner selection + optional notes
- Cancellation: Required reason input validation

---

### 3. EarningsFragment ✅
**Location**: `ui/earnings/EarningsFragment.kt`
**Purpose**: Display earnings and payout history
**Key Elements**:
- Period spinner: Daily/Weekly/Monthly/Yearly
- PayoutAdapter for history list
- Payout request dialog with amount validation

**Spinner Implementation**:
```kotlin
periodSpinner.setOnItemSelectedListener { parent, view, position, id ->
    val period = periods[position].lowercase()
    viewModel.loadEarnings(period)
}
```

---

### 4. ProfileFragment ✅
**Location**: `ui/profile/ProfileFragment.kt`
**Purpose**: Rider profile and settings
**Key Features**:
- Display: Name, phone, rating, completed orders
- Online/offline toggle switch
- Edit profile dialog
- Logout with confirmation

**Toggle Implementation**:
```kotlin
onlineSwitch.setOnCheckedChangeListener { _, isChecked ->
    val status = if (isChecked) "online" else "offline"
    viewModel.updateStatus(status)
}
```

---

### 5. TrackingFragment ✅
**Location**: `ui/tracking/TrackingFragment.kt`
**Purpose**: Real-time order tracking with Maps
**Key Features**:
- Google Maps MapView
- Rider location marker
- Pickup/dropoff location markers
- Distance to destination display

**Map Setup**:
```kotlin
override fun onMapReady(map: GoogleMap) {
    googleMap = map
    val defaultLocation = LatLng(28.7041, 77.1025)
    googleMap?.moveCamera(CameraUpdateFactory.newLatLngZoom(defaultLocation, 12f))
}
```

---

## Adapter Implementation

### OrderAdapter
- **Lines**: 95
- **Purpose**: Display orders in RecyclerView
- **Key Features**:
  - Status color coding (picked_up, in_transit, delivered)
  - Click listener callback
  - `updateOrders(list)` method for data updates

### PayoutAdapter
- **Lines**: 72
- **Purpose**: Display payout history
- **Key Features**:
  - Date formatting with SimpleDateFormat
  - Status color coding
  - `updatePayouts(list)` method

---

## Layout Files

| File | Lines | Purpose |
|------|-------|---------|
| fragment_orders.xml | - | Order list RecyclerView + empty state |
| fragment_order_details.xml | - | Order details display + action buttons |
| fragment_earnings.xml | - | Earnings summary + period spinner + payout list |
| fragment_profile.xml | - | Profile info + online switch + action buttons |
| fragment_tracking.xml | - | Google Maps MapView |
| item_order.xml | 60 | Card-based order list item |
| item_payout.xml | 35 | Card-based payout history item |

---

## Dialog Patterns

### AlertDialog with Spinner (Status Update)
```kotlin
val statuses = arrayOf("picked_up", "in_transit", "delivered")
AlertDialog.Builder(requireContext())
    .setTitle("Update Status")
    .setSingleChoiceItems(statuses, selected) { _, which ->
        selectedStatus = statuses[which]
    }
    .setPositiveButton("Update") { _, _ ->
        viewModel.updateOrderStatus(id, selectedStatus)
    }
    .show()
```

### AlertDialog with EditText (Input)
```kotlin
val input = EditText(requireContext())
AlertDialog.Builder(requireContext())
    .setTitle("Request Payout")
    .setView(input)
    .setPositiveButton("Request") { _, _ ->
        val amount = input.text.toString().toDoubleOrNull() ?: 0.0
        if (amount > 0) viewModel.requestPayout(amount)
    }
    .show()
```

---

## Services & DI

### LocationService.kt
- Foreground service for location tracking
- Uses FusedLocationProviderClient
- Broadcasts location updates every 5 seconds
- Minimum update interval: 2 seconds

### AppModule.kt
- Retrofit configuration for API calls
- FusedLocationProviderClient provision
- Singleton scoped providers

---

## Navigation

### Navigation Graph: mobile_navigation.xml
**Main Destinations**:
- orders_fragment → order_details_fragment (action: action_orders_to_details)
- profile_fragment → login_activity (action: action_profile_to_login)

---

## Common Code Patterns

### ViewModel Observation Pattern
```kotlin
viewModel.selectedOrder.observe(viewLifecycleOwner) { order ->
    order?.let {
        orderIdText.text = "Order #${it.id}"
        // ... update other fields
    }
}
```

### Loading State Management
```kotlin
viewModel.orderState.observe(viewLifecycleOwner) { state ->
    when (state) {
        is OrderState.Loading -> progressBar.visibility = View.VISIBLE
        is OrderState.Success -> progressBar.visibility = View.GONE
        is OrderState.Error -> showError(state.message)
    }
}
```

### RecyclerView Setup
```kotlin
adapter = OrderAdapter { order ->
    // Handle item click
}
recyclerView.layoutManager = LinearLayoutManager(requireContext())
recyclerView.adapter = adapter
```

---

## Key Configuration

### Google Maps
- **API Key**: AIzaSyBplM3-vJV-H92Ej1lH6V8E8Yw1eVSrVhI
- **Location**: AndroidManifest.xml (meta-data)
- **Permissions**: ACCESS_FINE_LOCATION, ACCESS_COARSE_LOCATION

### Permissions
```xml
<uses-permission android:name="android.permission.INTERNET" />
<uses-permission android:name="android.permission.ACCESS_FINE_LOCATION" />
<uses-permission android:name="android.permission.ACCESS_COARSE_LOCATION" />
```

---

## File Locations Quick Index

```
rider-app/src/main/java/com/delivery/rider/
├── ui/
│   ├── orders/
│   │   ├── OrdersFragment.kt ✅
│   │   ├── OrderDetailsFragment.kt ✅
│   │   └── OrderAdapter.kt ✅
│   ├── earnings/
│   │   ├── EarningsFragment.kt ✅
│   │   └── PayoutAdapter.kt ✅
│   ├── profile/
│   │   └── ProfileFragment.kt ✅
│   ├── tracking/
│   │   └── TrackingFragment.kt ✅
│   └── viewmodel/
│       ├── OrderViewModel.kt
│       ├── EarningsViewModel.kt
│       ├── TrackingViewModel.kt
│       └── RiderViewModel.kt
├── service/
│   └── LocationService.kt ✅
└── di/
    └── AppModule.kt ✅

rider-app/src/main/res/layout/
├── fragment_orders.xml ✅
├── fragment_order_details.xml ✅
├── fragment_earnings.xml ✅
├── fragment_profile.xml ✅
├── fragment_tracking.xml ✅
├── item_order.xml ✅
└── item_payout.xml ✅
```

---

## Next Steps

1. **Run Build**: `./gradlew build`
2. **Create Emulator**: Android Studio AVD Manager
3. **Install APK**: `adb install -r app-debug.apk`
4. **Test Flows**: Login → Orders → Details → Earnings → Profile → Tracking
5. **Backend Integration**: Update API base URLs
6. **Deploy**: Sign APK for production

---

## Status: 🟢 COMPLETE

All 5 main fragments fully implemented with:
- ✅ RecyclerView adapters
- ✅ Dialog implementations
- ✅ LiveData observers
- ✅ Navigation setup
- ✅ Maps integration
- ✅ Location tracking

**Ready for testing and backend integration!**
