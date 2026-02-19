package com.delivery.rider.ui.profile;

@dagger.hilt.android.AndroidEntryPoint()
@kotlin.Metadata(mv = {1, 9, 0}, k = 1, xi = 48, d1 = {"\u0000^\n\u0002\u0018\u0002\n\u0002\u0018\u0002\n\u0002\b\u0002\n\u0002\u0018\u0002\n\u0002\b\u0005\n\u0002\u0018\u0002\n\u0000\n\u0002\u0018\u0002\n\u0000\n\u0002\u0010\u000b\n\u0000\n\u0002\u0018\u0002\n\u0002\b\u0004\n\u0002\u0018\u0002\n\u0000\n\u0002\u0018\u0002\n\u0002\b\t\n\u0002\u0010\u0002\n\u0000\n\u0002\u0018\u0002\n\u0002\b\u0003\n\u0002\u0018\u0002\n\u0000\n\u0002\u0018\u0002\n\u0000\n\u0002\u0018\u0002\n\u0002\b\u0005\b\u0007\u0018\u00002\u00020\u0001B\u0005\u00a2\u0006\u0002\u0010\u0002J\u0010\u0010 \u001a\u00020!2\u0006\u0010\"\u001a\u00020#H\u0002J\b\u0010$\u001a\u00020!H\u0002J$\u0010%\u001a\u00020#2\u0006\u0010&\u001a\u00020\'2\b\u0010(\u001a\u0004\u0018\u00010)2\b\u0010*\u001a\u0004\u0018\u00010+H\u0016J\u001a\u0010,\u001a\u00020!2\u0006\u0010\"\u001a\u00020#2\b\u0010*\u001a\u0004\u0018\u00010+H\u0016J\b\u0010-\u001a\u00020!H\u0002J\b\u0010.\u001a\u00020!H\u0002J\b\u0010/\u001a\u00020!H\u0002R\u001b\u0010\u0003\u001a\u00020\u00048BX\u0082\u0084\u0002\u00a2\u0006\f\n\u0004\b\u0007\u0010\b\u001a\u0004\b\u0005\u0010\u0006R\u000e\u0010\t\u001a\u00020\nX\u0082.\u00a2\u0006\u0002\n\u0000R\u000e\u0010\u000b\u001a\u00020\fX\u0082.\u00a2\u0006\u0002\n\u0000R\u000e\u0010\r\u001a\u00020\u000eX\u0082\u000e\u00a2\u0006\u0002\n\u0000R\u001b\u0010\u000f\u001a\u00020\u00108BX\u0082\u0084\u0002\u00a2\u0006\f\n\u0004\b\u0013\u0010\b\u001a\u0004\b\u0011\u0010\u0012R\u000e\u0010\u0014\u001a\u00020\u0015X\u0082.\u00a2\u0006\u0002\n\u0000R\u000e\u0010\u0016\u001a\u00020\u0017X\u0082.\u00a2\u0006\u0002\n\u0000R\u000e\u0010\u0018\u001a\u00020\u0017X\u0082.\u00a2\u0006\u0002\n\u0000R\u000e\u0010\u0019\u001a\u00020\u0017X\u0082.\u00a2\u0006\u0002\n\u0000R\u000e\u0010\u001a\u001a\u00020\u0017X\u0082.\u00a2\u0006\u0002\n\u0000R\u000e\u0010\u001b\u001a\u00020\u0017X\u0082.\u00a2\u0006\u0002\n\u0000R\u000e\u0010\u001c\u001a\u00020\u0017X\u0082.\u00a2\u0006\u0002\n\u0000R\u000e\u0010\u001d\u001a\u00020\u0017X\u0082.\u00a2\u0006\u0002\n\u0000R\u000e\u0010\u001e\u001a\u00020\u0017X\u0082.\u00a2\u0006\u0002\n\u0000R\u000e\u0010\u001f\u001a\u00020\u0017X\u0082.\u00a2\u0006\u0002\n\u0000\u00a8\u00060"}, d2 = {"Lcom/delivery/rider/ui/profile/ProfileFragment;", "Landroidx/fragment/app/Fragment;", "()V", "authViewModel", "Lcom/delivery/rider/ui/viewmodel/AuthViewModel;", "getAuthViewModel", "()Lcom/delivery/rider/ui/viewmodel/AuthViewModel;", "authViewModel$delegate", "Lkotlin/Lazy;", "btnLogout", "Lcom/google/android/material/button/MaterialButton;", "cardChangePasscode", "Lcom/google/android/material/card/MaterialCardView;", "isOnline", "", "riderViewModel", "Lcom/delivery/rider/ui/viewmodel/RiderViewModel;", "getRiderViewModel", "()Lcom/delivery/rider/ui/viewmodel/RiderViewModel;", "riderViewModel$delegate", "toggleOnlineProfile", "Landroid/widget/LinearLayout;", "tvAvatar", "Landroid/widget/TextView;", "tvBike", "tvCompanyName", "tvDeliveries", "tvEarnings", "tvOnlineProfile", "tvPhone", "tvRating", "tvRiderName", "initViews", "", "view", "Landroid/view/View;", "observeViewModel", "onCreateView", "inflater", "Landroid/view/LayoutInflater;", "container", "Landroid/view/ViewGroup;", "savedInstanceState", "Landroid/os/Bundle;", "onViewCreated", "showChangePasscodeDialog", "showLogoutDialog", "updateOnlineUI", "DeliveryRiderApp_debug"})
public final class ProfileFragment extends androidx.fragment.app.Fragment {
    @org.jetbrains.annotations.NotNull()
    private final kotlin.Lazy riderViewModel$delegate = null;
    @org.jetbrains.annotations.NotNull()
    private final kotlin.Lazy authViewModel$delegate = null;
    private android.widget.TextView tvAvatar;
    private android.widget.TextView tvRiderName;
    private android.widget.TextView tvCompanyName;
    private android.widget.TextView tvOnlineProfile;
    private android.widget.LinearLayout toggleOnlineProfile;
    private android.widget.TextView tvRating;
    private android.widget.TextView tvDeliveries;
    private android.widget.TextView tvEarnings;
    private android.widget.TextView tvPhone;
    private android.widget.TextView tvBike;
    private com.google.android.material.card.MaterialCardView cardChangePasscode;
    private com.google.android.material.button.MaterialButton btnLogout;
    private boolean isOnline = false;
    
    public ProfileFragment() {
        super();
    }
    
    private final com.delivery.rider.ui.viewmodel.RiderViewModel getRiderViewModel() {
        return null;
    }
    
    private final com.delivery.rider.ui.viewmodel.AuthViewModel getAuthViewModel() {
        return null;
    }
    
    @java.lang.Override()
    @org.jetbrains.annotations.NotNull()
    public android.view.View onCreateView(@org.jetbrains.annotations.NotNull()
    android.view.LayoutInflater inflater, @org.jetbrains.annotations.Nullable()
    android.view.ViewGroup container, @org.jetbrains.annotations.Nullable()
    android.os.Bundle savedInstanceState) {
        return null;
    }
    
    @java.lang.Override()
    public void onViewCreated(@org.jetbrains.annotations.NotNull()
    android.view.View view, @org.jetbrains.annotations.Nullable()
    android.os.Bundle savedInstanceState) {
    }
    
    private final void initViews(android.view.View view) {
    }
    
    private final void observeViewModel() {
    }
    
    private final void updateOnlineUI() {
    }
    
    private final void showChangePasscodeDialog() {
    }
    
    private final void showLogoutDialog() {
    }
}