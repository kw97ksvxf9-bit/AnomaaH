package com.delivery.rider.data.repository;

import com.delivery.rider.data.api.ApiService;
import com.delivery.rider.data.local.SharedPrefManager;
import dagger.internal.DaggerGenerated;
import dagger.internal.Factory;
import dagger.internal.QualifierMetadata;
import dagger.internal.ScopeMetadata;
import javax.annotation.processing.Generated;
import javax.inject.Provider;

@ScopeMetadata
@QualifierMetadata
@DaggerGenerated
@Generated(
    value = "dagger.internal.codegen.ComponentProcessor",
    comments = "https://dagger.dev"
)
@SuppressWarnings({
    "unchecked",
    "rawtypes",
    "KotlinInternal",
    "KotlinInternalInJava"
})
public final class AuthRepository_Factory implements Factory<AuthRepository> {
  private final Provider<ApiService> apiServiceProvider;

  private final Provider<SharedPrefManager> sharedPrefManagerProvider;

  public AuthRepository_Factory(Provider<ApiService> apiServiceProvider,
      Provider<SharedPrefManager> sharedPrefManagerProvider) {
    this.apiServiceProvider = apiServiceProvider;
    this.sharedPrefManagerProvider = sharedPrefManagerProvider;
  }

  @Override
  public AuthRepository get() {
    return newInstance(apiServiceProvider.get(), sharedPrefManagerProvider.get());
  }

  public static AuthRepository_Factory create(Provider<ApiService> apiServiceProvider,
      Provider<SharedPrefManager> sharedPrefManagerProvider) {
    return new AuthRepository_Factory(apiServiceProvider, sharedPrefManagerProvider);
  }

  public static AuthRepository newInstance(ApiService apiService,
      SharedPrefManager sharedPrefManager) {
    return new AuthRepository(apiService, sharedPrefManager);
  }
}
