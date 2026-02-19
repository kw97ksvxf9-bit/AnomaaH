package com.delivery.rider.data.models;

@kotlin.Metadata(mv = {1, 9, 0}, k = 1, xi = 48, d1 = {"\u00000\n\u0002\u0018\u0002\n\u0002\u0010\u0000\n\u0000\n\u0002\u0010 \n\u0002\u0018\u0002\n\u0000\n\u0002\u0010\u0007\n\u0002\b\u000f\n\u0002\u0010\u000b\n\u0002\b\u0002\n\u0002\u0010\b\n\u0000\n\u0002\u0010\u000e\n\u0000\b\u0086\b\u0018\u00002\u00020\u0001B+\u0012\f\u0010\u0002\u001a\b\u0012\u0004\u0012\u00020\u00040\u0003\u0012\u0006\u0010\u0005\u001a\u00020\u0006\u0012\u0006\u0010\u0007\u001a\u00020\u0006\u0012\u0006\u0010\b\u001a\u00020\u0006\u00a2\u0006\u0002\u0010\tJ\u000f\u0010\u0010\u001a\b\u0012\u0004\u0012\u00020\u00040\u0003H\u00c6\u0003J\t\u0010\u0011\u001a\u00020\u0006H\u00c6\u0003J\t\u0010\u0012\u001a\u00020\u0006H\u00c6\u0003J\t\u0010\u0013\u001a\u00020\u0006H\u00c6\u0003J7\u0010\u0014\u001a\u00020\u00002\u000e\b\u0002\u0010\u0002\u001a\b\u0012\u0004\u0012\u00020\u00040\u00032\b\b\u0002\u0010\u0005\u001a\u00020\u00062\b\b\u0002\u0010\u0007\u001a\u00020\u00062\b\b\u0002\u0010\b\u001a\u00020\u0006H\u00c6\u0001J\u0013\u0010\u0015\u001a\u00020\u00162\b\u0010\u0017\u001a\u0004\u0018\u00010\u0001H\u00d6\u0003J\t\u0010\u0018\u001a\u00020\u0019H\u00d6\u0001J\t\u0010\u001a\u001a\u00020\u001bH\u00d6\u0001R\u001c\u0010\u0002\u001a\b\u0012\u0004\u0012\u00020\u00040\u00038\u0006X\u0087\u0004\u00a2\u0006\b\n\u0000\u001a\u0004\b\n\u0010\u000bR\u0016\u0010\u0007\u001a\u00020\u00068\u0006X\u0087\u0004\u00a2\u0006\b\n\u0000\u001a\u0004\b\f\u0010\rR\u0016\u0010\b\u001a\u00020\u00068\u0006X\u0087\u0004\u00a2\u0006\b\n\u0000\u001a\u0004\b\u000e\u0010\rR\u0016\u0010\u0005\u001a\u00020\u00068\u0006X\u0087\u0004\u00a2\u0006\b\n\u0000\u001a\u0004\b\u000f\u0010\r\u00a8\u0006\u001c"}, d2 = {"Lcom/delivery/rider/data/models/EarningsResponse;", "", "daily", "", "Lcom/delivery/rider/data/models/Earnings;", "weeklyTotal", "", "monthlyTotal", "totalEarnings", "(Ljava/util/List;FFF)V", "getDaily", "()Ljava/util/List;", "getMonthlyTotal", "()F", "getTotalEarnings", "getWeeklyTotal", "component1", "component2", "component3", "component4", "copy", "equals", "", "other", "hashCode", "", "toString", "", "DeliveryRiderApp_debug"})
public final class EarningsResponse {
    @com.google.gson.annotations.SerializedName(value = "daily")
    @org.jetbrains.annotations.NotNull()
    private final java.util.List<com.delivery.rider.data.models.Earnings> daily = null;
    @com.google.gson.annotations.SerializedName(value = "weekly_total")
    private final float weeklyTotal = 0.0F;
    @com.google.gson.annotations.SerializedName(value = "monthly_total")
    private final float monthlyTotal = 0.0F;
    @com.google.gson.annotations.SerializedName(value = "total_earnings")
    private final float totalEarnings = 0.0F;
    
    public EarningsResponse(@org.jetbrains.annotations.NotNull()
    java.util.List<com.delivery.rider.data.models.Earnings> daily, float weeklyTotal, float monthlyTotal, float totalEarnings) {
        super();
    }
    
    @org.jetbrains.annotations.NotNull()
    public final java.util.List<com.delivery.rider.data.models.Earnings> getDaily() {
        return null;
    }
    
    public final float getWeeklyTotal() {
        return 0.0F;
    }
    
    public final float getMonthlyTotal() {
        return 0.0F;
    }
    
    public final float getTotalEarnings() {
        return 0.0F;
    }
    
    @org.jetbrains.annotations.NotNull()
    public final java.util.List<com.delivery.rider.data.models.Earnings> component1() {
        return null;
    }
    
    public final float component2() {
        return 0.0F;
    }
    
    public final float component3() {
        return 0.0F;
    }
    
    public final float component4() {
        return 0.0F;
    }
    
    @org.jetbrains.annotations.NotNull()
    public final com.delivery.rider.data.models.EarningsResponse copy(@org.jetbrains.annotations.NotNull()
    java.util.List<com.delivery.rider.data.models.Earnings> daily, float weeklyTotal, float monthlyTotal, float totalEarnings) {
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