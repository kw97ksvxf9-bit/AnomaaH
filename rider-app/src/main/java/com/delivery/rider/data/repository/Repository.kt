package com.delivery.rider.data.repository

import com.delivery.rider.data.api.ApiService
import com.delivery.rider.data.api.AuthRequest
import com.delivery.rider.data.api.ChangePasscodeRequest
import com.delivery.rider.data.api.OtpVerifyRequest
import com.delivery.rider.data.api.PasscodeLoginRequest
import com.delivery.rider.data.api.PayoutRequest
import com.delivery.rider.data.local.SharedPrefManager
import com.delivery.rider.data.models.*
import javax.inject.Inject

class AuthRepository @Inject constructor(
    private val apiService: ApiService,
    private val sharedPrefManager: SharedPrefManager
) {
    
    /** New passcode-based login: phone + 5-digit passcode → JWT + Rider */
    suspend fun passcodeLogin(phone: String, passcode: String): Result<Rider> = try {
        val response = apiService.passcodeLogin(PasscodeLoginRequest(phone, passcode))
        if (response.isSuccessful && response.body()?.success == true) {
            val data = response.body()
            data?.accessToken?.let { sharedPrefManager.saveAuthToken(it) }
            data?.data?.let {
                sharedPrefManager.saveRider(it)
                sharedPrefManager.setLastLoginTime(System.currentTimeMillis())
                Result.success(it)
            } ?: Result.failure(Exception("No rider data returned"))
        } else {
            val msg = response.body()?.message ?: "Invalid phone or passcode"
            Result.failure(Exception(msg))
        }
    } catch (e: Exception) {
        Result.failure(e)
    }
    
    /** Change passcode (rider must be authenticated) */
    suspend fun changePasscode(newPasscode: String): Result<Unit> = try {
        val response = apiService.changePasscode(ChangePasscodeRequest(newPasscode))
        if (response.isSuccessful && response.body()?.success == true) {
            Result.success(Unit)
        } else {
            Result.failure(Exception(response.body()?.message ?: "Failed to change passcode"))
        }
    } catch (e: Exception) {
        Result.failure(e)
    }
    
    /** Legacy login (kept for compatibility) */
    suspend fun login(phone: String): Result<String> = try {
        val response = apiService.login(AuthRequest(phone))
        if (response.isSuccessful && response.body()?.success == true) {
            Result.success(response.body()?.message ?: "OTP sent")
        } else {
            Result.failure(Exception(response.body()?.message ?: "Login failed"))
        }
    } catch (e: Exception) {
        Result.failure(e)
    }
    
    suspend fun verifyOtp(phone: String, otp: String): Result<Rider> = try {
        val response = apiService.verifyOtp(OtpVerifyRequest(phone, otp))
        if (response.isSuccessful && response.body()?.success == true) {
            val data = response.body()
            data?.accessToken?.let { sharedPrefManager.saveAuthToken(it) }
            data?.rider?.let {
                sharedPrefManager.saveRider(it)
                Result.success(it)
            } ?: Result.failure(Exception("No rider data"))
        } else {
            Result.failure(Exception(response.body()?.message ?: "OTP verification failed"))
        }
    } catch (e: Exception) {
        Result.failure(e)
    }
    
    suspend fun logout(): Result<Unit> = try {
        apiService.logout()
        sharedPrefManager.logout()
        Result.success(Unit)
    } catch (e: Exception) {
        sharedPrefManager.logout()
        Result.failure(e)
    }
    
    suspend fun getCurrentRider(): Result<Rider> = try {
        val response = apiService.getCurrentRider()
        if (response.isSuccessful && response.body()?.success == true) {
            response.body()?.data?.let {
                sharedPrefManager.saveRider(it)
                Result.success(it)
            } ?: Result.failure(Exception("No rider data"))
        } else {
            Result.failure(Exception(response.body()?.message ?: "Failed to get rider"))
        }
    } catch (e: Exception) {
        Result.failure(e)
    }
    
    fun isLoggedIn(): Boolean {
        return !sharedPrefManager.getAuthToken().isNullOrEmpty()
    }
    
    fun getLocalRider(): Rider? {
        return sharedPrefManager.getRider()
    }
}

