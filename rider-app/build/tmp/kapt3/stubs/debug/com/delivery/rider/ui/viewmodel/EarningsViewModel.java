package com.delivery.rider.ui.viewmodel;

@kotlin.Metadata(mv = {1, 9, 0}, k = 1, xi = 48, d1 = {"\u0000J\n\u0002\u0018\u0002\n\u0002\u0018\u0002\n\u0000\n\u0002\u0018\u0002\n\u0002\b\u0002\n\u0002\u0018\u0002\n\u0002\u0018\u0002\n\u0000\n\u0002\u0018\u0002\n\u0000\n\u0002\u0010 \n\u0002\u0018\u0002\n\u0000\n\u0002\u0010\u000e\n\u0002\b\u0002\n\u0002\u0018\u0002\n\u0002\b\u0007\n\u0002\u0010\u0002\n\u0002\b\u0004\n\u0002\u0010\u0007\n\u0000\b\u0007\u0018\u00002\u00020\u0001B\u000f\b\u0007\u0012\u0006\u0010\u0002\u001a\u00020\u0003\u00a2\u0006\u0002\u0010\u0004J\u0010\u0010\u0018\u001a\u00020\u00192\b\b\u0002\u0010\u001a\u001a\u00020\u000eJ\u0006\u0010\u001b\u001a\u00020\u0019J\u000e\u0010\u001c\u001a\u00020\u00192\u0006\u0010\u001d\u001a\u00020\u001eR\u0016\u0010\u0005\u001a\n\u0012\u0006\u0012\u0004\u0018\u00010\u00070\u0006X\u0082\u0004\u00a2\u0006\u0002\n\u0000R\u0014\u0010\b\u001a\b\u0012\u0004\u0012\u00020\t0\u0006X\u0082\u0004\u00a2\u0006\u0002\n\u0000R\u001a\u0010\n\u001a\u000e\u0012\n\u0012\b\u0012\u0004\u0012\u00020\f0\u000b0\u0006X\u0082\u0004\u00a2\u0006\u0002\n\u0000R\u001c\u0010\r\u001a\u0010\u0012\f\u0012\n \u000f*\u0004\u0018\u00010\u000e0\u000e0\u0006X\u0082\u0004\u00a2\u0006\u0002\n\u0000R\u0019\u0010\u0010\u001a\n\u0012\u0006\u0012\u0004\u0018\u00010\u00070\u0011\u00a2\u0006\b\n\u0000\u001a\u0004\b\u0012\u0010\u0013R\u000e\u0010\u0002\u001a\u00020\u0003X\u0082\u0004\u00a2\u0006\u0002\n\u0000R\u0017\u0010\u0014\u001a\b\u0012\u0004\u0012\u00020\t0\u0011\u00a2\u0006\b\n\u0000\u001a\u0004\b\u0015\u0010\u0013R\u001d\u0010\u0016\u001a\u000e\u0012\n\u0012\b\u0012\u0004\u0012\u00020\f0\u000b0\u0011\u00a2\u0006\b\n\u0000\u001a\u0004\b\u0017\u0010\u0013\u00a8\u0006\u001f"}, d2 = {"Lcom/delivery/rider/ui/viewmodel/EarningsViewModel;", "Landroidx/lifecycle/ViewModel;", "earningsRepository", "Lcom/delivery/rider/data/repository/EarningsRepository;", "(Lcom/delivery/rider/data/repository/EarningsRepository;)V", "_earnings", "Landroidx/lifecycle/MutableLiveData;", "Lcom/delivery/rider/data/models/EarningsResponse;", "_earningsState", "Lcom/delivery/rider/ui/viewmodel/EarningsState;", "_payouts", "", "Lcom/delivery/rider/data/models/Payout;", "_period", "", "kotlin.jvm.PlatformType", "earnings", "Landroidx/lifecycle/LiveData;", "getEarnings", "()Landroidx/lifecycle/LiveData;", "earningsState", "getEarningsState", "payouts", "getPayouts", "loadEarnings", "", "period", "loadPayoutHistory", "requestPayout", "amount", "", "DeliveryRiderApp_debug"})
@dagger.hilt.android.lifecycle.HiltViewModel()
public final class EarningsViewModel extends androidx.lifecycle.ViewModel {
    @org.jetbrains.annotations.NotNull()
    private final com.delivery.rider.data.repository.EarningsRepository earningsRepository = null;
    @org.jetbrains.annotations.NotNull()
    private final androidx.lifecycle.MutableLiveData<com.delivery.rider.data.models.EarningsResponse> _earnings = null;
    @org.jetbrains.annotations.NotNull()
    private final androidx.lifecycle.LiveData<com.delivery.rider.data.models.EarningsResponse> earnings = null;
    @org.jetbrains.annotations.NotNull()
    private final androidx.lifecycle.MutableLiveData<java.util.List<com.delivery.rider.data.models.Payout>> _payouts = null;
    @org.jetbrains.annotations.NotNull()
    private final androidx.lifecycle.LiveData<java.util.List<com.delivery.rider.data.models.Payout>> payouts = null;
    @org.jetbrains.annotations.NotNull()
    private final androidx.lifecycle.MutableLiveData<com.delivery.rider.ui.viewmodel.EarningsState> _earningsState = null;
    @org.jetbrains.annotations.NotNull()
    private final androidx.lifecycle.LiveData<com.delivery.rider.ui.viewmodel.EarningsState> earningsState = null;
    @org.jetbrains.annotations.NotNull()
    private final androidx.lifecycle.MutableLiveData<java.lang.String> _period = null;
    
    @javax.inject.Inject()
    public EarningsViewModel(@org.jetbrains.annotations.NotNull()
    com.delivery.rider.data.repository.EarningsRepository earningsRepository) {
        super();
    }
    
    @org.jetbrains.annotations.NotNull()
    public final androidx.lifecycle.LiveData<com.delivery.rider.data.models.EarningsResponse> getEarnings() {
        return null;
    }
    
    @org.jetbrains.annotations.NotNull()
    public final androidx.lifecycle.LiveData<java.util.List<com.delivery.rider.data.models.Payout>> getPayouts() {
        return null;
    }
    
    @org.jetbrains.annotations.NotNull()
    public final androidx.lifecycle.LiveData<com.delivery.rider.ui.viewmodel.EarningsState> getEarningsState() {
        return null;
    }
    
    public final void loadEarnings(@org.jetbrains.annotations.NotNull()
    java.lang.String period) {
    }
    
    public final void loadPayoutHistory() {
    }
    
    public final void requestPayout(float amount) {
    }
}