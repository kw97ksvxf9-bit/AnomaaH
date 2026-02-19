package com.delivery.rider.ui.viewmodel

import android.location.Location
import androidx.lifecycle.LiveData
import androidx.lifecycle.MutableLiveData
import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.delivery.rider.data.models.Order
import com.delivery.rider.data.repository.OrderRepository
import dagger.hilt.android.lifecycle.HiltViewModel
import kotlinx.coroutines.launch
import javax.inject.Inject

@HiltViewModel
class TrackingViewModel @Inject constructor(
    private val orderRepository: OrderRepository
) : ViewModel() {
    
    private val _currentOrder = MutableLiveData<Order?>()
    val currentOrder: LiveData<Order?> = _currentOrder
    
    private val _currentLocation = MutableLiveData<Location?>()
    val currentLocation: LiveData<Location?> = _currentLocation
    
    private val _distanceToDestination = MutableLiveData<String>()
    val distanceToDestination: LiveData<String> = _distanceToDestination
    
    private val _isTracking = MutableLiveData(false)
    val isTracking: LiveData<Boolean> = _isTracking
    
    fun setCurrentOrder(order: Order) {
        _currentOrder.value = order
    }
    
    fun updateLocation(location: Location) {
        _currentLocation.value = location
        calculateDistance(location)
    }
    
    fun startTracking() {
        _isTracking.value = true
    }
    
    fun stopTracking() {
        _isTracking.value = false
    }
    
    private fun calculateDistance(riderLocation: Location) {
        val order = _currentOrder.value ?: return
        
        // Determine destination based on order status
        val destLat: Double
        val destLng: Double
        
        when (order.status.lowercase()) {
            "assigned", "picked_up" -> {
                // Navigate to pickup
                destLat = order.pickupLat
                destLng = order.pickupLng
            }
            "in_transit" -> {
                // Navigate to dropoff
                destLat = order.dropoffLat
                destLng = order.dropoffLng
            }
            else -> {
                _distanceToDestination.value = "--"
                return
            }
        }
        
        val destLocation = Location("destination").apply {
            latitude = destLat
            longitude = destLng
        }
        
        val distanceMeters = riderLocation.distanceTo(destLocation)
        val distanceKm = distanceMeters / 1000.0
        
        _distanceToDestination.value = String.format("%.1f", distanceKm)
    }
}
