package com.delivery.rider.ui.viewmodel;

@kotlin.Metadata(mv = {1, 9, 0}, k = 1, xi = 48, d1 = {"\u0000&\n\u0002\u0018\u0002\n\u0002\u0010\u0000\n\u0002\b\u0007\n\u0002\u0018\u0002\n\u0002\u0018\u0002\n\u0002\u0018\u0002\n\u0002\u0018\u0002\n\u0002\u0018\u0002\n\u0002\u0018\u0002\n\u0000\b6\u0018\u00002\u00020\u0001:\u0006\u0003\u0004\u0005\u0006\u0007\bB\u0007\b\u0004\u00a2\u0006\u0002\u0010\u0002\u0082\u0001\u0006\t\n\u000b\f\r\u000e\u00a8\u0006\u000f"}, d2 = {"Lcom/delivery/rider/ui/viewmodel/RiderState;", "", "()V", "Error", "Idle", "Loading", "ProfileUpdated", "StatusUpdated", "Success", "Lcom/delivery/rider/ui/viewmodel/RiderState$Error;", "Lcom/delivery/rider/ui/viewmodel/RiderState$Idle;", "Lcom/delivery/rider/ui/viewmodel/RiderState$Loading;", "Lcom/delivery/rider/ui/viewmodel/RiderState$ProfileUpdated;", "Lcom/delivery/rider/ui/viewmodel/RiderState$StatusUpdated;", "Lcom/delivery/rider/ui/viewmodel/RiderState$Success;", "DeliveryRiderApp_debug"})
public abstract class RiderState {
    
    private RiderState() {
        super();
    }
    
    @kotlin.Metadata(mv = {1, 9, 0}, k = 1, xi = 48, d1 = {"\u0000&\n\u0002\u0018\u0002\n\u0002\u0018\u0002\n\u0000\n\u0002\u0010\u000e\n\u0002\b\u0006\n\u0002\u0010\u000b\n\u0000\n\u0002\u0010\u0000\n\u0000\n\u0002\u0010\b\n\u0002\b\u0002\b\u0086\b\u0018\u00002\u00020\u0001B\r\u0012\u0006\u0010\u0002\u001a\u00020\u0003\u00a2\u0006\u0002\u0010\u0004J\t\u0010\u0007\u001a\u00020\u0003H\u00c6\u0003J\u0013\u0010\b\u001a\u00020\u00002\b\b\u0002\u0010\u0002\u001a\u00020\u0003H\u00c6\u0001J\u0013\u0010\t\u001a\u00020\n2\b\u0010\u000b\u001a\u0004\u0018\u00010\fH\u00d6\u0003J\t\u0010\r\u001a\u00020\u000eH\u00d6\u0001J\t\u0010\u000f\u001a\u00020\u0003H\u00d6\u0001R\u0011\u0010\u0002\u001a\u00020\u0003\u00a2\u0006\b\n\u0000\u001a\u0004\b\u0005\u0010\u0006\u00a8\u0006\u0010"}, d2 = {"Lcom/delivery/rider/ui/viewmodel/RiderState$Error;", "Lcom/delivery/rider/ui/viewmodel/RiderState;", "message", "", "(Ljava/lang/String;)V", "getMessage", "()Ljava/lang/String;", "component1", "copy", "equals", "", "other", "", "hashCode", "", "toString", "DeliveryRiderApp_debug"})
    public static final class Error extends com.delivery.rider.ui.viewmodel.RiderState {
        @org.jetbrains.annotations.NotNull()
        private final java.lang.String message = null;
        
        public Error(@org.jetbrains.annotations.NotNull()
        java.lang.String message) {
        }
        
        @org.jetbrains.annotations.NotNull()
        public final java.lang.String getMessage() {
            return null;
        }
        
        @org.jetbrains.annotations.NotNull()
        public final java.lang.String component1() {
            return null;
        }
        
        @org.jetbrains.annotations.NotNull()
        public final com.delivery.rider.ui.viewmodel.RiderState.Error copy(@org.jetbrains.annotations.NotNull()
        java.lang.String message) {
            return null;
        }
        
        @java.lang.Override()
        public boolean equals(@org.jetbrains.annotations.Nullable()
        java.lang.Object other) {
            return false;
        }
        
        @java.lang.Override()
        public int hashCode() {
            return 0;
        }
        
        @java.lang.Override()
        @org.jetbrains.annotations.NotNull()
        public java.lang.String toString() {
            return null;
        }
    }
    
    @kotlin.Metadata(mv = {1, 9, 0}, k = 1, xi = 48, d1 = {"\u0000\f\n\u0002\u0018\u0002\n\u0002\u0018\u0002\n\u0002\b\u0002\b\u00c6\u0002\u0018\u00002\u00020\u0001B\u0007\b\u0002\u00a2\u0006\u0002\u0010\u0002\u00a8\u0006\u0003"}, d2 = {"Lcom/delivery/rider/ui/viewmodel/RiderState$Idle;", "Lcom/delivery/rider/ui/viewmodel/RiderState;", "()V", "DeliveryRiderApp_debug"})
    public static final class Idle extends com.delivery.rider.ui.viewmodel.RiderState {
        @org.jetbrains.annotations.NotNull()
        public static final com.delivery.rider.ui.viewmodel.RiderState.Idle INSTANCE = null;
        
        private Idle() {
        }
    }
    
