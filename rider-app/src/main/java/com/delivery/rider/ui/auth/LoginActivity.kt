package com.delivery.rider.ui.auth

import android.content.Intent
import android.os.Bundle
import android.view.View
import android.widget.EditText
import android.widget.ProgressBar
import android.widget.TextView
import androidx.activity.viewModels
import androidx.appcompat.app.AppCompatActivity
import com.delivery.rider.R
import com.delivery.rider.ui.main.MainActivity
import com.delivery.rider.ui.viewmodel.AuthViewModel
import com.delivery.rider.ui.viewmodel.LoginState
import com.google.android.material.button.MaterialButton
import dagger.hilt.android.AndroidEntryPoint

@AndroidEntryPoint
class LoginActivity : AppCompatActivity() {
    
    private val viewModel: AuthViewModel by viewModels()
    
    private lateinit var etPhone: EditText
    private lateinit var etPasscode: EditText
    private lateinit var btnLogin: MaterialButton
    private lateinit var loginProgress: ProgressBar
    private lateinit var tvError: TextView
    
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        
        // If already logged in, go to main
        if (viewModel.isLoggedIn()) {
            startMain()
            return
        }
        
        setContentView(R.layout.activity_login)
        initViews()
        observeViewModel()
    }
    
    private fun initViews() {
        etPhone = findViewById(R.id.etPhone)
        etPasscode = findViewById(R.id.etPasscode)
        btnLogin = findViewById(R.id.btnLogin)
        loginProgress = findViewById(R.id.loginProgress)
        tvError = findViewById(R.id.tvError)
        
        btnLogin.setOnClickListener {
            val phone = etPhone.text.toString().trim()
            val passcode = etPasscode.text.toString().trim()
            
            // Validate
            if (phone.length < 10) {
                showError(getString(R.string.login_error_phone))
                return@setOnClickListener
            }
            if (passcode.length != 5 || !passcode.all { it.isDigit() }) {
                showError(getString(R.string.login_error_passcode))
                return@setOnClickListener
            }
            
            tvError.visibility = View.GONE
            viewModel.passcodeLogin(phone, passcode)
        }
    }
    
    private fun observeViewModel() {
        viewModel.loginState.observe(this) { state ->
            when (state) {
                is LoginState.Idle -> {
                    loginProgress.visibility = View.GONE
                    btnLogin.isEnabled = true
                }
                is LoginState.Loading -> {
                    loginProgress.visibility = View.VISIBLE
                    btnLogin.isEnabled = false
                    tvError.visibility = View.GONE
                }
                is LoginState.LoggedIn -> {
                    loginProgress.visibility = View.GONE
                    startMain()
                }
                is LoginState.Error -> {
                    loginProgress.visibility = View.GONE
                    btnLogin.isEnabled = true
                    showError(state.message)
                }
                else -> {}
            }
        }
    }
    
    private fun showError(msg: String) {
        tvError.text = msg
        tvError.visibility = View.VISIBLE
    }
    
    private fun startMain() {
        startActivity(Intent(this, MainActivity::class.java))
        finish()
    }
}
