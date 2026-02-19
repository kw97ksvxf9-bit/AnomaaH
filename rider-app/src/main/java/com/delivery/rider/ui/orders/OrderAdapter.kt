package com.delivery.rider.ui.orders

import android.view.LayoutInflater
import android.view.View
import android.view.ViewGroup
import android.widget.TextView
import androidx.recyclerview.widget.RecyclerView
import com.delivery.rider.R
import com.delivery.rider.data.models.Order

class OrderAdapter(
    private val orders: MutableList<Order> = mutableListOf(),
    private val onOrderClick: (Order) -> Unit
) : RecyclerView.Adapter<OrderAdapter.OrderViewHolder>() {
    
    override fun onCreateViewHolder(parent: ViewGroup, viewType: Int): OrderViewHolder {
        val view = LayoutInflater.from(parent.context)
            .inflate(R.layout.item_order, parent, false)
        return OrderViewHolder(view, onOrderClick)
    }
    
    override fun onBindViewHolder(holder: OrderViewHolder, position: Int) {
        holder.bind(orders[position])
    }
    
    override fun getItemCount() = orders.size
    
    fun updateOrders(newOrders: List<Order>) {
        orders.clear()
        orders.addAll(newOrders)
        notifyDataSetChanged()
    }
    
    inner class OrderViewHolder(
        itemView: View,
        private val onOrderClick: (Order) -> Unit
    ) : RecyclerView.ViewHolder(itemView) {
        
        private val tvOrderId: TextView = itemView.findViewById(R.id.tvOrderId)
        private val tvStatus: TextView = itemView.findViewById(R.id.tvStatus)
        private val tvPickup: TextView = itemView.findViewById(R.id.tvPickup)
        private val tvDropoff: TextView = itemView.findViewById(R.id.tvDropoff)
        private val tvFee: TextView = itemView.findViewById(R.id.tvFee)
        private val tvTime: TextView = itemView.findViewById(R.id.tvTime)
        
        fun bind(order: Order) {
            tvOrderId.text = "Order #${order.id.take(8)}"
            tvPickup.text = order.pickupAddress
            tvDropoff.text = order.dropoffAddress
            tvFee.text = "GH₵${String.format("%.2f", order.priceGhs)}"
            
            // Status badge
            val statusDisplay = order.status.replace("_", " ").replaceFirstChar { it.uppercase() }
            tvStatus.text = statusDisplay
            
            // Set badge background based on status
            val badgeBg = when (order.status.lowercase()) {
                "pending" -> R.drawable.badge_pending
                "assigned" -> R.drawable.badge_assigned
                "picked_up", "in_transit" -> R.drawable.badge_in_transit
                "delivered" -> R.drawable.badge_delivered
                "cancelled" -> R.drawable.badge_cancelled
                else -> R.drawable.badge_pending
            }
            tvStatus.setBackgroundResource(badgeBg)
            
            val statusColor = when (order.status.lowercase()) {
                "pending" -> R.color.status_pending_text
                "assigned" -> R.color.status_assigned_text
                "picked_up", "in_transit" -> R.color.status_in_transit_text
                "delivered" -> R.color.status_delivered_text
                "cancelled" -> R.color.status_cancelled_text
                else -> R.color.text_secondary
            }
            tvStatus.setTextColor(itemView.context.getColor(statusColor))
            
            // Time ago
            if (order.createdAt > 0) {
                val mins = (System.currentTimeMillis() - order.createdAt) / 60000
                tvTime.text = when {
                    mins < 1 -> "Just now"
                    mins < 60 -> "${mins}m ago"
                    mins < 1440 -> "${mins / 60}h ago"
                    else -> "${mins / 1440}d ago"
                }
            } else {
                tvTime.text = ""
            }
            
            itemView.setOnClickListener { onOrderClick(order) }
        }
    }
}
