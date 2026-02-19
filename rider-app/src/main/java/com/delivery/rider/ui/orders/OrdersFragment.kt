package com.delivery.rider.ui.orders

import android.os.Bundle
import android.view.LayoutInflater
import android.view.View
import android.view.ViewGroup
import android.widget.LinearLayout
import android.widget.ProgressBar
import android.widget.TextView
import androidx.fragment.app.Fragment
import androidx.fragment.app.activityViewModels
import androidx.navigation.fragment.findNavController
import androidx.recyclerview.widget.LinearLayoutManager
import androidx.recyclerview.widget.RecyclerView
import com.delivery.rider.R
import com.delivery.rider.ui.viewmodel.OrderViewModel
import com.delivery.rider.ui.viewmodel.OrderState
import com.google.android.material.tabs.TabLayout
import dagger.hilt.android.AndroidEntryPoint

@AndroidEntryPoint
class OrdersFragment : Fragment() {
    
    private val viewModel: OrderViewModel by activityViewModels()
    
    private lateinit var rvOrders: RecyclerView
    private lateinit var progressBar: ProgressBar
    private lateinit var emptyState: LinearLayout
    private lateinit var tvOrderCount: TextView
    private lateinit var tabLayout: TabLayout
    private lateinit var adapter: OrderAdapter
    
    private val tabs = listOf("All", "Pending", "Assigned", "In Transit", "Delivered", "Cancelled")
    private val tabStatusMap = mapOf(
        0 to null, 1 to "pending", 2 to "assigned",
        3 to "in_transit", 4 to "delivered", 5 to "cancelled"
    )
    
    override fun onCreateView(
        inflater: LayoutInflater, container: ViewGroup?, savedInstanceState: Bundle?
    ): View = inflater.inflate(R.layout.fragment_orders, container, false)
    
    override fun onViewCreated(view: View, savedInstanceState: Bundle?) {
        super.onViewCreated(view, savedInstanceState)
        initViews(view)
        setupTabs()
        observeViewModel()
        viewModel.loadOrders()
    }
    
    private fun initViews(view: View) {
        rvOrders = view.findViewById(R.id.rvOrders)
        progressBar = view.findViewById(R.id.progressBar)
        emptyState = view.findViewById(R.id.emptyState)
        tvOrderCount = view.findViewById(R.id.tvOrderCount)
        tabLayout = view.findViewById(R.id.tabLayout)
        
        adapter = OrderAdapter { order ->
            viewModel.loadOrderDetails(order.id)
            findNavController().navigate(R.id.action_orders_to_details)
        }
        rvOrders.layoutManager = LinearLayoutManager(requireContext())
        rvOrders.adapter = adapter
    }
    
    private fun setupTabs() {
        tabs.forEach { tabLayout.addTab(tabLayout.newTab().setText(it)) }
        tabLayout.addOnTabSelectedListener(object : TabLayout.OnTabSelectedListener {
            override fun onTabSelected(tab: TabLayout.Tab) {
                viewModel.loadOrders(tabStatusMap[tab.position])
            }
            override fun onTabUnselected(tab: TabLayout.Tab) {}
            override fun onTabReselected(tab: TabLayout.Tab) {
                viewModel.loadOrders(tabStatusMap[tab.position])
            }
        })
    }
    
    private fun observeViewModel() {
        viewModel.orderState.observe(viewLifecycleOwner) { state ->
            when (state) {
                is OrderState.Loading -> {
                    progressBar.visibility = View.VISIBLE
                    rvOrders.visibility = View.GONE
                    emptyState.visibility = View.GONE
                }
                is OrderState.Success -> {
                    progressBar.visibility = View.GONE
                    rvOrders.visibility = View.VISIBLE
                }
                is OrderState.Error -> {
                    progressBar.visibility = View.GONE
                    emptyState.visibility = View.VISIBLE
                }
                else -> {}
            }
        }
        
        viewModel.orders.observe(viewLifecycleOwner) { orders ->
            if (orders.isNullOrEmpty()) {
                emptyState.visibility = View.VISIBLE
                rvOrders.visibility = View.GONE
                tvOrderCount.text = "0 active orders"
            } else {
                emptyState.visibility = View.GONE
                rvOrders.visibility = View.VISIBLE
                adapter.updateOrders(orders)
                val active = orders.count { it.status in listOf("assigned", "picked_up", "in_transit") }
                tvOrderCount.text = "$active active orders"
            }
        }
    }
}
