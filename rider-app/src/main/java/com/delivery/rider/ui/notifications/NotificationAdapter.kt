package com.delivery.rider.ui.notifications

import android.view.LayoutInflater
import android.view.View
import android.view.ViewGroup
import android.widget.TextView
import androidx.recyclerview.widget.RecyclerView
import com.delivery.rider.R
import com.delivery.rider.data.models.Notification

class NotificationAdapter(
    private var items: List<Notification>
) : RecyclerView.Adapter<NotificationAdapter.ViewHolder>() {

    class ViewHolder(view: View) : RecyclerView.ViewHolder(view) {
        val tvTitle: TextView = view.findViewById(R.id.tvTitle)
        val tvBody: TextView = view.findViewById(R.id.tvBody)
    }

    override fun onCreateViewHolder(parent: ViewGroup, viewType: Int): ViewHolder {
        val view = LayoutInflater.from(parent.context)
            .inflate(R.layout.item_notification, parent, false)
        return ViewHolder(view)
    }

    override fun onBindViewHolder(holder: ViewHolder, position: Int) {
        val notif = items[position]
        holder.tvTitle.text = notif.title ?: ""
        holder.tvBody.text = notif.message ?: ""
    }

    override fun getItemCount(): Int = items.size

    fun update(newItems: List<Notification>) {
        items = newItems
        notifyDataSetChanged()
    }
}
