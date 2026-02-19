package com.delivery.rider.ui.earnings

import android.app.AlertDialog
import android.os.Bundle
import android.view.LayoutInflater
import android.view.View
import android.view.ViewGroup
import android.widget.EditText
import android.widget.LinearLayout
import android.widget.TextView
import android.widget.Toast
import androidx.fragment.app.Fragment
import androidx.fragment.app.viewModels
import androidx.recyclerview.widget.LinearLayoutManager
import androidx.recyclerview.widget.RecyclerView
import com.delivery.rider.R
import com.delivery.rider.ui.viewmodel.EarningsViewModel
import com.delivery.rider.ui.viewmodel.EarningsState
import com.google.android.material.button.MaterialButton
import dagger.hilt.android.AndroidEntryPoint

@AndroidEntryPoint
class EarningsFragment : Fragment() {
    
    private val viewModel: EarningsViewModel by viewModels()
    
    private lateinit var tvTotalEarnings: TextView
    private lateinit var tvAvailable: TextView
    private lateinit var tvPending: TextView
    private lateinit var rvPayouts: RecyclerView
    private lateinit var emptyPayouts: LinearLayout
    private lateinit var btnRequestPayout: MaterialButton
    private lateinit var adapter: PayoutAdapter
    
    override fun onCreateView(
        inflater: LayoutInflater, container: ViewGroup?, savedInstanceState: Bundle?
    ): View = inflater.inflate(R.layout.fragment_earnings, container, false)
    
    override fun onViewCreated(view: View, savedInstanceState: Bundle?) {
        super.onViewCreated(view, savedInstanceState)
        initViews(view)
        observeViewModel()
        viewModel.loadEarnings("monthly")
        viewModel.loadPayoutHistory()
    }
    
    private fun initViews(view: View) {
        tvTotalEarnings = view.findViewById(R.id.tvTotalEarnings)
        tvAvailable = view.findViewById(R.id.tvAvailable)
        tvPending = view.findViewById(R.id.tvPending)
        rvPayouts = view.findViewById(R.id.rvPayouts)
        emptyPayouts = view.findViewById(R.id.emptyPayouts)
        btnRequestPayout = view.findViewById(R.id.btnRequestPayout)
        
        adapter = PayoutAdapter()
        rvPayouts.layoutManager = LinearLayoutManager(requireContext())
        rvPayouts.adapter = adapter
        
        btnRequestPayout.setOnClickListener { showPayoutDialog() }
    }
    
    private fun observeViewModel() {
        viewModel.earnings.observe(viewLifecycleOwner) { earnings ->
            earnings?.let {
                tvTotalEarnings.text = "GH₵ ${String.format("%.2f", it.totalEarnings)}"
                tvAvailable.text = "GH₵ ${String.format("%.2f", it.weeklyTotal)}"
                tvPending.text = "GH₵ ${String.format("%.2f", it.monthlyTotal)}"
            }
        }
        
        viewModel.payouts.observe(viewLifecycleOwner) { payouts ->
            if (payouts.isNullOrEmpty()) {
                emptyPayouts.visibility = View.VISIBLE
                rvPayouts.visibility = View.GONE
            } else {
                emptyPayouts.visibility = View.GONE
                rvPayouts.visibility = View.VISIBLE
                adapter.updatePayouts(payouts)
            }
        }
        
        viewModel.earningsState.observe(viewLifecycleOwner) { state ->
            when (state) {
                is EarningsState.PayoutRequested -> {
                    Toast.makeText(requireContext(), "Payout requested!", Toast.LENGTH_SHORT).show()
                }
                is EarningsState.Error -> {
                    Toast.makeText(requireContext(), state.message, Toast.LENGTH_SHORT).show()
                }
                else -> {}
            }
        }
    }
    
    private fun showPayoutDialog() {
        val input = EditText(requireContext()).apply {
            inputType = android.text.InputType.TYPE_CLASS_NUMBER or android.text.InputType.TYPE_NUMBER_FLAG_DECIMAL
            hint = "Enter amount in GH₵"
            setPadding(48, 32, 48, 32)
        }
        AlertDialog.Builder(requireContext())
            .setTitle(getString(R.string.btn_request_payout))
            .setView(input)
            .setPositiveButton(getString(R.string.confirm)) { _, _ ->
                val amount = input.text.toString().toFloatOrNull() ?: 0f
                if (amount > 0f) {
                    viewModel.requestPayout(amount)
                } else {
                    Toast.makeText(requireContext(), "Enter a valid amount", Toast.LENGTH_SHORT).show()
                }
            }
            .setNegativeButton(getString(R.string.cancel), null)
            .show()
    }
}
