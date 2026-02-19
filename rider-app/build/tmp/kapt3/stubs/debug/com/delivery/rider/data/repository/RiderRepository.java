package com.delivery.rider.data.repository;

@kotlin.Metadata(mv = {1, 9, 0}, k = 1, xi = 48, d1 = {"\u0000>\n\u0002\u0018\u0002\n\u0002\u0010\u0000\n\u0000\n\u0002\u0018\u0002\n\u0000\n\u0002\u0018\u0002\n\u0002\b\u0002\n\u0002\u0018\u0002\n\u0000\n\u0002\u0018\u0002\n\u0002\u0010 \n\u0002\u0018\u0002\n\u0002\b\u0003\n\u0002\u0010\u0002\n\u0002\b\u0002\n\u0002\u0010\u000e\n\u0002\b\b\u0018\u00002\u00020\u0001B\u0017\b\u0007\u0012\u0006\u0010\u0002\u001a\u00020\u0003\u0012\u0006\u0010\u0004\u001a\u00020\u0005\u00a2\u0006\u0002\u0010\u0006J\b\u0010\u0007\u001a\u0004\u0018\u00010\bJ\"\u0010\t\u001a\u000e\u0012\n\u0012\b\u0012\u0004\u0012\u00020\f0\u000b0\nH\u0086@\u00f8\u0001\u0000\u00f8\u0001\u0001\u00a2\u0006\u0004\b\r\u0010\u000eJ\u0006\u0010\u000f\u001a\u00020\u0010J0\u0010\u0011\u001a\b\u0012\u0004\u0012\u00020\b0\n2\b\u0010\u0012\u001a\u0004\u0018\u00010\u00132\b\u0010\u0014\u001a\u0004\u0018\u00010\u0013H\u0086@\u00f8\u0001\u0000\u00f8\u0001\u0001\u00a2\u0006\u0004\b\u0015\u0010\u0016J$\u0010\u0017\u001a\b\u0012\u0004\u0012\u00020\u00100\n2\u0006\u0010\u0018\u001a\u00020\u0013H\u0086@\u00f8\u0001\u0000\u00f8\u0001\u0001\u00a2\u0006\u0004\b\u0019\u0010\u001aR\u000e\u0010\u0002\u001a\u00020\u0003X\u0082\u0004\u00a2\u0006\u0002\n\u0000R\u000e\u0010\u0004\u001a\u00020\u0005X\u0082\u0004\u00a2\u0006\u0002\n\u0000\u0082\u0002\u000b\n\u0002\b!\n\u0005\b\u00a1\u001e0\u0001\u00a8\u0006\u001b"}, d2 = {"Lcom/delivery/rider/data/repository/RiderRepository;", "", "apiService", "Lcom/delivery/rider/data/api/ApiService;", "sharedPrefManager", "Lcom/delivery/rider/data/local/SharedPrefManager;", "(Lcom/delivery/rider/data/api/ApiService;Lcom/delivery/rider/data/local/SharedPrefManager;)V", "getLocalRider", "Lcom/delivery/rider/data/models/Rider;", "getRiderReviews", "Lkotlin/Result;", "", "Lcom/delivery/rider/data/models/Review;", "getRiderReviews-IoAF18A", "(Lkotlin/coroutines/Continuation;)Ljava/lang/Object;", "logout", "", "updateProfile", "name", "", "email", "updateProfile-0E7RQCE", "(Ljava/lang/String;Ljava/lang/String;Lkotlin/coroutines/Continuation;)Ljava/lang/Object;", "updateStatus", "status", "updateStatus-gIAlu-s", "(Ljava/lang/String;Lkotlin/coroutines/Continuation;)Ljava/lang/Object;", "DeliveryRiderApp_debug"})
public final class RiderRepository {
    @org.jetbrains.annotations.NotNull()
    private final com.delivery.rider.data.api.ApiService apiService = null;
    @org.jetbrains.annotations.NotNull()
    private final com.delivery.rider.data.local.SharedPrefManager sharedPrefManager = null;
    
    @javax.inject.Inject()
    public RiderRepository(@org.jetbrains.annotations.NotNull()
    com.delivery.rider.data.api.ApiService apiService, @org.jetbrains.annotations.NotNull()
    com.delivery.rider.data.local.SharedPrefManager sharedPrefManager) {
        super();
    }
    
    @org.jetbrains.annotations.Nullable()
    public final com.delivery.rider.data.models.Rider getLocalRider() {
        return null;
    }
    
    public final void logout() {
    }
}