    @kotlin.Metadata(mv = {1, 9, 0}, k = 1, xi = 48, d1 = {"\u0000\f\n\u0002\u0018\u0002\n\u0002\u0018\u0002\n\u0002\b\u0002\b\u00c6\u0002\u0018\u00002\u00020\u0001B\u0007\b\u0002\u00a2\u0006\u0002\u0010\u0002\u00a8\u0006\u0003"}, d2 = {"Lcom/delivery/rider/ui/viewmodel/RiderState$Loading;", "Lcom/delivery/rider/ui/viewmodel/RiderState;", "()V", "DeliveryRiderApp_debug"})
    public static final class Loading extends com.delivery.rider.ui.viewmodel.RiderState {
        @org.jetbrains.annotations.NotNull()
        public static final com.delivery.rider.ui.viewmodel.RiderState.Loading INSTANCE = null;
        
        private Loading() {
        }
    }
    
    @kotlin.Metadata(mv = {1, 9, 0}, k = 1, xi = 48, d1 = {"\u0000*\n\u0002\u0018\u0002\n\u0002\u0018\u0002\n\u0000\n\u0002\u0018\u0002\n\u0002\b\u0006\n\u0002\u0010\u000b\n\u0000\n\u0002\u0010\u0000\n\u0000\n\u0002\u0010\b\n\u0000\n\u0002\u0010\u000e\n\u0000\b\u0086\b\u0018\u00002\u00020\u0001B\r\u0012\u0006\u0010\u0002\u001a\u00020\u0003\u00a2\u0006\u0002\u0010\u0004J\t\u0010\u0007\u001a\u00020\u0003H\u00c6\u0003J\u0013\u0010\b\u001a\u00020\u00002\b\b\u0002\u0010\u0002\u001a\u00020\u0003H\u00c6\u0001J\u0013\u0010\t\u001a\u00020\n2\b\u0010\u000b\u001a\u0004\u0018\u00010\fH\u00d6\u0003J\t\u0010\r\u001a\u00020\u000eH\u00d6\u0001J\t\u0010\u000f\u001a\u00020\u0010H\u00d6\u0001R\u0011\u0010\u0002\u001a\u00020\u0003\u00a2\u0006\b\n\u0000\u001a\u0004\b\u0005\u0010\u0006\u00a8\u0006\u0011"}, d2 = {"Lcom/delivery/rider/ui/viewmodel/RiderState$ProfileUpdated;", "Lcom/delivery/rider/ui/viewmodel/RiderState;", "rider", "Lcom/delivery/rider/data/models/Rider;", "(Lcom/delivery/rider/data/models/Rider;)V", "getRider", "()Lcom/delivery/rider/data/models/Rider;", "component1", "copy", "equals", "", "other", "", "hashCode", "", "toString", "", "DeliveryRiderApp_debug"})
    public static final class ProfileUpdated extends com.delivery.rider.ui.viewmodel.RiderState {
        @org.jetbrains.annotations.NotNull()
        private final com.delivery.rider.data.models.Rider rider = null;
        
        public ProfileUpdated(@org.jetbrains.annotations.NotNull()
        com.delivery.rider.data.models.Rider rider) {
        }
        
        @org.jetbrains.annotations.NotNull()
        public final com.delivery.rider.data.models.Rider getRider() {
            return null;
        }
        
        @org.jetbrains.annotations.NotNull()
        public final com.delivery.rider.data.models.Rider component1() {
            return null;
        }
        
        @org.jetbrains.annotations.NotNull()
        public final com.delivery.rider.ui.viewmodel.RiderState.ProfileUpdated copy(@org.jetbrains.annotations.NotNull()
        com.delivery.rider.data.models.Rider rider) {
            return null;
        }
        
        @java.lang.Override()
        public boolean equals(@org.jetbrains.annotations.Nullable()
        java.lang.Object other) {
            return false;
        }
        
        @java.lang.Override()
        public int hashCode() {
            return 0;
        }
        
        @java.lang.Override()
        @org.jetbrains.annotations.NotNull()
        public java.lang.String toString() {
            return null;
        }
    }
    
    @kotlin.Metadata(mv = {1, 9, 0}, k = 1, xi = 48, d1 = {"\u0000\f\n\u0002\u0018\u0002\n\u0002\u0018\u0002\n\u0002\b\u0002\b\u00c6\u0002\u0018\u00002\u00020\u0001B\u0007\b\u0002\u00a2\u0006\u0002\u0010\u0002\u00a8\u0006\u0003"}, d2 = {"Lcom/delivery/rider/ui/viewmodel/RiderState$StatusUpdated;", "Lcom/delivery/rider/ui/viewmodel/RiderState;", "()V", "DeliveryRiderApp_debug"})
    public static final class StatusUpdated extends com.delivery.rider.ui.viewmodel.RiderState {
        @org.jetbrains.annotations.NotNull()
        public static final com.delivery.rider.ui.viewmodel.RiderState.StatusUpdated INSTANCE = null;
        
        private StatusUpdated() {
        }
    }
    
    @kotlin.Metadata(mv = {1, 9, 0}, k = 1, xi = 48, d1 = {"\u0000\f\n\u0002\u0018\u0002\n\u0002\u0018\u0002\n\u0002\b\u0002\b\u00c6\u0002\u0018\u00002\u00020\u0001B\u0007\b\u0002\u00a2\u0006\u0002\u0010\u0002\u00a8\u0006\u0003"}, d2 = {"Lcom/delivery/rider/ui/viewmodel/RiderState$Success;", "Lcom/delivery/rider/ui/viewmodel/RiderState;", "()V", "DeliveryRiderApp_debug"})
    public static final class Success extends com.delivery.rider.ui.viewmodel.RiderState {
        @org.jetbrains.annotations.NotNull()
        public static final com.delivery.rider.ui.viewmodel.RiderState.Success INSTANCE = null;
        
        private Success() {
        }
    }
}