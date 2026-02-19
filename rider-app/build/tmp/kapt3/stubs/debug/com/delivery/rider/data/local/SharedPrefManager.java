package com.delivery.rider.data.local;

@kotlin.Metadata(mv = {1, 9, 0}, k = 1, xi = 48, d1 = {"\u0000H\n\u0002\u0018\u0002\n\u0002\u0010\u0000\n\u0000\n\u0002\u0018\u0002\n\u0002\b\u0002\n\u0002\u0018\u0002\n\u0000\n\u0002\u0018\u0002\n\u0000\n\u0002\u0018\u0002\n\u0000\n\u0002\u0010\u000b\n\u0000\n\u0002\u0010\u0002\n\u0002\b\u0003\n\u0002\u0010\u000e\n\u0000\n\u0002\u0010\t\n\u0002\b\u0003\n\u0002\u0018\u0002\n\u0002\b\u0016\u0018\u0000 -2\u00020\u0001:\u0001-B\r\u0012\u0006\u0010\u0002\u001a\u00020\u0003\u00a2\u0006\u0002\u0010\u0004J\u0006\u0010\u000b\u001a\u00020\fJ\u0006\u0010\r\u001a\u00020\u000eJ\u0006\u0010\u000f\u001a\u00020\u000eJ\u0006\u0010\u0010\u001a\u00020\u000eJ\b\u0010\u0011\u001a\u0004\u0018\u00010\u0012J\u0006\u0010\u0013\u001a\u00020\u0014J\u0006\u0010\u0015\u001a\u00020\u0014J\b\u0010\u0016\u001a\u0004\u0018\u00010\u0012J\b\u0010\u0017\u001a\u0004\u0018\u00010\u0018J\b\u0010\u0019\u001a\u0004\u0018\u00010\u0012J\u0006\u0010\u001a\u001a\u00020\u0012J\u0006\u0010\u001b\u001a\u00020\fJ\u0006\u0010\u001c\u001a\u00020\fJ\u0006\u0010\u001d\u001a\u00020\u000eJ\u000e\u0010\u001e\u001a\u00020\u000e2\u0006\u0010\u001f\u001a\u00020\u0012J\u000e\u0010 \u001a\u00020\u000e2\u0006\u0010\u001f\u001a\u00020\u0012J\u000e\u0010!\u001a\u00020\u000e2\u0006\u0010\"\u001a\u00020\u0018J\u000e\u0010#\u001a\u00020\u000e2\u0006\u0010$\u001a\u00020\u0014J\u000e\u0010%\u001a\u00020\u000e2\u0006\u0010$\u001a\u00020\u0014J\u000e\u0010&\u001a\u00020\u000e2\u0006\u0010\'\u001a\u00020\fJ\u000e\u0010(\u001a\u00020\u000e2\u0006\u0010\'\u001a\u00020\fJ\u000e\u0010)\u001a\u00020\u000e2\u0006\u0010*\u001a\u00020\fJ\u000e\u0010+\u001a\u00020\u000e2\u0006\u0010,\u001a\u00020\u0012R\u000e\u0010\u0005\u001a\u00020\u0006X\u0082\u0004\u00a2\u0006\u0002\n\u0000R\u000e\u0010\u0007\u001a\u00020\bX\u0082\u0004\u00a2\u0006\u0002\n\u0000R\u000e\u0010\t\u001a\u00020\nX\u0082\u0004\u00a2\u0006\u0002\n\u0000\u00a8\u0006."}, d2 = {"Lcom/delivery/rider/data/local/SharedPrefManager;", "", "context", "Landroid/content/Context;", "(Landroid/content/Context;)V", "gson", "Lcom/google/gson/Gson;", "masterKey", "Landroidx/security/crypto/MasterKey;", "sharedPreferences", "Landroid/content/SharedPreferences;", "areNotificationsEnabled", "", "clearAll", "", "clearAuthToken", "clearRider", "getAuthToken", "", "getLastLocationUpdateTime", "", "getLastLoginTime", "getRefreshToken", "getRider", "Lcom/delivery/rider/data/models/Rider;", "getRiderId", "getUserLanguage", "isLocationTrackingEnabled", "isOnline", "logout", "saveAuthToken", "token", "saveRefreshToken", "saveRider", "rider", "setLastLocationUpdateTime", "timestamp", "setLastLoginTime", "setLocationTrackingEnabled", "enabled", "setNotificationsEnabled", "setOnlineStatus", "online", "setUserLanguage", "language", "Companion", "DeliveryRiderApp_debug"})
public final class SharedPrefManager {
    @org.jetbrains.annotations.NotNull()
    private final androidx.security.crypto.MasterKey masterKey = null;
    @org.jetbrains.annotations.NotNull()
    private final android.content.SharedPreferences sharedPreferences = null;
    @org.jetbrains.annotations.NotNull()
    private final com.google.gson.Gson gson = null;
    @org.jetbrains.annotations.NotNull()
    private static final java.lang.String KEY_AUTH_TOKEN = "auth_token";
    @org.jetbrains.annotations.NotNull()
    private static final java.lang.String KEY_REFRESH_TOKEN = "refresh_token";
    @org.jetbrains.annotations.NotNull()
    private static final java.lang.String KEY_RIDER = "rider";
    @org.jetbrains.annotations.NotNull()
    private static final java.lang.String KEY_LANGUAGE = "language";
    @org.jetbrains.annotations.NotNull()
    private static final java.lang.String KEY_NOTIFICATIONS_ENABLED = "notifications_enabled";
    @org.jetbrains.annotations.NotNull()
    private static final java.lang.String KEY_LOCATION_TRACKING = "location_tracking";
    @org.jetbrains.annotations.NotNull()
    private static final java.lang.String KEY_ONLINE_STATUS = "online_status";
    @org.jetbrains.annotations.NotNull()
    private static final java.lang.String KEY_LAST_LOGIN = "last_login";
    @org.jetbrains.annotations.NotNull()
    private static final java.lang.String KEY_LAST_LOCATION_UPDATE = "last_location_update";
    @org.jetbrains.annotations.NotNull()
    public static final com.delivery.rider.data.local.SharedPrefManager.Companion Companion = null;
    
