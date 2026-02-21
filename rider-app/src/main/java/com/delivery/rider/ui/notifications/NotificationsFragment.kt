package com.delivery.rider.ui.notifications

import android.os.Bundle
import android.view.LayoutInflater
import android.view.View
import android.view.ViewGroup
import androidx.fragment.app.Fragment
import androidx.fragment.app.viewModels
import androidx.recyclerview.widget.LinearLayoutManager
import androidx.recyclerview.widget.RecyclerView
import com.delivery.rider.R
import com.delivery.rider.ui.viewmodel.NotificationViewModel

class NotificationsFragment : Fragment() {
    private val viewModel: NotificationViewModel by viewModels()
    private lateinit var recyclerView: RecyclerView
    private lateinit var adapter: NotificationAdapter

    override fun onCreateView(
        inflater: LayoutInflater, container: ViewGroup?, savedInstanceState: Bundle?
    ): View = inflater.inflate(R.layout.fragment_notifications, container, false)

    override fun onViewCreated(view: View, savedInstanceState: Bundle?) {
        super.onViewCreated(view, savedInstanceState)
        recyclerView = view.findViewById(R.id.recyclerNotifications)
        adapter = NotificationAdapter(emptyList())
        recyclerView.layoutManager = LinearLayoutManager(requireContext())
        recyclerView.adapter = adapter

        observeViewModel()
        viewModel.loadNotifications()
    }

    private fun observeViewModel() {
        viewModel.notifications.observe(viewLifecycleOwner) { list ->
            adapter.update(list)
        }
    }
}
