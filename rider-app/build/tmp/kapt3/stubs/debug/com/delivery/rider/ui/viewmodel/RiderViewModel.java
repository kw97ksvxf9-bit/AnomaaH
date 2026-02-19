package com.delivery.rider.ui.viewmodel;

@kotlin.Metadata(mv = {1, 9, 0}, k = 1, xi = 48, d1 = {"\u0000L\n\u0002\u0018\u0002\n\u0002\u0018\u0002\n\u0000\n\u0002\u0018\u0002\n\u0002\b\u0002\n\u0002\u0018\u0002\n\u0002\u0010\u000b\n\u0002\b\u0002\n\u0002\u0010 \n\u0002\u0018\u0002\n\u0000\n\u0002\u0018\u0002\n\u0000\n\u0002\u0018\u0002\n\u0000\n\u0002\u0018\u0002\n\u0002\b\b\n\u0002\u0010\u0002\n\u0002\b\u0004\n\u0002\u0010\u000e\n\u0002\b\u0004\b\u0007\u0018\u00002\u00020\u0001B\u000f\b\u0007\u0012\u0006\u0010\u0002\u001a\u00020\u0003\u00a2\u0006\u0002\u0010\u0004J\u0006\u0010\u0019\u001a\u00020\u001aJ\u0006\u0010\u001b\u001a\u00020\u001aJ\u0006\u0010\u001c\u001a\u00020\u001aJ\u001a\u0010\u001d\u001a\u00020\u001a2\b\u0010\u001e\u001a\u0004\u0018\u00010\u001f2\b\u0010 \u001a\u0004\u0018\u00010\u001fJ\u000e\u0010!\u001a\u00020\u001a2\u0006\u0010\"\u001a\u00020\u001fR\u001c\u0010\u0005\u001a\u0010\u0012\f\u0012\n \b*\u0004\u0018\u00010\u00070\u00070\u0006X\u0082\u0004\u00a2\u0006\u0002\n\u0000R\u001a\u0010\t\u001a\u000e\u0012\n\u0012\b\u0012\u0004\u0012\u00020\u000b0\n0\u0006X\u0082\u0004\u00a2\u0006\u0002\n\u0000R\u0016\u0010\f\u001a\n\u0012\u0006\u0012\u0004\u0018\u00010\r0\u0006X\u0082\u0004\u00a2\u0006\u0002\n\u0000R\u0014\u0010\u000e\u001a\b\u0012\u0004\u0012\u00020\u000f0\u0006X\u0082\u0004\u00a2\u0006\u0002\n\u0000R\u0017\u0010\u0010\u001a\b\u0012\u0004\u0012\u00020\u00070\u0011\u00a2\u0006\b\n\u0000\u001a\u0004\b\u0010\u0010\u0012R\u001d\u0010\u0013\u001a\u000e\u0012\n\u0012\b\u0012\u0004\u0012\u00020\u000b0\n0\u0011\u00a2\u0006\b\n\u0000\u001a\u0004\b\u0014\u0010\u0012R\u0019\u0010\u0015\u001a\n\u0012\u0006\u0012\u0004\u0018\u00010\r0\u0011\u00a2\u0006\b\n\u0000\u001a\u0004\b\u0016\u0010\u0012R\u000e\u0010\u0002\u001a\u00020\u0003X\u0082\u0004\u00a2\u0006\u0002\n\u0000R\u0017\u0010\u0017\u001a\b\u0012\u0004\u0012\u00020\u000f0\u0011\u00a2\u0006\b\n\u0000\u001a\u0004\b\u0018\u0010\u0012\u00a8\u0006#"}, d2 = {"Lcom/delivery/rider/ui/viewmodel/RiderViewModel;", "Landroidx/lifecycle/ViewModel;", "riderRepository", "Lcom/delivery/rider/data/repository/RiderRepository;", "(Lcom/delivery/rider/data/repository/RiderRepository;)V", "_isOnline", "Landroidx/lifecycle/MutableLiveData;", "", "kotlin.jvm.PlatformType", "_reviews", "", "Lcom/delivery/rider/data/models/Review;", "_riderProfile", "Lcom/delivery/rider/data/models/Rider;", "_riderState", "Lcom/delivery/rider/ui/viewmodel/RiderState;", "isOnline", "Landroidx/lifecycle/LiveData;", "()Landroidx/lifecycle/LiveData;", "reviews", "getReviews", "riderProfile", "getRiderProfile", "riderState", "getRiderState", "loadProfile", "", "loadReviews", "logout", "updateProfile", "name", "", "email", "updateStatus", "status", "DeliveryRiderApp_debug"})
@dagger.hilt.android.lifecycle.HiltViewModel()
public final class RiderViewModel extends androidx.lifecycle.ViewModel {
    @org.jetbrains.annotations.NotNull()
    private final com.delivery.rider.data.repository.RiderRepository riderRepository = null;
    @org.jetbrains.annotations.NotNull()
    private final androidx.lifecycle.MutableLiveData<com.delivery.rider.data.models.Rider> _riderProfile = null;
    @org.jetbrains.annotations.NotNull()
    private final androidx.lifecycle.LiveData<com.delivery.rider.data.models.Rider> riderProfile = null;
    @org.jetbrains.annotations.NotNull()
    private final androidx.lifecycle.MutableLiveData<java.lang.Boolean> _isOnline = null;
    @org.jetbrains.annotations.NotNull()
    private final androidx.lifecycle.LiveData<java.lang.Boolean> isOnline = null;
    @org.jetbrains.annotations.NotNull()
    private final androidx.lifecycle.MutableLiveData<java.util.List<com.delivery.rider.data.models.Review>> _reviews = null;
    @org.jetbrains.annotations.NotNull()
    private final androidx.lifecycle.LiveData<java.util.List<com.delivery.rider.data.models.Review>> reviews = null;
    @org.jetbrains.annotations.NotNull()
    private final androidx.lifecycle.MutableLiveData<com.delivery.rider.ui.viewmodel.RiderState> _riderState = null;
    @org.jetbrains.annotations.NotNull()
    private final androidx.lifecycle.LiveData<com.delivery.rider.ui.viewmodel.RiderState> riderState = null;
    
    @javax.inject.Inject()
    public RiderViewModel(@org.jetbrains.annotations.NotNull()
    com.delivery.rider.data.repository.RiderRepository riderRepository) {
        super();
    }
    
    @org.jetbrains.annotations.NotNull()
    public final androidx.lifecycle.LiveData<com.delivery.rider.data.models.Rider> getRiderProfile() {
        return null;
    }
    
    @org.jetbrains.annotations.NotNull()
    public final androidx.lifecycle.LiveData<java.lang.Boolean> isOnline() {
        return null;
    }
    
    @org.jetbrains.annotations.NotNull()
    public final androidx.lifecycle.LiveData<java.util.List<com.delivery.rider.data.models.Review>> getReviews() {
        return null;
    }
    
    @org.jetbrains.annotations.NotNull()
    public final androidx.lifecycle.LiveData<com.delivery.rider.ui.viewmodel.RiderState> getRiderState() {
        return null;
    }
    
    public final void loadProfile() {
    }
    
    public final void logout() {
    }
    
    public final void updateStatus(@org.jetbrains.annotations.NotNull()
    java.lang.String status) {
    }
    
    public final void loadReviews() {
    }
    
    public final void updateProfile(@org.jetbrains.annotations.Nullable()
    java.lang.String name, @org.jetbrains.annotations.Nullable()
    java.lang.String email) {
    }
}