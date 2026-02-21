package com.delivery.rider.ui.profile

import android.app.AlertDialog
import android.content.Intent
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
import androidx.navigation.findNavController
import com.delivery.rider.R
import com.delivery.rider.ui.auth.LoginActivity
import com.delivery.rider.ui.viewmodel.AuthViewModel
import com.delivery.rider.ui.viewmodel.ChangePasscodeState
import com.delivery.rider.ui.viewmodel.RiderViewModel
import com.google.android.material.button.MaterialButton
import com.google.android.material.card.MaterialCardView
import dagger.hilt.android.AndroidEntryPoint

@AndroidEntryPoint
class ProfileFragment : Fragment() {
    
    private val riderViewModel: RiderViewModel by viewModels()
    private val authViewModel: AuthViewModel by viewModels()
    
    private lateinit var tvAvatar: TextView
    private lateinit var tvRiderName: TextView
    private lateinit var tvCompanyName: TextView
    private lateinit var tvOnlineProfile: TextView
    private lateinit var toggleOnlineProfile: LinearLayout
    private lateinit var tvRating: TextView
    private lateinit var tvDeliveries: TextView
    private lateinit var tvEarnings: TextView
    private lateinit var tvPhone: TextView
    private lateinit var tvBike: TextView
    private lateinit var cardChangePasscode: MaterialCardView
    private lateinit var cardMessages: MaterialCardView
    private lateinit var btnLogout: MaterialButton
    
    private var isOnline = false
    
    override fun onCreateView(
        inflater: LayoutInflater, container: ViewGroup?, savedInstanceState: Bundle?
    ): View = inflater.inflate(R.layout.fragment_profile, container, false)
    
    override fun onViewCreated(view: View, savedInstanceState: Bundle?) {
        super.onViewCreated(view, savedInstanceState)
        initViews(view)
        observeViewModel()
    }
    
    private fun initViews(view: View) {
        tvAvatar = view.findViewById(R.id.tvAvatar)
        tvRiderName = view.findViewById(R.id.tvRiderName)
        tvCompanyName = view.findViewById(R.id.tvCompanyName)
        tvOnlineProfile = view.findViewById(R.id.tvOnlineProfile)
        toggleOnlineProfile = view.findViewById(R.id.toggleOnlineProfile)
        tvRating = view.findViewById(R.id.tvRating)
        tvDeliveries = view.findViewById(R.id.tvDeliveries)
        tvEarnings = view.findViewById(R.id.tvEarnings)
        tvPhone = view.findViewById(R.id.tvPhone)
        tvBike = view.findViewById(R.id.tvBike)
        cardChangePasscode = view.findViewById(R.id.cardChangePasscode)
        cardMessages = view.findViewById(R.id.cardMessages)
        btnLogout = view.findViewById(R.id.btnLogout)
        
        toggleOnlineProfile.setOnClickListener {
            isOnline = !isOnline
            val status = if (isOnline) "online" else "offline"
            riderViewModel.updateStatus(status)
            updateOnlineUI()
        }
        
        cardChangePasscode.setOnClickListener { showChangePasscodeDialog() }
        cardMessages.setOnClickListener {
            // navigate to notifications screen
            val navController = requireActivity().findNavController(com.delivery.rider.R.id.nav_host_fragment)
            navController.navigate(com.delivery.rider.R.id.action_profile_to_notifications)
        }
        btnLogout.setOnClickListener { showLogoutDialog() }
    }
    
