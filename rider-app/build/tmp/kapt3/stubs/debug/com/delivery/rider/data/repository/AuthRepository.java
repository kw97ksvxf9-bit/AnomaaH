package com.delivery.rider.data.repository;

@kotlin.Metadata(mv = {1, 9, 0}, k = 1, xi = 48, d1 = {"\u0000:\n\u0002\u0018\u0002\n\u0002\u0010\u0000\n\u0000\n\u0002\u0018\u0002\n\u0000\n\u0002\u0018\u0002\n\u0002\b\u0002\n\u0002\u0018\u0002\n\u0002\u0010\u0002\n\u0000\n\u0002\u0010\u000e\n\u0002\b\u0003\n\u0002\u0018\u0002\n\u0002\b\u0004\n\u0002\u0010\u000b\n\u0002\b\r\u0018\u00002\u00020\u0001B\u0017\b\u0007\u0012\u0006\u0010\u0002\u001a\u00020\u0003\u0012\u0006\u0010\u0004\u001a\u00020\u0005\u00a2\u0006\u0002\u0010\u0006J$\u0010\u0007\u001a\b\u0012\u0004\u0012\u00020\t0\b2\u0006\u0010\n\u001a\u00020\u000bH\u0086@\u00f8\u0001\u0000\u00f8\u0001\u0001\u00a2\u0006\u0004\b\f\u0010\rJ\u001c\u0010\u000e\u001a\b\u0012\u0004\u0012\u00020\u000f0\bH\u0086@\u00f8\u0001\u0000\u00f8\u0001\u0001\u00a2\u0006\u0004\b\u0010\u0010\u0011J\b\u0010\u0012\u001a\u0004\u0018\u00010\u000fJ\u0006\u0010\u0013\u001a\u00020\u0014J$\u0010\u0015\u001a\b\u0012\u0004\u0012\u00020\u000b0\b2\u0006\u0010\u0016\u001a\u00020\u000bH\u0086@\u00f8\u0001\u0000\u00f8\u0001\u0001\u00a2\u0006\u0004\b\u0017\u0010\rJ\u001c\u0010\u0018\u001a\b\u0012\u0004\u0012\u00020\t0\bH\u0086@\u00f8\u0001\u0000\u00f8\u0001\u0001\u00a2\u0006\u0004\b\u0019\u0010\u0011J,\u0010\u001a\u001a\b\u0012\u0004\u0012\u00020\u000f0\b2\u0006\u0010\u0016\u001a\u00020\u000b2\u0006\u0010\u001b\u001a\u00020\u000bH\u0086@\u00f8\u0001\u0000\u00f8\u0001\u0001\u00a2\u0006\u0004\b\u001c\u0010\u001dJ,\u0010\u001e\u001a\b\u0012\u0004\u0012\u00020\u000f0\b2\u0006\u0010\u0016\u001a\u00020\u000b2\u0006\u0010\u001f\u001a\u00020\u000bH\u0086@\u00f8\u0001\u0000\u00f8\u0001\u0001\u00a2\u0006\u0004\b \u0010\u001dR\u000e\u0010\u0002\u001a\u00020\u0003X\u0082\u0004\u00a2\u0006\u0002\n\u0000R\u000e\u0010\u0004\u001a\u00020\u0005X\u0082\u0004\u00a2\u0006\u0002\n\u0000\u0082\u0002\u000b\n\u0002\b!\n\u0005\b\u00a1\u001e0\u0001\u00a8\u0006!"}, d2 = {"Lcom/delivery/rider/data/repository/AuthRepository;", "", "apiService", "Lcom/delivery/rider/data/api/ApiService;", "sharedPrefManager", "Lcom/delivery/rider/data/local/SharedPrefManager;", "(Lcom/delivery/rider/data/api/ApiService;Lcom/delivery/rider/data/local/SharedPrefManager;)V", "changePasscode", "Lkotlin/Result;", "", "newPasscode", "", "changePasscode-gIAlu-s", "(Ljava/lang/String;Lkotlin/coroutines/Continuation;)Ljava/lang/Object;", "getCurrentRider", "Lcom/delivery/rider/data/models/Rider;", "getCurrentRider-IoAF18A", "(Lkotlin/coroutines/Continuation;)Ljava/lang/Object;", "getLocalRider", "isLoggedIn", "", "login", "phone", "login-gIAlu-s", "logout", "logout-IoAF18A", "passcodeLogin", "passcode", "passcodeLogin-0E7RQCE", "(Ljava/lang/String;Ljava/lang/String;Lkotlin/coroutines/Continuation;)Ljava/lang/Object;", "verifyOtp", "otp", "verifyOtp-0E7RQCE", "DeliveryRiderApp_debug"})
public final class AuthRepository {
    @org.jetbrains.annotations.NotNull()
    private final com.delivery.rider.data.api.ApiService apiService = null;
    @org.jetbrains.annotations.NotNull()
    private final com.delivery.rider.data.local.SharedPrefManager sharedPrefManager = null;
    
    @javax.inject.Inject()
    public AuthRepository(@org.jetbrains.annotations.NotNull()
    com.delivery.rider.data.api.ApiService apiService, @org.jetbrains.annotations.NotNull()
    com.delivery.rider.data.local.SharedPrefManager sharedPrefManager) {
        super();
    }
    
    public final boolean isLoggedIn() {
        return false;
    }
    
    @org.jetbrains.annotations.Nullable()
    public final com.delivery.rider.data.models.Rider getLocalRider() {
        return null;
    }
}