package com.delivery.rider.ui.orders

import android.os.Bundle
import android.view.LayoutInflater
import android.view.View
import android.view.ViewGroup
import android.widget.EditText
import android.widget.ImageView
import android.widget.TextView
import android.widget.Toast
import androidx.appcompat.app.AlertDialog
import androidx.fragment.app.Fragment
import androidx.fragment.app.activityViewModels
import androidx.navigation.fragment.findNavController
import com.delivery.rider.R
import com.delivery.rider.ui.viewmodel.OrderViewModel
import com.delivery.rider.ui.viewmodel.OrderState
import com.google.android.material.button.MaterialButton
import dagger.hilt.android.AndroidEntryPoint

@AndroidEntryPoint
class OrderDetailFragment : Fragment() {
    
    private val viewModel: OrderViewModel by activityViewModels()
    
    override fun onCreateView(
        inflater: LayoutInflater, container: ViewGroup?, savedInstanceState: Bundle?
    ): View = inflater.inflate(R.layout.fragment_order_details, container, false)
    
    override fun onViewCreated(view: View, savedInstanceState: Bundle?) {
        super.onViewCreated(view, savedInstanceState)
        
        val btnBack = view.findViewById<ImageView>(R.id.btnBack)
        val tvOrderId = view.findViewById<TextView>(R.id.tvOrderId)
        val tvStatus = view.findViewById<TextView>(R.id.tvStatus)
        val tvOrderDate = view.findViewById<TextView>(R.id.tvOrderDate)
        val tvPickupAddress = view.findViewById<TextView>(R.id.tvPickupAddress)
        val tvDropoffAddress = view.findViewById<TextView>(R.id.tvDropoffAddress)
        val tvCustomerName = view.findViewById<TextView>(R.id.tvCustomerName)
        val tvDeliveryFee = view.findViewById<TextView>(R.id.tvDeliveryFee)
        val btnAction = view.findViewById<MaterialButton>(R.id.btnAction)
        val btnCancel = view.findViewById<MaterialButton>(R.id.btnCancel)
        
        btnBack.setOnClickListener { findNavController().popBackStack() }
        
        viewModel.selectedOrder.observe(viewLifecycleOwner) { order ->
            order?.let {
                tvOrderId.text = "Order #${it.id.take(8)}"
                tvPickupAddress.text = it.pickupAddress
                tvDropoffAddress.text = it.dropoffAddress
                tvCustomerName.text = it.merchantId ?: "Customer"
                tvDeliveryFee.text = "GH₵${String.format("%.2f", it.priceGhs)}"
                
                val statusDisplay = it.status.replace("_", " ").replaceFirstChar { c -> c.uppercase() }
                tvStatus.text = statusDisplay
                
                // Badge styling
                val badgeBg = when (it.status.lowercase()) {
                    "pending" -> R.drawable.badge_pending
                    "assigned" -> R.drawable.badge_assigned
                    "picked_up", "in_transit" -> R.drawable.badge_in_transit
                    "delivered" -> R.drawable.badge_delivered
                    "cancelled" -> R.drawable.badge_cancelled
                    else -> R.drawable.badge_pending
                }
                tvStatus.setBackgroundResource(badgeBg)
                
                // Action button based on status
                when (it.status.lowercase()) {
                    "pending" -> {
                        btnAction.text = getString(R.string.btn_accept)
                        btnAction.visibility = View.VISIBLE
                        btnCancel.visibility = View.GONE
                    }
                    "assigned" -> {
                        btnAction.text = getString(R.string.btn_picked_up)
                        btnAction.visibility = View.VISIBLE
                        btnCancel.visibility = View.VISIBLE
                    }
                    "picked_up" -> {
                        btnAction.text = getString(R.string.btn_in_transit)
                        btnAction.visibility = View.VISIBLE
                        btnCancel.visibility = View.VISIBLE
                    }
                    "in_transit" -> {
                        btnAction.text = getString(R.string.btn_delivered)
                        btnAction.visibility = View.VISIBLE
                        btnCancel.visibility = View.GONE
                    }
                    else -> {
                        btnAction.visibility = View.GONE
                        btnCancel.visibility = View.GONE
                    }
                }
                
                btnAction.setOnClickListener { _ ->
                    val nextStatus = when (it.status.lowercase()) {
                        "pending" -> "assigned"
                        "assigned" -> "picked_up"
                        "picked_up" -> "in_transit"
                        "in_transit" -> "delivered"
                        else -> return@setOnClickListener
                    }
                    viewModel.updateOrderStatus(it.id, nextStatus)
                }
                
                btnCancel.setOnClickListener { _ ->
                    showCancelDialog(it.id)
                }
            }
        }
    }
    
    private fun showCancelDialog(orderId: String) {
        val input = EditText(requireContext()).apply {
            hint = getString(R.string.cancel_reason_hint)
            setPadding(48, 32, 48, 32)
        }
        AlertDialog.Builder(requireContext())
            .setTitle(getString(R.string.btn_cancel_order))
            .setView(input)
            .setPositiveButton(getString(R.string.confirm)) { _, _ ->
                val reason = input.text.toString()
                if (reason.isNotEmpty()) {
                    viewModel.cancelOrder(orderId, reason)
                    Toast.makeText(requireContext(), "Order cancelled", Toast.LENGTH_SHORT).show()
                }
            }
            .setNegativeButton(getString(R.string.cancel), null)
            .show()
    }
}
