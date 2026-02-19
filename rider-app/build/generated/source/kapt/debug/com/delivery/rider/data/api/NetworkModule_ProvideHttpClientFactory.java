package com.delivery.rider.data.api;

import com.delivery.rider.data.local.SharedPrefManager;
import dagger.internal.DaggerGenerated;
import dagger.internal.Factory;
import dagger.internal.Preconditions;
import dagger.internal.QualifierMetadata;
import dagger.internal.ScopeMetadata;
import javax.annotation.processing.Generated;
import javax.inject.Provider;
import okhttp3.OkHttpClient;

@ScopeMetadata("javax.inject.Singleton")
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
public final class NetworkModule_ProvideHttpClientFactory implements Factory<OkHttpClient> {
  private final Provider<SharedPrefManager> sharedPrefManagerProvider;

  public NetworkModule_ProvideHttpClientFactory(
      Provider<SharedPrefManager> sharedPrefManagerProvider) {
    this.sharedPrefManagerProvider = sharedPrefManagerProvider;
  }

  @Override
  public OkHttpClient get() {
    return provideHttpClient(sharedPrefManagerProvider.get());
  }

  public static NetworkModule_ProvideHttpClientFactory create(
      Provider<SharedPrefManager> sharedPrefManagerProvider) {
    return new NetworkModule_ProvideHttpClientFactory(sharedPrefManagerProvider);
  }

  public static OkHttpClient provideHttpClient(SharedPrefManager sharedPrefManager) {
    return Preconditions.checkNotNullFromProvides(NetworkModule.INSTANCE.provideHttpClient(sharedPrefManager));
  }
}
