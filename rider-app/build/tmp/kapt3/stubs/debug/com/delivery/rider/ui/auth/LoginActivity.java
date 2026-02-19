package com.delivery.rider.ui.auth;

@dagger.hilt.android.AndroidEntryPoint()
@kotlin.Metadata(mv = {1, 9, 0}, k = 1, xi = 48, d1 = {"\u0000F\n\u0002\u0018\u0002\n\u0002\u0018\u0002\n\u0002\b\u0002\n\u0002\u0018\u0002\n\u0000\n\u0002\u0018\u0002\n\u0002\b\u0002\n\u0002\u0018\u0002\n\u0000\n\u0002\u0018\u0002\n\u0000\n\u0002\u0018\u0002\n\u0002\b\u0005\n\u0002\u0010\u0002\n\u0002\b\u0003\n\u0002\u0018\u0002\n\u0002\b\u0002\n\u0002\u0010\u000e\n\u0002\b\u0002\b\u0007\u0018\u00002\u00020\u0001B\u0005\u00a2\u0006\u0002\u0010\u0002J\b\u0010\u0012\u001a\u00020\u0013H\u0002J\b\u0010\u0014\u001a\u00020\u0013H\u0002J\u0012\u0010\u0015\u001a\u00020\u00132\b\u0010\u0016\u001a\u0004\u0018\u00010\u0017H\u0014J\u0010\u0010\u0018\u001a\u00020\u00132\u0006\u0010\u0019\u001a\u00020\u001aH\u0002J\b\u0010\u001b\u001a\u00020\u0013H\u0002R\u000e\u0010\u0003\u001a\u00020\u0004X\u0082.\u00a2\u0006\u0002\n\u0000R\u000e\u0010\u0005\u001a\u00020\u0006X\u0082.\u00a2\u0006\u0002\n\u0000R\u000e\u0010\u0007\u001a\u00020\u0006X\u0082.\u00a2\u0006\u0002\n\u0000R\u000e\u0010\b\u001a\u00020\tX\u0082.\u00a2\u0006\u0002\n\u0000R\u000e\u0010\n\u001a\u00020\u000bX\u0082.\u00a2\u0006\u0002\n\u0000R\u001b\u0010\f\u001a\u00020\r8BX\u0082\u0084\u0002\u00a2\u0006\f\n\u0004\b\u0010\u0010\u0011\u001a\u0004\b\u000e\u0010\u000f\u00a8\u0006\u001c"}, d2 = {"Lcom/delivery/rider/ui/auth/LoginActivity;", "Landroidx/appcompat/app/AppCompatActivity;", "()V", "btnLogin", "Lcom/google/android/material/button/MaterialButton;", "etPasscode", "Landroid/widget/EditText;", "etPhone", "loginProgress", "Landroid/widget/ProgressBar;", "tvError", "Landroid/widget/TextView;", "viewModel", "Lcom/delivery/rider/ui/viewmodel/AuthViewModel;", "getViewModel", "()Lcom/delivery/rider/ui/viewmodel/AuthViewModel;", "viewModel$delegate", "Lkotlin/Lazy;", "initViews", "", "observeViewModel", "onCreate", "savedInstanceState", "Landroid/os/Bundle;", "showError", "msg", "", "startMain", "DeliveryRiderApp_debug"})
public final class LoginActivity extends androidx.appcompat.app.AppCompatActivity {
    @org.jetbrains.annotations.NotNull()
    private final kotlin.Lazy viewModel$delegate = null;
    private android.widget.EditText etPhone;
    private android.widget.EditText etPasscode;
    private com.google.android.material.button.MaterialButton btnLogin;
    private android.widget.ProgressBar loginProgress;
    private android.widget.TextView tvError;
    
    public LoginActivity() {
        super();
    }
    
    private final com.delivery.rider.ui.viewmodel.AuthViewModel getViewModel() {
        return null;
    }
    
    @java.lang.Override()
    protected void onCreate(@org.jetbrains.annotations.Nullable()
    android.os.Bundle savedInstanceState) {
    }
    
    private final void initViews() {
    }
    
    private final void observeViewModel() {
    }
    
    private final void showError(java.lang.String msg) {
    }
    
    private final void startMain() {
    }
}