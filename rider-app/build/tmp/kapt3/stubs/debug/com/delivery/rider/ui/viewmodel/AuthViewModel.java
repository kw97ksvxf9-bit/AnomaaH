package com.delivery.rider.ui.viewmodel;

@kotlin.Metadata(mv = {1, 9, 0}, k = 1, xi = 48, d1 = {"\u0000F\n\u0002\u0018\u0002\n\u0002\u0018\u0002\n\u0000\n\u0002\u0018\u0002\n\u0002\b\u0002\n\u0002\u0018\u0002\n\u0002\u0018\u0002\n\u0000\n\u0002\u0018\u0002\n\u0000\n\u0002\u0018\u0002\n\u0000\n\u0002\u0018\u0002\n\u0002\b\u0007\n\u0002\u0010\u0002\n\u0000\n\u0002\u0010\u000e\n\u0002\b\u0002\n\u0002\u0010\u000b\n\u0002\b\u0007\b\u0007\u0018\u00002\u00020\u0001B\u000f\b\u0007\u0012\u0006\u0010\u0002\u001a\u00020\u0003\u00a2\u0006\u0002\u0010\u0004J\u000e\u0010\u0014\u001a\u00020\u00152\u0006\u0010\u0016\u001a\u00020\u0017J\u0006\u0010\u0018\u001a\u00020\u0015J\u0006\u0010\u0019\u001a\u00020\u001aJ\u0006\u0010\u001b\u001a\u00020\u0015J\u0016\u0010\u001c\u001a\u00020\u00152\u0006\u0010\u001d\u001a\u00020\u00172\u0006\u0010\u001e\u001a\u00020\u0017J\u0006\u0010\u001f\u001a\u00020\u0015J\u0006\u0010 \u001a\u00020\u0015R\u0014\u0010\u0005\u001a\b\u0012\u0004\u0012\u00020\u00070\u0006X\u0082\u0004\u00a2\u0006\u0002\n\u0000R\u0016\u0010\b\u001a\n\u0012\u0006\u0012\u0004\u0018\u00010\t0\u0006X\u0082\u0004\u00a2\u0006\u0002\n\u0000R\u0014\u0010\n\u001a\b\u0012\u0004\u0012\u00020\u000b0\u0006X\u0082\u0004\u00a2\u0006\u0002\n\u0000R\u000e\u0010\u0002\u001a\u00020\u0003X\u0082\u0004\u00a2\u0006\u0002\n\u0000R\u0017\u0010\f\u001a\b\u0012\u0004\u0012\u00020\u00070\r\u00a2\u0006\b\n\u0000\u001a\u0004\b\u000e\u0010\u000fR\u0019\u0010\u0010\u001a\n\u0012\u0006\u0012\u0004\u0018\u00010\t0\r\u00a2\u0006\b\n\u0000\u001a\u0004\b\u0011\u0010\u000fR\u0017\u0010\u0012\u001a\b\u0012\u0004\u0012\u00020\u000b0\r\u00a2\u0006\b\n\u0000\u001a\u0004\b\u0013\u0010\u000f\u00a8\u0006!"}, d2 = {"Lcom/delivery/rider/ui/viewmodel/AuthViewModel;", "Landroidx/lifecycle/ViewModel;", "authRepository", "Lcom/delivery/rider/data/repository/AuthRepository;", "(Lcom/delivery/rider/data/repository/AuthRepository;)V", "_changePasscodeState", "Landroidx/lifecycle/MutableLiveData;", "Lcom/delivery/rider/ui/viewmodel/ChangePasscodeState;", "_currentRider", "Lcom/delivery/rider/data/models/Rider;", "_loginState", "Lcom/delivery/rider/ui/viewmodel/LoginState;", "changePasscodeState", "Landroidx/lifecycle/LiveData;", "getChangePasscodeState", "()Landroidx/lifecycle/LiveData;", "currentRider", "getCurrentRider", "loginState", "getLoginState", "changePasscode", "", "newPasscode", "", "checkLoginStatus", "isLoggedIn", "", "logout", "passcodeLogin", "phone", "passcode", "refreshRider", "resetChangePasscodeState", "DeliveryRiderApp_debug"})
@dagger.hilt.android.lifecycle.HiltViewModel()
public final class AuthViewModel extends androidx.lifecycle.ViewModel {
    @org.jetbrains.annotations.NotNull()
    private final com.delivery.rider.data.repository.AuthRepository authRepository = null;
    @org.jetbrains.annotations.NotNull()
    private final androidx.lifecycle.MutableLiveData<com.delivery.rider.ui.viewmodel.LoginState> _loginState = null;
    @org.jetbrains.annotations.NotNull()
    private final androidx.lifecycle.LiveData<com.delivery.rider.ui.viewmodel.LoginState> loginState = null;
    @org.jetbrains.annotations.NotNull()
    private final androidx.lifecycle.MutableLiveData<com.delivery.rider.data.models.Rider> _currentRider = null;
    @org.jetbrains.annotations.NotNull()
    private final androidx.lifecycle.LiveData<com.delivery.rider.data.models.Rider> currentRider = null;
    @org.jetbrains.annotations.NotNull()
    private final androidx.lifecycle.MutableLiveData<com.delivery.rider.ui.viewmodel.ChangePasscodeState> _changePasscodeState = null;
    @org.jetbrains.annotations.NotNull()
    private final androidx.lifecycle.LiveData<com.delivery.rider.ui.viewmodel.ChangePasscodeState> changePasscodeState = null;
    
    @javax.inject.Inject()
    public AuthViewModel(@org.jetbrains.annotations.NotNull()
    com.delivery.rider.data.repository.AuthRepository authRepository) {
        super();
    }
    
    @org.jetbrains.annotations.NotNull()
    public final androidx.lifecycle.LiveData<com.delivery.rider.ui.viewmodel.LoginState> getLoginState() {
        return null;
    }
    
    @org.jetbrains.annotations.NotNull()
    public final androidx.lifecycle.LiveData<com.delivery.rider.data.models.Rider> getCurrentRider() {
        return null;
    }
    
    @org.jetbrains.annotations.NotNull()
    public final androidx.lifecycle.LiveData<com.delivery.rider.ui.viewmodel.ChangePasscodeState> getChangePasscodeState() {
        return null;
    }
    
    /**
     * Passcode login: phone + 5-digit code
     */
    public final void passcodeLogin(@org.jetbrains.annotations.NotNull()
    java.lang.String phone, @org.jetbrains.annotations.NotNull()
    java.lang.String passcode) {
    }
    
    /**
     * Change passcode
     */
    public final void changePasscode(@org.jetbrains.annotations.NotNull()
    java.lang.String newPasscode) {
    }
    
    public final void resetChangePasscodeState() {
    }
    
    public final void logout() {
    }
    
    public final void checkLoginStatus() {
    }
    
    public final boolean isLoggedIn() {
        return false;
    }
    
    public final void refreshRider() {
    }
}