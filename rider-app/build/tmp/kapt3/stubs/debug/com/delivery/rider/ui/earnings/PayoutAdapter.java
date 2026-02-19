package com.delivery.rider.ui.earnings;

@kotlin.Metadata(mv = {1, 9, 0}, k = 1, xi = 48, d1 = {"\u0000>\n\u0002\u0018\u0002\n\u0002\u0018\u0002\n\u0002\u0018\u0002\n\u0000\n\u0002\u0010!\n\u0002\u0018\u0002\n\u0002\b\u0002\n\u0002\u0018\u0002\n\u0000\n\u0002\u0010\b\n\u0000\n\u0002\u0010\u0002\n\u0002\b\u0004\n\u0002\u0018\u0002\n\u0002\b\u0003\n\u0002\u0010 \n\u0002\b\u0002\u0018\u00002\f\u0012\b\u0012\u00060\u0002R\u00020\u00000\u0001:\u0001\u0016B\u0015\u0012\u000e\b\u0002\u0010\u0003\u001a\b\u0012\u0004\u0012\u00020\u00050\u0004\u00a2\u0006\u0002\u0010\u0006J\b\u0010\t\u001a\u00020\nH\u0016J\u001c\u0010\u000b\u001a\u00020\f2\n\u0010\r\u001a\u00060\u0002R\u00020\u00002\u0006\u0010\u000e\u001a\u00020\nH\u0016J\u001c\u0010\u000f\u001a\u00060\u0002R\u00020\u00002\u0006\u0010\u0010\u001a\u00020\u00112\u0006\u0010\u0012\u001a\u00020\nH\u0016J\u0014\u0010\u0013\u001a\u00020\f2\f\u0010\u0014\u001a\b\u0012\u0004\u0012\u00020\u00050\u0015R\u000e\u0010\u0007\u001a\u00020\bX\u0082\u0004\u00a2\u0006\u0002\n\u0000R\u0014\u0010\u0003\u001a\b\u0012\u0004\u0012\u00020\u00050\u0004X\u0082\u0004\u00a2\u0006\u0002\n\u0000\u00a8\u0006\u0017"}, d2 = {"Lcom/delivery/rider/ui/earnings/PayoutAdapter;", "Landroidx/recyclerview/widget/RecyclerView$Adapter;", "Lcom/delivery/rider/ui/earnings/PayoutAdapter$PayoutViewHolder;", "payouts", "", "Lcom/delivery/rider/data/models/Payout;", "(Ljava/util/List;)V", "dateFormat", "Ljava/text/SimpleDateFormat;", "getItemCount", "", "onBindViewHolder", "", "holder", "position", "onCreateViewHolder", "parent", "Landroid/view/ViewGroup;", "viewType", "updatePayouts", "newPayouts", "", "PayoutViewHolder", "DeliveryRiderApp_debug"})
public final class PayoutAdapter extends androidx.recyclerview.widget.RecyclerView.Adapter<com.delivery.rider.ui.earnings.PayoutAdapter.PayoutViewHolder> {
    @org.jetbrains.annotations.NotNull()
    private final java.util.List<com.delivery.rider.data.models.Payout> payouts = null;
    @org.jetbrains.annotations.NotNull()
    private final java.text.SimpleDateFormat dateFormat = null;
    
    public PayoutAdapter(@org.jetbrains.annotations.NotNull()
    java.util.List<com.delivery.rider.data.models.Payout> payouts) {
        super();
    }
    
    @java.lang.Override()
    @org.jetbrains.annotations.NotNull()
    public com.delivery.rider.ui.earnings.PayoutAdapter.PayoutViewHolder onCreateViewHolder(@org.jetbrains.annotations.NotNull()
    android.view.ViewGroup parent, int viewType) {
        return null;
    }
    
    @java.lang.Override()
    public void onBindViewHolder(@org.jetbrains.annotations.NotNull()
    com.delivery.rider.ui.earnings.PayoutAdapter.PayoutViewHolder holder, int position) {
    }
    
    @java.lang.Override()
    public int getItemCount() {
        return 0;
    }
    
    public final void updatePayouts(@org.jetbrains.annotations.NotNull()
    java.util.List<com.delivery.rider.data.models.Payout> newPayouts) {
    }
    
    public PayoutAdapter() {
        super();
    }
    
    @kotlin.Metadata(mv = {1, 9, 0}, k = 1, xi = 48, d1 = {"\u0000&\n\u0002\u0018\u0002\n\u0002\u0018\u0002\n\u0000\n\u0002\u0018\u0002\n\u0002\b\u0002\n\u0002\u0018\u0002\n\u0002\b\u0004\n\u0002\u0010\u0002\n\u0000\n\u0002\u0018\u0002\n\u0000\b\u0086\u0004\u0018\u00002\u00020\u0001B\r\u0012\u0006\u0010\u0002\u001a\u00020\u0003\u00a2\u0006\u0002\u0010\u0004J\u000e\u0010\n\u001a\u00020\u000b2\u0006\u0010\f\u001a\u00020\rR\u000e\u0010\u0005\u001a\u00020\u0006X\u0082\u0004\u00a2\u0006\u0002\n\u0000R\u000e\u0010\u0007\u001a\u00020\u0006X\u0082\u0004\u00a2\u0006\u0002\n\u0000R\u000e\u0010\b\u001a\u00020\u0006X\u0082\u0004\u00a2\u0006\u0002\n\u0000R\u000e\u0010\t\u001a\u00020\u0006X\u0082\u0004\u00a2\u0006\u0002\n\u0000\u00a8\u0006\u000e"}, d2 = {"Lcom/delivery/rider/ui/earnings/PayoutAdapter$PayoutViewHolder;", "Landroidx/recyclerview/widget/RecyclerView$ViewHolder;", "itemView", "Landroid/view/View;", "(Lcom/delivery/rider/ui/earnings/PayoutAdapter;Landroid/view/View;)V", "tvIcon", "Landroid/widget/TextView;", "tvPayoutAmount", "tvPayoutDate", "tvPayoutStatus", "bind", "", "payout", "Lcom/delivery/rider/data/models/Payout;", "DeliveryRiderApp_debug"})
    public final class PayoutViewHolder extends androidx.recyclerview.widget.RecyclerView.ViewHolder {
        @org.jetbrains.annotations.NotNull()
        private final android.widget.TextView tvPayoutAmount = null;
        @org.jetbrains.annotations.NotNull()
        private final android.widget.TextView tvPayoutDate = null;
        @org.jetbrains.annotations.NotNull()
        private final android.widget.TextView tvPayoutStatus = null;
        @org.jetbrains.annotations.NotNull()
        private final android.widget.TextView tvIcon = null;
        
        public PayoutViewHolder(@org.jetbrains.annotations.NotNull()
        android.view.View itemView) {
            super(null);
        }
        
        public final void bind(@org.jetbrains.annotations.NotNull()
        com.delivery.rider.data.models.Payout payout) {
        }
    }
}