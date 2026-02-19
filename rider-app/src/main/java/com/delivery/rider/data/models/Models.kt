package com.delivery.rider.data.models

import com.google.gson.annotations.SerializedName

// ==================== Rider ====================

data class Rider(
    val id: String,
    val name: String,
    val phone: String,
    val email: String? = null,
    @SerializedName("profile_pic_url")
    val profilePicUrl: String? = null,
    @SerializedName("company_id")
    val companyId: String? = null,
    @SerializedName("companyName")
    val companyName: String? = null,
    @SerializedName("bikeId")
    val bikeId: String? = null,
    @SerializedName("fullName")
    val fullName: String? = null,
    val rating: Float = 0f,
    @SerializedName("total_deliveries")
    val totalDeliveries: Int = 0,
    @SerializedName("totalDeliveries")
    val totalDeliveriesAlt: Int = 0,
    @SerializedName("total_earnings")
    val totalEarnings: Float = 0f,
    @SerializedName("totalEarnings")
    val totalEarningsAlt: Float = 0f,
    val status: String = "offline",
    @SerializedName("created_at")
    val createdAt: Long = 0L,
    @SerializedName("verified")
    val verified: Boolean = false
) {
    fun displayName(): String = fullName ?: name
    fun deliveryCount(): Int = if (totalDeliveries > 0) totalDeliveries else totalDeliveriesAlt
    fun earningsTotal(): Float = if (totalEarnings > 0f) totalEarnings else totalEarningsAlt
}

// ==================== Order ====================

data class Order(
    val id: String,
    @SerializedName("pickup_address")
    val pickupAddress: String,
    @SerializedName("pickup_lat")
    val pickupLat: Double,
    @SerializedName("pickup_lng")
    val pickupLng: Double,
    @SerializedName("dropoff_address")
    val dropoffAddress: String,
    @SerializedName("dropoff_lat")
    val dropoffLat: Double,
    @SerializedName("dropoff_lng")
    val dropoffLng: Double,
    @SerializedName("distance_km")
    val distanceKm: Float,
    @SerializedName("eta_min")
    val etaMin: Int,
    @SerializedName("price_ghs")
    val priceGhs: Float,
    val status: String,
    @SerializedName("assigned_rider_id")
    val assignedRiderId: String? = null,
    @SerializedName("created_at")
    val createdAt: Long = 0L,
    @SerializedName("assigned_at")
    val assignedAt: Long? = null,
    @SerializedName("delivered_at")
    val deliveredAt: Long? = null,
    @SerializedName("merchant_id")
    val merchantId: String? = null,
    @SerializedName("tracking_link")
    val trackingLink: String? = null
)

// ==================== User ====================

data class User(
    val id: String,
    val name: String,
    val phone: String,
    val email: String,
    val role: String, // rider, merchant, admin, superadmin
    val status: String = "active",
    @SerializedName("created_at")
    val createdAt: Long = 0L
)

// Auth models moved to com.delivery.rider.data.api.ApiModels

// ==================== Earnings ====================

data class Earnings(
    val date: String,
    val amount: Float,
    val orders: Int,
    val distance: Float,
    @SerializedName("delivery_time")
    val deliveryTime: Int = 0
)

data class EarningsResponse(
    @SerializedName("daily")
    val daily: List<Earnings>,
    @SerializedName("weekly_total")
    val weeklyTotal: Float,
    @SerializedName("monthly_total")
    val monthlyTotal: Float,
    @SerializedName("total_earnings")
    val totalEarnings: Float
)

// ==================== Review ====================

data class Review(
    val id: String,
    val rating: Int,
    val comment: String,
    @SerializedName("merchant_name")
    val merchantName: String,
    @SerializedName("merchant_id")
    val merchantId: String,
    @SerializedName("created_at")
    val createdAt: Long
)

// ==================== Tracking ====================

data class TrackingData(
    @SerializedName("order_id")
    val orderId: String,
    @SerializedName("rider_id")
    val riderId: String,
    @SerializedName("current_lat")
    val currentLat: Double,
    @SerializedName("current_lng")
    val currentLng: Double,
    @SerializedName("is_active")
    val isActive: Boolean,
    @SerializedName("last_updated")
    val lastUpdated: Long
)

data class LocationUpdate(
    @SerializedName("order_id")
    val orderId: String,
    @SerializedName("rider_id")
    val riderId: String,
    val lat: Double,
    val lng: Double,
    val timestamp: Long
)

// ==================== Notification ====================

data class Notification(
    val id: String,
    val title: String,
    val message: String,
    val type: String, // order, payment, message, alert
    val data: Map<String, String>? = null,
    @SerializedName("is_read")
    val isRead: Boolean = false,
    @SerializedName("created_at")
    val createdAt: Long = 0L
)

// ==================== Payout ====================

data class Payout(
    val id: String,
    val amount: Float,
    val status: String, // pending, processing, completed, failed
    @SerializedName("created_at")
    val createdAt: Long,
    @SerializedName("processed_at")
    val processedAt: Long? = null
)

// PayoutRequest moved to com.delivery.rider.data.api.ApiModels

// ==================== Document ====================

data class Document(
    val id: String,
    @SerializedName("rider_id")
    val riderId: String,
    @SerializedName("doc_type")
    val docType: String, // license, insurance, id
    val filename: String,
    @SerializedName("expires_at")
    val expiresAt: Long? = null,
    @SerializedName("uploaded_at")
    val uploadedAt: Long = 0L,
    val status: String = "pending" // pending, approved, rejected, expired
)

// ApiResponse moved to com.delivery.rider.data.api.ApiModels

data class ListResponse<T>(
    val success: Boolean,
    val data: List<T>? = null,
    val message: String = ""
)
