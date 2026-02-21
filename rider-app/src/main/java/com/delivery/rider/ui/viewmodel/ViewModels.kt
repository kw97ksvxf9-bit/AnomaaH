package com.delivery.rider.ui.viewmodel

import androidx.lifecycle.*
import com.delivery.rider.data.models.*
import com.delivery.rider.data.repository.*
import dagger.hilt.android.lifecycle.HiltViewModel
import kotlinx.coroutines.launch
import javax.inject.Inject

@HiltViewModel
class AuthViewModel @Inject constructor(
    private val authRepository: AuthRepository
) : ViewModel() {
    
    private val _loginState = MutableLiveData<LoginState>(LoginState.Idle)
    val loginState: LiveData<LoginState> = _loginState
    
    private val _currentRider = MutableLiveData<Rider?>()
    val currentRider: LiveData<Rider?> = _currentRider
    
    private val _changePasscodeState = MutableLiveData<ChangePasscodeState>(ChangePasscodeState.Idle)
    val changePasscodeState: LiveData<ChangePasscodeState> = _changePasscodeState
    
    /** Passcode login: phone + 5-digit code */
    fun passcodeLogin(phone: String, passcode: String) {
        _loginState.value = LoginState.Loading
        viewModelScope.launch {
            authRepository.passcodeLogin(phone, passcode).onSuccess { rider ->
                _currentRider.value = rider
                _loginState.value = LoginState.LoggedIn(rider)
            }.onFailure {
                _loginState.value = LoginState.Error(it.message ?: "Login failed")
            }
        }
    }
    
    /** Change passcode */
    fun changePasscode(newPasscode: String) {
        _changePasscodeState.value = ChangePasscodeState.Loading
        viewModelScope.launch {
            authRepository.changePasscode(newPasscode).onSuccess {
                _changePasscodeState.value = ChangePasscodeState.Success
            }.onFailure {
                _changePasscodeState.value = ChangePasscodeState.Error(it.message ?: "Failed")
            }
        }
    }
    
    fun resetChangePasscodeState() {
        _changePasscodeState.value = ChangePasscodeState.Idle
    }
    
    fun logout() {
        viewModelScope.launch {
            authRepository.logout()
            _currentRider.value = null
            _loginState.value = LoginState.Idle
        }
    }
    
    fun checkLoginStatus() {
        if (authRepository.isLoggedIn()) {
            _currentRider.value = authRepository.getLocalRider()
        }
    }
    
    fun isLoggedIn(): Boolean = authRepository.isLoggedIn()
    
    fun refreshRider() {
        viewModelScope.launch {
            authRepository.getCurrentRider().onSuccess {
                _currentRider.value = it
            }
        }
    }
}

sealed class LoginState {
    object Idle : LoginState()
    object Loading : LoginState()
    data class LoggedIn(val rider: Rider) : LoginState()
    data class Success(val message: String) : LoginState()
    data class Error(val message: String) : LoginState()
}

sealed class ChangePasscodeState {
    object Idle : ChangePasscodeState()
    object Loading : ChangePasscodeState()
    object Success : ChangePasscodeState()
    data class Error(val message: String) : ChangePasscodeState()
}

sealed class OtpState {
    object Idle : OtpState()
    object Loading : OtpState()
    object Success : OtpState()
    data class Error(val message: String) : OtpState()
}

@HiltViewModel
class OrderViewModel @Inject constructor(
    private val orderRepository: OrderRepository
) : ViewModel() {
    
    private val _orders = MutableLiveData<List<Order>>()
    val orders: LiveData<List<Order>> = _orders
    
    private val _selectedOrder = MutableLiveData<Order?>()
    val selectedOrder: LiveData<Order?> = _selectedOrder
    
    private val _orderState = MutableLiveData<OrderState>(OrderState.Idle)
    val orderState: LiveData<OrderState> = _orderState
    
    private val _filterStatus = MutableLiveData<String?>(null)
    
    fun loadOrders(status: String? = null) {
        _orderState.value = OrderState.Loading
        _filterStatus.value = status
        viewModelScope.launch {
            orderRepository.getRiderOrders(status).onSuccess { list ->
                _orders.value = list
                _orderState.value = OrderState.Success
            }.onFailure {
                _orderState.value = OrderState.Error(it.message ?: "Failed to load orders")
            }
        }
    }
    
    fun loadOrderDetails(orderId: String) {
        viewModelScope.launch {
            orderRepository.getOrderDetails(orderId).onSuccess {
                _selectedOrder.value = it
            }.onFailure {
                _orderState.value = OrderState.Error(it.message ?: "Failed to load order")
            }
        }
    }
    
    fun updateOrderStatus(orderId: String, status: String, notes: String? = null) {
        viewModelScope.launch {
            orderRepository.updateOrderStatus(orderId, status, notes).onSuccess {
                _selectedOrder.value = it
                loadOrders(_filterStatus.value)
            }.onFailure {
                _orderState.value = OrderState.Error(it.message ?: "Failed to update status")
            }
        }
    }
    
    fun cancelOrder(orderId: String, reason: String) {
        viewModelScope.launch {
            orderRepository.cancelOrder(orderId, reason).onSuccess {
                _selectedOrder.value = it
                loadOrders(_filterStatus.value)
            }.onFailure {
                _orderState.value = OrderState.Error(it.message ?: "Failed to cancel order")
            }
        }
    }
}

