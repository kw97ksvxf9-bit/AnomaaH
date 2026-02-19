package com.delivery.rider.data.api

import com.google.gson.annotations.SerializedName

// Passcode Login Request (phone + 5-digit passcode)
data class PasscodeLoginRequest(
    @SerializedName("phone")
    val phone: String,
    @SerializedName("passcode")
    val passcode: String
)

// Change Passcode Request
data class ChangePasscodeRequest(
    @SerializedName("new_passcode")
    val newPasscode: String
)

// Legacy Auth (kept for compatibility)
data class AuthRequest(
    @SerializedName("phone")
    val phone: String
)

data class OtpVerifyRequest(
    @SerializedName("phone")
    val phone: String,
    @SerializedName("otp")
    val otp: String
)

// Generic API Response
data class ApiResponse<T>(
    @SerializedName("success")
    val success: Boolean,
    @SerializedName("message")
    val message: String? = null,
    @SerializedName("data")
    val data: T? = null,
    @SerializedName("accessToken")
    val accessToken: String? = null,
    @SerializedName("rider")
    val rider: com.delivery.rider.data.models.Rider? = null
)

// Order Updates
data class UpdateStatusRequest(
    @SerializedName("status")
    val status: String,
    @SerializedName("notes")
    val notes: String? = null
)

data class CancelOrderRequest(
    @SerializedName("reason")
    val reason: String
)

// Status Updates
data class StatusUpdateRequest(
    @SerializedName("riderId")
    val riderId: String,
    @SerializedName("status")
    val status: String
)

// Profile Updates
data class UpdateProfileRequest(
    @SerializedName("name")
    val name: String? = null,
    @SerializedName("email")
    val email: String? = null
)

// Location Update
data class LocationUpdateRequest(
    @SerializedName("latitude")
    val latitude: Double,
    @SerializedName("longitude")
    val longitude: Double,
    @SerializedName("accuracy")
    val accuracy: Float? = null
)

// Document Upload Response
data class DocumentUploadResponse(
    @SerializedName("url")
    val url: String,
    @SerializedName("documentId")
    val documentId: String
)

// Rating/Review Request
data class CreateReviewRequest(
    @SerializedName("orderId")
    val orderId: String,
    @SerializedName("customerId")
    val customerId: String,
    @SerializedName("rating")
    val rating: Float,
    @SerializedName("review")
    val review: String? = null
)

// Payout Request
data class PayoutRequest(
    @SerializedName("amount")
    val amount: Float
)

// Tracking Requests
data class TrackingStartRequest(
    @SerializedName("order_id")
    val orderId: String,
    @SerializedName("rider_id")
    val riderId: String
)

data class TrackingStopRequest(
    @SerializedName("order_id")
    val orderId: String,
    @SerializedName("rider_id")
    val riderId: String
)

// Documents
data class DocumentsResponse(
    val docs: List<com.delivery.rider.data.models.Document> = emptyList()
)
