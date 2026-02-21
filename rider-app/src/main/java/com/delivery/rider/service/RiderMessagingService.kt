package com.delivery.rider.service

import android.app.NotificationManager
import android.app.PendingIntent
import android.content.Context
import android.content.Intent
import android.os.Build
import androidx.core.app.NotificationCompat
import com.delivery.rider.R
import com.delivery.rider.RiderApplication
import com.delivery.rider.ui.main.MainActivity
import com.google.firebase.messaging.FirebaseMessagingService
import com.google.firebase.messaging.RemoteMessage
import javax.inject.Inject
import com.delivery.rider.data.local.SharedPrefManager

class RiderMessagingService : FirebaseMessagingService() {
    
    @Inject
    lateinit var sharedPrefManager: SharedPrefManager
    
    override fun onNewToken(token: String) {
        super.onNewToken(token)
        // Send token to server for push notification targeting
        // TODO: Forward to backend API when endpoint is ready
    }
    
    override fun onMessageReceived(message: RemoteMessage) {
        super.onMessageReceived(message)
        
        val title = message.notification?.title ?: message.data["title"] ?: "Delivery Rider"
        val body = message.notification?.body ?: message.data["body"] ?: ""
        val type = message.data["type"] ?: "general"
        val orderId = message.data["order_id"]
        
        showNotification(title, body, type, orderId)
    }
    
    private fun showNotification(
        title: String,
        body: String,
        type: String,
        orderId: String?
    ) {
        val intent = Intent(this, MainActivity::class.java).apply {
            flags = Intent.FLAG_ACTIVITY_NEW_TASK or Intent.FLAG_ACTIVITY_CLEAR_TOP
            orderId?.let { putExtra("order_id", it) }
            putExtra("notification_type", type)
        }
        
        val pendingIntentFlags = if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.M) {
            PendingIntent.FLAG_IMMUTABLE or PendingIntent.FLAG_UPDATE_CURRENT
        } else {
            PendingIntent.FLAG_UPDATE_CURRENT
        }
        
        val pendingIntent = PendingIntent.getActivity(
            this, 0, intent, pendingIntentFlags
        )
        
        val notification = NotificationCompat.Builder(this, RiderApplication.CHANNEL_GENERAL)
            .setContentTitle(title)
            .setContentText(body)
            .setSmallIcon(R.drawable.ic_launcher_foreground)
            .setAutoCancel(true)
            .setContentIntent(pendingIntent)
            .setPriority(NotificationCompat.PRIORITY_HIGH)
            .build()
        
        val notificationManager = getSystemService(Context.NOTIFICATION_SERVICE) as NotificationManager
        notificationManager.notify(System.currentTimeMillis().toInt(), notification)
    }
}
