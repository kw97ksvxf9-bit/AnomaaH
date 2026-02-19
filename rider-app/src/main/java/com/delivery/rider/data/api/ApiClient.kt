package com.delivery.rider.data.api

import android.content.Context
import com.delivery.rider.BuildConfig
import com.delivery.rider.data.local.SharedPrefManager
import dagger.Module
import dagger.Provides
import dagger.hilt.InstallIn
import dagger.hilt.android.qualifiers.ApplicationContext
import dagger.hilt.components.SingletonComponent
import okhttp3.Interceptor
import okhttp3.OkHttpClient
import okhttp3.logging.HttpLoggingInterceptor
import retrofit2.Retrofit
import retrofit2.converter.gson.GsonConverterFactory
import javax.inject.Singleton

// ==================== Interceptors ====================

class AuthInterceptor(
    private val sharedPrefManager: SharedPrefManager
) : Interceptor {
    override fun intercept(chain: Interceptor.Chain): okhttp3.Response {
        val originalRequest = chain.request()
        
        // Add authorization token if available
        val token = sharedPrefManager.getAuthToken()
        val requestBuilder = originalRequest.newBuilder()
        
        if (!token.isNullOrEmpty()) {
            requestBuilder.addHeader("Authorization", "Bearer $token")
        }
        
        // Add common headers
        requestBuilder.addHeader("Content-Type", "application/json")
        requestBuilder.addHeader("Accept", "application/json")
        
        return chain.proceed(requestBuilder.build())
    }
}

class ErrorInterceptor : Interceptor {
    override fun intercept(chain: Interceptor.Chain): okhttp3.Response {
        val response = chain.proceed(chain.request())
        
        // Handle common errors
        when (response.code) {
            401 -> {
                // Unauthorized - token expired or invalid
                // Trigger logout / refresh token flow
            }
            403 -> {
                // Forbidden
            }
            404 -> {
                // Not found
            }
            500, 502, 503 -> {
                // Server errors
            }
        }
        
        return response
    }
}

// ==================== Hilt Module ====================

@Module
@InstallIn(SingletonComponent::class)
object NetworkModule {
    
    @Provides
    @Singleton
    fun provideSharedPrefManager(
        @ApplicationContext context: Context
    ): SharedPrefManager = SharedPrefManager(context)
    
    @Provides
    @Singleton
    fun provideHttpClient(
        sharedPrefManager: SharedPrefManager
    ): OkHttpClient {
        val httpClientBuilder = OkHttpClient.Builder()
        
        // Add interceptors
        httpClientBuilder.addInterceptor(AuthInterceptor(sharedPrefManager))
        httpClientBuilder.addInterceptor(ErrorInterceptor())
        
        // Add logging interceptor in debug mode
        if (BuildConfig.DEBUG) {
            val loggingInterceptor = HttpLoggingInterceptor().apply {
                level = HttpLoggingInterceptor.Level.BODY
            }
            httpClientBuilder.addInterceptor(loggingInterceptor)
        }
        
        // Set timeout
        httpClientBuilder.connectTimeout(30, java.util.concurrent.TimeUnit.SECONDS)
        httpClientBuilder.readTimeout(30, java.util.concurrent.TimeUnit.SECONDS)
        httpClientBuilder.writeTimeout(30, java.util.concurrent.TimeUnit.SECONDS)
        
        return httpClientBuilder.build()
    }
    
    @Provides
    @Singleton
    fun provideRetrofit(
        okHttpClient: OkHttpClient
    ): Retrofit = Retrofit.Builder()
        .baseUrl(BuildConfig.API_BASE_URL)
        .client(okHttpClient)
        .addConverterFactory(GsonConverterFactory.create())
        .build()
    
    @Provides
    @Singleton
    fun provideApiService(
        retrofit: Retrofit
    ): ApiService = retrofit.create(ApiService::class.java)
}
