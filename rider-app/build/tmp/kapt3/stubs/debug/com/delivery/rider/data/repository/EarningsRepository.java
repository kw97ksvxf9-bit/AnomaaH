package com.delivery.rider.data.repository;

@kotlin.Metadata(mv = {1, 9, 0}, k = 1, xi = 48, d1 = {"\u0000>\n\u0002\u0018\u0002\n\u0002\u0010\u0000\n\u0000\n\u0002\u0018\u0002\n\u0000\n\u0002\u0018\u0002\n\u0002\b\u0002\n\u0002\u0018\u0002\n\u0002\u0018\u0002\n\u0000\n\u0002\u0010\u000e\n\u0002\b\u0003\n\u0002\u0010 \n\u0002\u0018\u0002\n\u0002\b\u0004\n\u0002\u0010\u0007\n\u0002\b\u0003\u0018\u00002\u00020\u0001B\u0017\b\u0007\u0012\u0006\u0010\u0002\u001a\u00020\u0003\u0012\u0006\u0010\u0004\u001a\u00020\u0005\u00a2\u0006\u0002\u0010\u0006J&\u0010\u0007\u001a\b\u0012\u0004\u0012\u00020\t0\b2\b\b\u0002\u0010\n\u001a\u00020\u000bH\u0086@\u00f8\u0001\u0000\u00f8\u0001\u0001\u00a2\u0006\u0004\b\f\u0010\rJ\"\u0010\u000e\u001a\u000e\u0012\n\u0012\b\u0012\u0004\u0012\u00020\u00100\u000f0\bH\u0086@\u00f8\u0001\u0000\u00f8\u0001\u0001\u00a2\u0006\u0004\b\u0011\u0010\u0012J$\u0010\u0013\u001a\b\u0012\u0004\u0012\u00020\u00100\b2\u0006\u0010\u0014\u001a\u00020\u0015H\u0086@\u00f8\u0001\u0000\u00f8\u0001\u0001\u00a2\u0006\u0004\b\u0016\u0010\u0017R\u000e\u0010\u0002\u001a\u00020\u0003X\u0082\u0004\u00a2\u0006\u0002\n\u0000R\u000e\u0010\u0004\u001a\u00020\u0005X\u0082\u0004\u00a2\u0006\u0002\n\u0000\u0082\u0002\u000b\n\u0002\b!\n\u0005\b\u00a1\u001e0\u0001\u00a8\u0006\u0018"}, d2 = {"Lcom/delivery/rider/data/repository/EarningsRepository;", "", "apiService", "Lcom/delivery/rider/data/api/ApiService;", "sharedPrefManager", "Lcom/delivery/rider/data/local/SharedPrefManager;", "(Lcom/delivery/rider/data/api/ApiService;Lcom/delivery/rider/data/local/SharedPrefManager;)V", "getEarnings", "Lkotlin/Result;", "Lcom/delivery/rider/data/models/EarningsResponse;", "period", "", "getEarnings-gIAlu-s", "(Ljava/lang/String;Lkotlin/coroutines/Continuation;)Ljava/lang/Object;", "getPayoutHistory", "", "Lcom/delivery/rider/data/models/Payout;", "getPayoutHistory-IoAF18A", "(Lkotlin/coroutines/Continuation;)Ljava/lang/Object;", "requestPayout", "amount", "", "requestPayout-gIAlu-s", "(FLkotlin/coroutines/Continuation;)Ljava/lang/Object;", "DeliveryRiderApp_debug"})
public final class EarningsRepository {
    @org.jetbrains.annotations.NotNull()
    private final com.delivery.rider.data.api.ApiService apiService = null;
    @org.jetbrains.annotations.NotNull()
    private final com.delivery.rider.data.local.SharedPrefManager sharedPrefManager = null;
    
    @javax.inject.Inject()
    public EarningsRepository(@org.jetbrains.annotations.NotNull()
    com.delivery.rider.data.api.ApiService apiService, @org.jetbrains.annotations.NotNull()
    com.delivery.rider.data.local.SharedPrefManager sharedPrefManager) {
        super();
    }
}