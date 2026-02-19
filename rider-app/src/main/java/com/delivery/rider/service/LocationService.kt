package com.delivery.rider.service

import android.app.Service
import android.content.Intent
import android.content.pm.PackageManager
import android.location.Location
import android.os.Build
import android.os.IBinder
import android.os.Looper
import androidx.core.app.ActivityCompat
import androidx.core.app.NotificationCompat
import com.google.android.gms.location.FusedLocationProviderClient
import com.google.android.gms.location.LocationCallback
import com.google.android.gms.location.LocationRequest
import com.google.android.gms.location.LocationResult
import com.google.android.gms.location.Priority
import com.google.android.gms.location.LocationServices
import com.delivery.rider.R
import dagger.hilt.android.AndroidEntryPoint
import javax.inject.Inject

@AndroidEntryPoint
class LocationService : Service() {
    
    @Inject
    lateinit var fusedLocationProviderClient: FusedLocationProviderClient
    
    private var locationCallback: LocationCallback? = null
    private val NOTIFICATION_ID = 999
    
    override fun onCreate() {
        super.onCreate()
        startForegroundNotification()
    }
    
    override fun onStartCommand(intent: Intent?, flags: Int, startId: Int): Int {
        startLocationUpdates()
        return START_STICKY
    }
    
    override fun onBind(intent: Intent?): IBinder? = null
    
    private fun startLocationUpdates() {
        val locationRequest = LocationRequest.Builder(Priority.PRIORITY_HIGH_ACCURACY, LOCATION_UPDATE_INTERVAL)
            .setMinUpdateIntervalMillis(FASTEST_LOCATION_INTERVAL)
            .build()
        
        locationCallback = object : LocationCallback() {
            override fun onLocationResult(locationResult: LocationResult) {
                val location = locationResult.lastLocation ?: return
                broadcastLocation(location)
            }
        }
        
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.S) {
            if (ActivityCompat.checkSelfPermission(
                    this,
                    android.Manifest.permission.ACCESS_FINE_LOCATION
                ) == PackageManager.PERMISSION_GRANTED
            ) {
                fusedLocationProviderClient.requestLocationUpdates(
                    locationRequest,
                    locationCallback!!,
                    Looper.getMainLooper()
                )
            }
        } else {
            @Suppress("DEPRECATION")
            if (ActivityCompat.checkSelfPermission(
                    this,
                    android.Manifest.permission.ACCESS_FINE_LOCATION
                ) == PackageManager.PERMISSION_GRANTED
            ) {
                fusedLocationProviderClient.requestLocationUpdates(
                    locationRequest,
                    locationCallback!!,
                    Looper.getMainLooper()
                )
            }
        }
    }
    
    private fun broadcastLocation(location: Location) {
        val intent = Intent(ACTION_LOCATION_UPDATE)
        intent.putExtra(EXTRA_LATITUDE, location.latitude)
        intent.putExtra(EXTRA_LONGITUDE, location.longitude)
        intent.putExtra(EXTRA_ACCURACY, location.accuracy)
        sendBroadcast(intent)
    }
    
    private fun startForegroundNotification() {
        val notification = NotificationCompat.Builder(this, "location_tracking")
            .setContentTitle("Location Tracking")
            .setContentText("Tracking your location for order delivery")
            .setSmallIcon(R.drawable.ic_launcher_foreground)
            .setPriority(NotificationCompat.PRIORITY_DEFAULT)
            .build()
        
        startForeground(NOTIFICATION_ID, notification)
    }
    
    override fun onDestroy() {
        super.onDestroy()
        locationCallback?.let {
            fusedLocationProviderClient.removeLocationUpdates(it)
        }
        stopForeground(STOP_FOREGROUND_REMOVE)
    }
    
    companion object {
        const val LOCATION_UPDATE_INTERVAL = 5000L // 5 seconds
        const val FASTEST_LOCATION_INTERVAL = 2000L // 2 seconds
        const val ACTION_LOCATION_UPDATE = "com.delivery.rider.LOCATION_UPDATE"
        const val EXTRA_LATITUDE = "latitude"
        const val EXTRA_LONGITUDE = "longitude"
        const val EXTRA_ACCURACY = "accuracy"
    }
}
