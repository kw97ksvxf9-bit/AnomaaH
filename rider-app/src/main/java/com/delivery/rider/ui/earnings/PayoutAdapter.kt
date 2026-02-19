package com.delivery.rider.ui.earnings

import android.view.LayoutInflater
import android.view.View
import android.view.ViewGroup
import android.widget.TextView
import androidx.recyclerview.widget.RecyclerView
import com.delivery.rider.R
import com.delivery.rider.data.models.Payout
import java.text.SimpleDateFormat
import java.util.*

class PayoutAdapter(
    private val payouts: MutableList<Payout> = mutableListOf()
) : RecyclerView.Adapter<PayoutAdapter.PayoutViewHolder>() {
    
    private val dateFormat = SimpleDateFormat("MMM dd, yyyy", Locale.getDefault())
    
    override fun onCreateViewHolder(parent: ViewGroup, viewType: Int): PayoutViewHolder {
        val view = LayoutInflater.from(parent.context)
            .inflate(R.layout.item_payout, parent, false)
        return PayoutViewHolder(view)
    }
    
    override fun onBindViewHolder(holder: PayoutViewHolder, position: Int) {
        holder.bind(payouts[position])
    }
    
    override fun getItemCount() = payouts.size
    
    fun updatePayouts(newPayouts: List<Payout>) {
        payouts.clear()
        payouts.addAll(newPayouts)
        notifyDataSetChanged()
    }
    
    inner class PayoutViewHolder(itemView: View) : RecyclerView.ViewHolder(itemView) {
        
        private val tvPayoutAmount: TextView = itemView.findViewById(R.id.tvPayoutAmount)
        private val tvPayoutDate: TextView = itemView.findViewById(R.id.tvPayoutDate)
        private val tvPayoutStatus: TextView = itemView.findViewById(R.id.tvPayoutStatus)
        private val tvIcon: TextView = itemView.findViewById(R.id.tvIcon)
        
        fun bind(payout: Payout) {
            tvPayoutAmount.text = "GH₵ ${String.format("%.2f", payout.amount)}"
            tvPayoutDate.text = dateFormat.format(Date(payout.createdAt))
            tvPayoutStatus.text = payout.status.replaceFirstChar { it.uppercase() }
            
            // Color based on status
            val color = when (payout.status) {
                "completed" -> R.color.success
                "pending" -> R.color.warning
                "processing" -> R.color.info
                "failed" -> R.color.error
                else -> R.color.text_secondary
            }
            tvPayoutAmount.setTextColor(itemView.context.getColor(color))
            
            tvIcon.text = when (payout.status) {
                "completed" -> "✅"
                "pending" -> "⏳"
                "processing" -> "🔄"
                "failed" -> "❌"
                else -> "💰"
            }
        }
    }
}
