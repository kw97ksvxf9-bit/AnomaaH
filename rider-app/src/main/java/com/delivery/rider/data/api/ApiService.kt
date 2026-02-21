package com.delivery.rider.data.api

import com.delivery.rider.data.models.Document
import com.delivery.rider.data.models.EarningsResponse
import com.delivery.rider.data.models.ListResponse
import com.delivery.rider.data.models.Notification
import com.delivery.rider.data.models.Order
import com.delivery.rider.data.models.Payout
import com.delivery.rider.data.models.Review
import com.delivery.rider.data.models.Rider
import com.delivery.rider.data.models.TrackingData
import com.delivery.rider.data.models.LocationUpdate
import retrofit2.Response
import retrofit2.http.*

interface ApiService {
    
    // ==================== Authentication ====================
    
    @POST("rider/passcode-login")
    suspend fun passcodeLogin(@Body request: PasscodeLoginRequest): Response<ApiResponse<Rider>>
    
    @POST("rider/change-passcode")
    suspend fun changePasscode(@Body request: ChangePasscodeRequest): Response<ApiResponse<Unit>>
    
    @POST("auth/login")
    suspend fun login(@Body request: AuthRequest): Response<ApiResponse<Rider>>
    
    @POST("auth/verify-otp")
    suspend fun verifyOtp(@Body request: OtpVerifyRequest): Response<ApiResponse<Rider>>
    
    @POST("auth/logout")
    suspend fun logout(): Response<ApiResponse<Unit>>
    
    @GET("auth/me")
    suspend fun getCurrentRider(): Response<ApiResponse<Rider>>
    
    // ==================== Orders ====================
    
    @GET("orders/rider/{rider_id}")
    suspend fun getRiderOrders(
        @Path("rider_id") riderId: String,
        @Query("status") status: String? = null
    ): Response<ListResponse<Order>>
    
    @GET("orders/{order_id}")
    suspend fun getOrderDetails(
        @Path("order_id") orderId: String
    ): Response<ApiResponse<Order>>
    
    @POST("orders/{order_id}/update-status")
    suspend fun updateOrderStatus(
        @Path("order_id") orderId: String,
        @Body request: UpdateStatusRequest
    ): Response<ApiResponse<Order>>
    
    @POST("orders/{order_id}/cancel")
    suspend fun cancelOrder(
        @Path("order_id") orderId: String,
        @Body request: CancelOrderRequest
    ): Response<ApiResponse<Order>>
    
    // ==================== Tracking ====================
    
    @POST("tracking/start")
    suspend fun startTracking(
        @Body request: TrackingStartRequest
    ): Response<ApiResponse<TrackingData>>
    
    @POST("tracking/location")
    suspend fun updateLocation(
        @Body request: LocationUpdate
    ): Response<ApiResponse<Unit>>
    
    @GET("tracking/order/{order_id}")
    suspend fun getTrackingInfo(
        @Path("order_id") orderId: String
    ): Response<ApiResponse<TrackingData>>
    
    @POST("tracking/stop")
    suspend fun stopTracking(
        @Body request: TrackingStopRequest
    ): Response<ApiResponse<Unit>>
    
    // ==================== Rider Status ====================
    
    // STATUS_SERVICE_URL may be different from API_BASE_URL, call with full URL via @Url
    @POST
    suspend fun updateStatus(
        @Url url: String,
        @Body request: StatusUpdateRequest
    ): Response<ApiResponse<Unit>>
    
    @GET("status/{rider_id}")
    suspend fun getRiderStatus(
        @Path("rider_id") riderId: String
    ): Response<ApiResponse<String>>
    
    // ==================== Earnings ====================
    
    @GET("earnings/{rider_id}")
    suspend fun getEarnings(
        @Path("rider_id") riderId: String,
        @Query("period") period: String = "monthly"
    ): Response<ApiResponse<EarningsResponse>>
    
    @GET("payouts/{rider_id}")
    suspend fun getPayoutHistory(
        @Path("rider_id") riderId: String,
        @Query("limit") limit: Int = 20
    ): Response<ListResponse<Payout>>
    
    @POST("payouts/request")
    suspend fun requestPayout(
        @Body request: PayoutRequest
    ): Response<ApiResponse<Payout>>
    
    // ==================== Reviews ====================
    
    @GET("reviews/rider/{rider_id}")
    suspend fun getRiderReviews(
        @Path("rider_id") riderId: String,
        @Query("limit") limit: Int = 20
    ): Response<ListResponse<Review>>
    
    @GET("ratings/rider/{rider_id}")
    suspend fun getRiderRatings(
        @Path("rider_id") riderId: String
    ): Response<ApiResponse<Map<String, Any>>>
    
    // ==================== Documents ====================
    
    @GET("docs/{rider_id}")
    suspend fun getRiderDocuments(
        @Path("rider_id") riderId: String
    ): Response<ApiResponse<DocumentsResponse>>
    
    @Multipart
    @POST("docs/upload")
    suspend fun uploadDocument(
        @Part("rider_id") riderId: String,
        @Part("doc_type") docType: String,
        @Part("expires_at") expiresAt: String? = null,
        @Part file: okhttp3.MultipartBody.Part
    ): Response<ApiResponse<Document>>
    
    // ==================== Notifications ====================
    
    // notifications may reside on separate service; call with full URL via @Url
    @GET
    suspend fun getNotifications(
        @Url url: String,
        @Query("limit") limit: Int = 20,
        @Query("offset") offset: Int = 0
    ): Response<ListResponse<Notification>>
    
    @POST("notifications/{id}/read")
    suspend fun markNotificationAsRead(
        @Path("id") notificationId: String
    ): Response<ApiResponse<Unit>>
    
    // ==================== Rider Profile ====================
    
    @PUT("rider/profile")
    suspend fun updateProfile(
        @Body request: UpdateProfileRequest
    ): Response<ApiResponse<Rider>>
    
    @GET("rider/{rider_id}")
    suspend fun getRiderProfile(
        @Path("rider_id") riderId: String
    ): Response<ApiResponse<Rider>>
}