    public SharedPrefManager(@org.jetbrains.annotations.NotNull()
    android.content.Context context) {
        super();
    }
    
    public final void saveAuthToken(@org.jetbrains.annotations.NotNull()
    java.lang.String token) {
    }
    
    @org.jetbrains.annotations.Nullable()
    public final java.lang.String getAuthToken() {
        return null;
    }
    
    public final void clearAuthToken() {
    }
    
    public final void saveRefreshToken(@org.jetbrains.annotations.NotNull()
    java.lang.String token) {
    }
    
    @org.jetbrains.annotations.Nullable()
    public final java.lang.String getRefreshToken() {
        return null;
    }
    
    public final void saveRider(@org.jetbrains.annotations.NotNull()
    com.delivery.rider.data.models.Rider rider) {
    }
    
    @org.jetbrains.annotations.Nullable()
    public final com.delivery.rider.data.models.Rider getRider() {
        return null;
    }
    
    @org.jetbrains.annotations.Nullable()
    public final java.lang.String getRiderId() {
        return null;
    }
    
    public final void clearRider() {
    }
    
    public final void setUserLanguage(@org.jetbrains.annotations.NotNull()
    java.lang.String language) {
    }
    
    @org.jetbrains.annotations.NotNull()
    public final java.lang.String getUserLanguage() {
        return null;
    }
    
    public final void setNotificationsEnabled(boolean enabled) {
    }
    
    public final boolean areNotificationsEnabled() {
        return false;
    }
    
    public final void setLocationTrackingEnabled(boolean enabled) {
    }
    
    public final boolean isLocationTrackingEnabled() {
        return false;
    }
    
    public final void setOnlineStatus(boolean online) {
    }
    
    public final boolean isOnline() {
        return false;
    }
    
    public final void setLastLoginTime(long timestamp) {
    }
    
    public final long getLastLoginTime() {
        return 0L;
    }
    
    public final void setLastLocationUpdateTime(long timestamp) {
    }
    
    public final long getLastLocationUpdateTime() {
        return 0L;
    }
    
    public final void clearAll() {
    }
    
    public final void logout() {
    }
    
    @kotlin.Metadata(mv = {1, 9, 0}, k = 1, xi = 48, d1 = {"\u0000\u0014\n\u0002\u0018\u0002\n\u0002\u0010\u0000\n\u0002\b\u0002\n\u0002\u0010\u000e\n\u0002\b\t\b\u0086\u0003\u0018\u00002\u00020\u0001B\u0007\b\u0002\u00a2\u0006\u0002\u0010\u0002R\u000e\u0010\u0003\u001a\u00020\u0004X\u0082T\u00a2\u0006\u0002\n\u0000R\u000e\u0010\u0005\u001a\u00020\u0004X\u0082T\u00a2\u0006\u0002\n\u0000R\u000e\u0010\u0006\u001a\u00020\u0004X\u0082T\u00a2\u0006\u0002\n\u0000R\u000e\u0010\u0007\u001a\u00020\u0004X\u0082T\u00a2\u0006\u0002\n\u0000R\u000e\u0010\b\u001a\u00020\u0004X\u0082T\u00a2\u0006\u0002\n\u0000R\u000e\u0010\t\u001a\u00020\u0004X\u0082T\u00a2\u0006\u0002\n\u0000R\u000e\u0010\n\u001a\u00020\u0004X\u0082T\u00a2\u0006\u0002\n\u0000R\u000e\u0010\u000b\u001a\u00020\u0004X\u0082T\u00a2\u0006\u0002\n\u0000R\u000e\u0010\f\u001a\u00020\u0004X\u0082T\u00a2\u0006\u0002\n\u0000\u00a8\u0006\r"}, d2 = {"Lcom/delivery/rider/data/local/SharedPrefManager$Companion;", "", "()V", "KEY_AUTH_TOKEN", "", "KEY_LANGUAGE", "KEY_LAST_LOCATION_UPDATE", "KEY_LAST_LOGIN", "KEY_LOCATION_TRACKING", "KEY_NOTIFICATIONS_ENABLED", "KEY_ONLINE_STATUS", "KEY_REFRESH_TOKEN", "KEY_RIDER", "DeliveryRiderApp_debug"})
    public static final class Companion {
        
        private Companion() {
            super();
        }
    }
}