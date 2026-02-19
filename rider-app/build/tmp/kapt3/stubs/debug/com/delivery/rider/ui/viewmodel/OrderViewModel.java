package com.delivery.rider.ui.viewmodel;

@kotlin.Metadata(mv = {1, 9, 0}, k = 1, xi = 48, d1 = {"\u0000>\n\u0002\u0018\u0002\n\u0002\u0018\u0002\n\u0000\n\u0002\u0018\u0002\n\u0002\b\u0002\n\u0002\u0018\u0002\n\u0002\u0010\u000e\n\u0000\n\u0002\u0018\u0002\n\u0000\n\u0002\u0010 \n\u0002\u0018\u0002\n\u0002\b\u0002\n\u0002\u0018\u0002\n\u0002\b\u0007\n\u0002\u0010\u0002\n\u0002\b\b\b\u0007\u0018\u00002\u00020\u0001B\u000f\b\u0007\u0012\u0006\u0010\u0002\u001a\u00020\u0003\u00a2\u0006\u0002\u0010\u0004J\u0016\u0010\u0016\u001a\u00020\u00172\u0006\u0010\u0018\u001a\u00020\u00072\u0006\u0010\u0019\u001a\u00020\u0007J\u000e\u0010\u001a\u001a\u00020\u00172\u0006\u0010\u0018\u001a\u00020\u0007J\u0012\u0010\u001b\u001a\u00020\u00172\n\b\u0002\u0010\u001c\u001a\u0004\u0018\u00010\u0007J\"\u0010\u001d\u001a\u00020\u00172\u0006\u0010\u0018\u001a\u00020\u00072\u0006\u0010\u001c\u001a\u00020\u00072\n\b\u0002\u0010\u001e\u001a\u0004\u0018\u00010\u0007R\u0016\u0010\u0005\u001a\n\u0012\u0006\u0012\u0004\u0018\u00010\u00070\u0006X\u0082\u0004\u00a2\u0006\u0002\n\u0000R\u0014\u0010\b\u001a\b\u0012\u0004\u0012\u00020\t0\u0006X\u0082\u0004\u00a2\u0006\u0002\n\u0000R\u001a\u0010\n\u001a\u000e\u0012\n\u0012\b\u0012\u0004\u0012\u00020\f0\u000b0\u0006X\u0082\u0004\u00a2\u0006\u0002\n\u0000R\u0016\u0010\r\u001a\n\u0012\u0006\u0012\u0004\u0018\u00010\f0\u0006X\u0082\u0004\u00a2\u0006\u0002\n\u0000R\u000e\u0010\u0002\u001a\u00020\u0003X\u0082\u0004\u00a2\u0006\u0002\n\u0000R\u0017\u0010\u000e\u001a\b\u0012\u0004\u0012\u00020\t0\u000f\u00a2\u0006\b\n\u0000\u001a\u0004\b\u0010\u0010\u0011R\u001d\u0010\u0012\u001a\u000e\u0012\n\u0012\b\u0012\u0004\u0012\u00020\f0\u000b0\u000f\u00a2\u0006\b\n\u0000\u001a\u0004\b\u0013\u0010\u0011R\u0019\u0010\u0014\u001a\n\u0012\u0006\u0012\u0004\u0018\u00010\f0\u000f\u00a2\u0006\b\n\u0000\u001a\u0004\b\u0015\u0010\u0011\u00a8\u0006\u001f"}, d2 = {"Lcom/delivery/rider/ui/viewmodel/OrderViewModel;", "Landroidx/lifecycle/ViewModel;", "orderRepository", "Lcom/delivery/rider/data/repository/OrderRepository;", "(Lcom/delivery/rider/data/repository/OrderRepository;)V", "_filterStatus", "Landroidx/lifecycle/MutableLiveData;", "", "_orderState", "Lcom/delivery/rider/ui/viewmodel/OrderState;", "_orders", "", "Lcom/delivery/rider/data/models/Order;", "_selectedOrder", "orderState", "Landroidx/lifecycle/LiveData;", "getOrderState", "()Landroidx/lifecycle/LiveData;", "orders", "getOrders", "selectedOrder", "getSelectedOrder", "cancelOrder", "", "orderId", "reason", "loadOrderDetails", "loadOrders", "status", "updateOrderStatus", "notes", "DeliveryRiderApp_debug"})
@dagger.hilt.android.lifecycle.HiltViewModel()
public final class OrderViewModel extends androidx.lifecycle.ViewModel {
    @org.jetbrains.annotations.NotNull()
    private final com.delivery.rider.data.repository.OrderRepository orderRepository = null;
    @org.jetbrains.annotations.NotNull()
    private final androidx.lifecycle.MutableLiveData<java.util.List<com.delivery.rider.data.models.Order>> _orders = null;
    @org.jetbrains.annotations.NotNull()
    private final androidx.lifecycle.LiveData<java.util.List<com.delivery.rider.data.models.Order>> orders = null;
    @org.jetbrains.annotations.NotNull()
    private final androidx.lifecycle.MutableLiveData<com.delivery.rider.data.models.Order> _selectedOrder = null;
    @org.jetbrains.annotations.NotNull()
    private final androidx.lifecycle.LiveData<com.delivery.rider.data.models.Order> selectedOrder = null;
    @org.jetbrains.annotations.NotNull()
    private final androidx.lifecycle.MutableLiveData<com.delivery.rider.ui.viewmodel.OrderState> _orderState = null;
    @org.jetbrains.annotations.NotNull()
    private final androidx.lifecycle.LiveData<com.delivery.rider.ui.viewmodel.OrderState> orderState = null;
    @org.jetbrains.annotations.NotNull()
    private final androidx.lifecycle.MutableLiveData<java.lang.String> _filterStatus = null;
    
    @javax.inject.Inject()
    public OrderViewModel(@org.jetbrains.annotations.NotNull()
    com.delivery.rider.data.repository.OrderRepository orderRepository) {
        super();
    }
    
    @org.jetbrains.annotations.NotNull()
    public final androidx.lifecycle.LiveData<java.util.List<com.delivery.rider.data.models.Order>> getOrders() {
        return null;
    }
    
    @org.jetbrains.annotations.NotNull()
    public final androidx.lifecycle.LiveData<com.delivery.rider.data.models.Order> getSelectedOrder() {
        return null;
    }
    
    @org.jetbrains.annotations.NotNull()
    public final androidx.lifecycle.LiveData<com.delivery.rider.ui.viewmodel.OrderState> getOrderState() {
        return null;
    }
    
    public final void loadOrders(@org.jetbrains.annotations.Nullable()
    java.lang.String status) {
    }
    
    public final void loadOrderDetails(@org.jetbrains.annotations.NotNull()
    java.lang.String orderId) {
    }
    
    public final void updateOrderStatus(@org.jetbrains.annotations.NotNull()
    java.lang.String orderId, @org.jetbrains.annotations.NotNull()
    java.lang.String status, @org.jetbrains.annotations.Nullable()
    java.lang.String notes) {
    }
    
    public final void cancelOrder(@org.jetbrains.annotations.NotNull()
    java.lang.String orderId, @org.jetbrains.annotations.NotNull()
    java.lang.String reason) {
    }
}