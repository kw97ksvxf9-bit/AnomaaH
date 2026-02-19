package com.delivery.rider.data.local

import android.content.Context
import android.content.SharedPreferences
import androidx.security.crypto.EncryptedSharedPreferences
import androidx.security.crypto.MasterKey
import com.delivery.rider.data.models.Rider
import com.google.gson.Gson

class SharedPrefManager(context: Context) {
    private val masterKey = MasterKey.Builder(context)
        .setKeyScheme(MasterKey.KeyScheme.AES256_GCM)
        .build()
    
    private val sharedPreferences: SharedPreferences = 
        EncryptedSharedPreferences.create(
            context,
            "rider_app_prefs",
            masterKey,
            EncryptedSharedPreferences.PrefKeyEncryptionScheme.AES256_SIV,
            EncryptedSharedPreferences.PrefValueEncryptionScheme.AES256_GCM
        )
    
    private val gson = Gson()
    
    // ==================== Auth ====================
    
    fun saveAuthToken(token: String) {
        sharedPreferences.edit().putString(KEY_AUTH_TOKEN, token).apply()
    }
    
    fun getAuthToken(): String? {
        return sharedPreferences.getString(KEY_AUTH_TOKEN, null)
    }
    
    fun clearAuthToken() {
        sharedPreferences.edit().remove(KEY_AUTH_TOKEN).apply()
    }
    
    fun saveRefreshToken(token: String) {
        sharedPreferences.edit().putString(KEY_REFRESH_TOKEN, token).apply()
    }
    
    fun getRefreshToken(): String? {
        return sharedPreferences.getString(KEY_REFRESH_TOKEN, null)
    }
    
    // ==================== User/Rider ====================
    
    fun saveRider(rider: Rider) {
        val json = gson.toJson(rider)
        sharedPreferences.edit().putString(KEY_RIDER, json).apply()
    }
    
    fun getRider(): Rider? {
        val json = sharedPreferences.getString(KEY_RIDER, null)
        return if (json != null) {
            gson.fromJson(json, Rider::class.java)
        } else {
            null
        }
    }
    
    fun getRiderId(): String? {
        return getRider()?.id
    }
    
    fun clearRider() {
        sharedPreferences.edit().remove(KEY_RIDER).apply()
    }
    
    // ==================== Preferences ====================
    
    fun setUserLanguage(language: String) {
        sharedPreferences.edit().putString(KEY_LANGUAGE, language).apply()
    }
    
    fun getUserLanguage(): String {
        return sharedPreferences.getString(KEY_LANGUAGE, "en") ?: "en"
    }
    
    fun setNotificationsEnabled(enabled: Boolean) {
        sharedPreferences.edit().putBoolean(KEY_NOTIFICATIONS_ENABLED, enabled).apply()
    }
    
    fun areNotificationsEnabled(): Boolean {
        return sharedPreferences.getBoolean(KEY_NOTIFICATIONS_ENABLED, true)
    }
    
    fun setLocationTrackingEnabled(enabled: Boolean) {
        sharedPreferences.edit().putBoolean(KEY_LOCATION_TRACKING, enabled).apply()
    }
    
    fun isLocationTrackingEnabled(): Boolean {
        return sharedPreferences.getBoolean(KEY_LOCATION_TRACKING, true)
    }
    
    fun setOnlineStatus(online: Boolean) {
        sharedPreferences.edit().putBoolean(KEY_ONLINE_STATUS, online).apply()
    }
    
    fun isOnline(): Boolean {
        return sharedPreferences.getBoolean(KEY_ONLINE_STATUS, false)
    }
    
    // ==================== Session ====================
    
    fun setLastLoginTime(timestamp: Long) {
        sharedPreferences.edit().putLong(KEY_LAST_LOGIN, timestamp).apply()
    }
    
    fun getLastLoginTime(): Long {
        return sharedPreferences.getLong(KEY_LAST_LOGIN, 0L)
    }
    
    fun setLastLocationUpdateTime(timestamp: Long) {
        sharedPreferences.edit().putLong(KEY_LAST_LOCATION_UPDATE, timestamp).apply()
    }
    
    fun getLastLocationUpdateTime(): Long {
        return sharedPreferences.getLong(KEY_LAST_LOCATION_UPDATE, 0L)
    }
    
    // ==================== Clear All ====================
    
    fun clearAll() {
        sharedPreferences.edit().clear().apply()
    }
    
    fun logout() {
        clearAuthToken()
        clearRider()
        setOnlineStatus(false)
    }
    
    companion object {
        // Auth Keys
        private const val KEY_AUTH_TOKEN = "auth_token"
        private const val KEY_REFRESH_TOKEN = "refresh_token"
        
        // User Keys
        private const val KEY_RIDER = "rider"
        
        // Preference Keys
        private const val KEY_LANGUAGE = "language"
        private const val KEY_NOTIFICATIONS_ENABLED = "notifications_enabled"
        private const val KEY_LOCATION_TRACKING = "location_tracking"
        private const val KEY_ONLINE_STATUS = "online_status"
        
        // Session Keys
        private const val KEY_LAST_LOGIN = "last_login"
        private const val KEY_LAST_LOCATION_UPDATE = "last_location_update"
    }
}