class OrderRepository @Inject constructor(
    private val apiService: ApiService,
    private val sharedPrefManager: SharedPrefManager
) {
    
    suspend fun getRiderOrders(status: String? = null): Result<List<Order>> {
        val riderId = sharedPrefManager.getRiderId()
            ?: return Result.failure(Exception("Rider ID not found"))
        return try {
        val response = apiService.getRiderOrders(riderId, status)
        if (response.isSuccessful && response.body()?.success == true) {
            Result.success(response.body()?.data ?: emptyList())
        } else {
            Result.failure(Exception(response.body()?.message ?: "Failed to get orders"))
        }
        } catch (e: Exception) {
            Result.failure(e)
        }
    }
    
    suspend fun getOrderDetails(orderId: String): Result<Order> = try {
        val response = apiService.getOrderDetails(orderId)
        if (response.isSuccessful && response.body()?.success == true) {
            response.body()?.data?.let { Result.success(it) }
                ?: Result.failure(Exception("No order data"))
        } else {
            Result.failure(Exception(response.body()?.message ?: "Failed to get order"))
        }
    } catch (e: Exception) {
        Result.failure(e)
    }
    
    suspend fun updateOrderStatus(orderId: String, status: String, notes: String? = null): Result<Order> = try {
        val response = apiService.updateOrderStatus(
            orderId,
            com.delivery.rider.data.api.UpdateStatusRequest(status, notes)
        )
        if (response.isSuccessful && response.body()?.success == true) {
            response.body()?.data?.let { Result.success(it) }
                ?: Result.failure(Exception("No order data"))
        } else {
            Result.failure(Exception(response.body()?.message ?: "Failed to update status"))
        }
    } catch (e: Exception) {
        Result.failure(e)
    }
    
    suspend fun cancelOrder(orderId: String, reason: String): Result<Order> = try {
        val response = apiService.cancelOrder(
            orderId,
            com.delivery.rider.data.api.CancelOrderRequest(reason)
        )
        if (response.isSuccessful && response.body()?.success == true) {
            response.body()?.data?.let { Result.success(it) }
                ?: Result.failure(Exception("No order data"))
        } else {
            Result.failure(Exception(response.body()?.message ?: "Failed to cancel order"))
        }
    } catch (e: Exception) {
        Result.failure(e)
    }
}

class EarningsRepository @Inject constructor(
    private val apiService: ApiService,
    private val sharedPrefManager: SharedPrefManager
) {
    
    suspend fun getEarnings(period: String = "monthly"): Result<EarningsResponse> {
        val riderId = sharedPrefManager.getRiderId()
            ?: return Result.failure(Exception("Rider ID not found"))
        return try {
        val response = apiService.getEarnings(riderId, period)
        if (response.isSuccessful && response.body()?.success == true) {
            response.body()?.data?.let { Result.success(it) }
                ?: Result.failure(Exception("No earnings data"))
        } else {
            Result.failure(Exception(response.body()?.message ?: "Failed to get earnings"))
        }
        } catch (e: Exception) {
            Result.failure(e)
        }
    }
    
    suspend fun getPayoutHistory(): Result<List<Payout>> {
        val riderId = sharedPrefManager.getRiderId()
            ?: return Result.failure(Exception("Rider ID not found"))
        return try {
        val response = apiService.getPayoutHistory(riderId)
        if (response.isSuccessful && response.body()?.success == true) {
            Result.success(response.body()?.data ?: emptyList())
        } else {
            Result.failure(Exception(response.body()?.message ?: "Failed to get payouts"))
        }
        } catch (e: Exception) {
            Result.failure(e)
        }
    }
    
    suspend fun requestPayout(amount: Float): Result<Payout> = try {
        val response = apiService.requestPayout(PayoutRequest(amount))
        if (response.isSuccessful && response.body()?.success == true) {
            response.body()?.data?.let { Result.success(it) }
                ?: Result.failure(Exception("No payout data"))
        } else {
            Result.failure(Exception(response.body()?.message ?: "Failed to request payout"))
        }
    } catch (e: Exception) {
        Result.failure(e)
    }
}

class RiderRepository @Inject constructor(
    private val apiService: ApiService,
    private val sharedPrefManager: SharedPrefManager
) {
    
    suspend fun updateStatus(status: String): Result<Unit> {
        val riderId = sharedPrefManager.getRiderId()
            ?: return Result.failure(Exception("Rider ID not found"))
        return try {
        val response = apiService.updateStatus(com.delivery.rider.data.api.StatusUpdateRequest(riderId, status))
        if (response.isSuccessful && response.body()?.success == true) {
            sharedPrefManager.setOnlineStatus(status == "online")
            Result.success(Unit)
        } else {
            Result.failure(Exception(response.body()?.message ?: "Failed to update status"))
        }
        } catch (e: Exception) {
            Result.failure(e)
        }
    }
    
    suspend fun getRiderReviews(): Result<List<Review>> {
        val riderId = sharedPrefManager.getRiderId()
            ?: return Result.failure(Exception("Rider ID not found"))
        return try {
        val response = apiService.getRiderReviews(riderId)
        if (response.isSuccessful && response.body()?.success == true) {
            Result.success(response.body()?.data ?: emptyList())
        } else {
            Result.failure(Exception(response.body()?.message ?: "Failed to get reviews"))
        }
        } catch (e: Exception) {
            Result.failure(e)
        }
    }
    
    suspend fun updateProfile(name: String?, email: String?): Result<Rider> = try {
        val response = apiService.updateProfile(
            com.delivery.rider.data.api.UpdateProfileRequest(name, email)
        )
        if (response.isSuccessful && response.body()?.success == true) {
            response.body()?.data?.let {
                sharedPrefManager.saveRider(it)
                Result.success(it)
            } ?: Result.failure(Exception("No rider data"))
        } else {
            Result.failure(Exception(response.body()?.message ?: "Failed to update profile"))
        }
    } catch (e: Exception) {
        Result.failure(e)
    }
    
    fun getLocalRider(): Rider? {
        return sharedPrefManager.getRider()
    }
    
    fun logout() {
        sharedPrefManager.logout()
    }
}