sealed class OrderState {
    object Idle : OrderState()
    object Loading : OrderState()
    object Success : OrderState()
    data class Error(val message: String) : OrderState()
}

@HiltViewModel
class EarningsViewModel @Inject constructor(
    private val earningsRepository: EarningsRepository
) : ViewModel() {
    
    private val _earnings = MutableLiveData<EarningsResponse?>()
    val earnings: LiveData<EarningsResponse?> = _earnings
    
    private val _payouts = MutableLiveData<List<Payout>>()
    val payouts: LiveData<List<Payout>> = _payouts
    
    private val _earningsState = MutableLiveData<EarningsState>(EarningsState.Idle)
    val earningsState: LiveData<EarningsState> = _earningsState
    
    private val _period = MutableLiveData("monthly")
    
    fun loadEarnings(period: String = "monthly") {
        _earningsState.value = EarningsState.Loading
        _period.value = period
        viewModelScope.launch {
            earningsRepository.getEarnings(period).onSuccess {
                _earnings.value = it
                _earningsState.value = EarningsState.Success
            }.onFailure {
                _earningsState.value = EarningsState.Error(it.message ?: "Failed to load earnings")
            }
        }
    }
    
    fun loadPayoutHistory() {
        viewModelScope.launch {
            earningsRepository.getPayoutHistory().onSuccess {
                _payouts.value = it
            }.onFailure {
                _earningsState.value = EarningsState.Error(it.message ?: "Failed to load payouts")
            }
        }
    }
    
    fun requestPayout(amount: Float) {
        _earningsState.value = EarningsState.Loading
        viewModelScope.launch {
            earningsRepository.requestPayout(amount).onSuccess {
                _earningsState.value = EarningsState.PayoutRequested(it)
                loadPayoutHistory()
            }.onFailure {
                _earningsState.value = EarningsState.Error(it.message ?: "Failed to request payout")
            }
        }
    }
}

sealed class EarningsState {
    object Idle : EarningsState()
    object Loading : EarningsState()
    object Success : EarningsState()
    data class PayoutRequested(val payout: Payout) : EarningsState()
    data class Error(val message: String) : EarningsState()
}

@HiltViewModel
class RiderViewModel @Inject constructor(
    private val riderRepository: RiderRepository
) : ViewModel() {
    
    private val _riderProfile = MutableLiveData<Rider?>()
    val riderProfile: LiveData<Rider?> = _riderProfile
    
    private val _isOnline = MutableLiveData(false)
    val isOnline: LiveData<Boolean> = _isOnline
    
    private val _reviews = MutableLiveData<List<Review>>()
    val reviews: LiveData<List<Review>> = _reviews
    
    private val _riderState = MutableLiveData<RiderState>(RiderState.Idle)
    val riderState: LiveData<RiderState> = _riderState
    
    init {
        loadProfile()
    }
    
    fun loadProfile() {
        _riderProfile.value = riderRepository.getLocalRider()
    }
    
    fun logout() {
        viewModelScope.launch {
            riderRepository.logout()
            _riderProfile.value = null
            _isOnline.value = false
        }
    }
    
    fun updateStatus(status: String) {
        viewModelScope.launch {
            riderRepository.updateStatus(status).onSuccess {
                _isOnline.value = status == "online"
                _riderState.value = RiderState.StatusUpdated
            }.onFailure {
                _riderState.value = RiderState.Error(it.message ?: "Failed to update status")
            }
        }
    }
    
    fun loadReviews() {
        _riderState.value = RiderState.Loading
        viewModelScope.launch {
            riderRepository.getRiderReviews().onSuccess {
                _reviews.value = it
                _riderState.value = RiderState.Success
            }.onFailure {
                _riderState.value = RiderState.Error(it.message ?: "Failed to load reviews")
            }
        }
    }
    
    fun updateProfile(name: String?, email: String?) {
        _riderState.value = RiderState.Loading
        viewModelScope.launch {
            riderRepository.updateProfile(name, email).onSuccess {
                _riderProfile.value = it
                _riderState.value = RiderState.ProfileUpdated(it)
            }.onFailure {
                _riderState.value = RiderState.Error(it.message ?: "Failed to update profile")
            }
        }
    }
}

@HiltViewModel
class NotificationViewModel @Inject constructor(
    private val riderRepository: com.delivery.rider.data.repository.RiderRepository
) : ViewModel() {
    private val _notifications = MutableLiveData<List<com.delivery.rider.data.models.Notification>>(emptyList())
    val notifications: LiveData<List<com.delivery.rider.data.models.Notification>> = _notifications

    fun loadNotifications() {
        viewModelScope.launch {
            riderRepository.getNotifications().onSuccess {
                _notifications.value = it
            }.onFailure {
                // ignore or log
                android.util.Log.e("NotifVM", "loadNotifications error", it)
            }
        }
    }
}

sealed class RiderState {
    object Idle : RiderState()
    object Loading : RiderState()
    object Success : RiderState()
    object StatusUpdated : RiderState()
    data class ProfileUpdated(val rider: Rider) : RiderState()
    data class Error(val message: String) : RiderState()
}
