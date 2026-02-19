package com.delivery.rider

import android.app.Application
import android.app.NotificationChannel
import android.app.NotificationManager
import android.os.Build
import dagger.hilt.android.HiltAndroidApp

@HiltAndroidApp
class RiderApplication : Application() {
    override fun onCreate() {
        super.onCreate()
        createNotificationChannels()
    }
    
    private fun createNotificationChannels() {
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
            val locationChannel = NotificationChannel(
                CHANNEL_LOCATION_TRACKING,
                "Location Tracking",
                NotificationManager.IMPORTANCE_LOW
            ).apply {
                description = "Shows when location is being tracked for deliveries"
            }
            
            val notificationChannel = NotificationChannel(
                CHANNEL_GENERAL,
                "General Notifications",
                NotificationManager.IMPORTANCE_DEFAULT
            ).apply {
                description = "Order updates, assignments, and alerts"
            }
            
            val manager = getSystemService(NotificationManager::class.java)
            manager.createNotificationChannel(locationChannel)
            manager.createNotificationChannel(notificationChannel)
        }
    }
    
    companion object {
        const val CHANNEL_LOCATION_TRACKING = "location_tracking"
        const val CHANNEL_GENERAL = "general_notifications"
    }
}