    private fun observeViewModel() {
        riderViewModel.riderProfile.observe(viewLifecycleOwner) { rider ->
            rider?.let {
                val name = it.displayName()
                tvRiderName.text = name
                tvAvatar.text = name.firstOrNull()?.uppercase() ?: "R"
                tvCompanyName.text = it.companyName ?: "Delivery Company"
                tvRating.text = "${String.format("%.1f", it.rating)} ⭐"
                tvDeliveries.text = "${it.deliveryCount()}"
                tvEarnings.text = "GH₵ ${String.format("%.0f", it.earningsTotal())}"
                tvPhone.text = it.phone
                tvBike.text = it.bikeId ?: "Not assigned"
                
                isOnline = it.status == "online"
                updateOnlineUI()
            }
        }
        
        authViewModel.changePasscodeState.observe(viewLifecycleOwner) { state ->
            when (state) {
                is ChangePasscodeState.Success -> {
                    Toast.makeText(requireContext(), getString(R.string.passcode_changed), Toast.LENGTH_SHORT).show()
                    authViewModel.resetChangePasscodeState()
                }
                is ChangePasscodeState.Error -> {
                    Toast.makeText(requireContext(), state.message, Toast.LENGTH_SHORT).show()
                    authViewModel.resetChangePasscodeState()
                }
                else -> {}
            }
        }
    }
    
    private fun updateOnlineUI() {
        if (isOnline) {
            tvOnlineProfile.text = getString(R.string.online_status)
            toggleOnlineProfile.setBackgroundResource(R.drawable.toggle_online)
        } else {
            tvOnlineProfile.text = getString(R.string.offline_status)
            toggleOnlineProfile.setBackgroundResource(R.drawable.toggle_offline)
        }
    }
    
    private fun showChangePasscodeDialog() {
        val container = LinearLayout(requireContext()).apply {
            orientation = LinearLayout.VERTICAL
            setPadding(48, 32, 48, 0)
        }
        
        val newPasscode = EditText(requireContext()).apply {
            hint = getString(R.string.new_passcode_hint)
            inputType = android.text.InputType.TYPE_CLASS_NUMBER or android.text.InputType.TYPE_NUMBER_VARIATION_PASSWORD
            maxEms = 5
        }
        
        val confirmPasscode = EditText(requireContext()).apply {
            hint = getString(R.string.confirm_passcode_hint)
            inputType = android.text.InputType.TYPE_CLASS_NUMBER or android.text.InputType.TYPE_NUMBER_VARIATION_PASSWORD
            maxEms = 5
        }
        
        container.addView(newPasscode, LinearLayout.LayoutParams(
            LinearLayout.LayoutParams.MATCH_PARENT, LinearLayout.LayoutParams.WRAP_CONTENT
        ).apply { bottomMargin = 16 })
        container.addView(confirmPasscode)
        
        AlertDialog.Builder(requireContext())
            .setTitle(getString(R.string.change_passcode_title))
            .setView(container)
            .setPositiveButton(getString(R.string.confirm)) { _, _ ->
                val newCode = newPasscode.text.toString()
                val confirmCode = confirmPasscode.text.toString()
                
                when {
                    newCode.length != 5 || !newCode.all { it.isDigit() } -> {
                        Toast.makeText(requireContext(), getString(R.string.passcode_invalid), Toast.LENGTH_SHORT).show()
                    }
                    newCode != confirmCode -> {
                        Toast.makeText(requireContext(), getString(R.string.passcode_mismatch), Toast.LENGTH_SHORT).show()
                    }
                    else -> {
                        authViewModel.changePasscode(newCode)
                    }
                }
            }
            .setNegativeButton(getString(R.string.cancel), null)
            .show()
    }
    
    private fun showLogoutDialog() {
        AlertDialog.Builder(requireContext())
            .setTitle(getString(R.string.btn_logout))
            .setMessage(getString(R.string.logout_confirm))
            .setPositiveButton(getString(R.string.confirm)) { _, _ ->
                riderViewModel.logout()
                startActivity(Intent(requireContext(), LoginActivity::class.java).apply {
                    flags = Intent.FLAG_ACTIVITY_NEW_TASK or Intent.FLAG_ACTIVITY_CLEAR_TASK
                })
            }
            .setNegativeButton(getString(R.string.cancel), null)
            .show()
    }
}
