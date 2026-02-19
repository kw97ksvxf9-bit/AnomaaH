package com.delivery.rider.data.api;

import android.content.Context;
import com.delivery.rider.data.local.SharedPrefManager;
import dagger.internal.DaggerGenerated;
import dagger.internal.Factory;
import dagger.internal.Preconditions;
import dagger.internal.QualifierMetadata;
import dagger.internal.ScopeMetadata;
import javax.annotation.processing.Generated;
import javax.inject.Provider;

@ScopeMetadata("javax.inject.Singleton")
@QualifierMetadata("dagger.hilt.android.qualifiers.ApplicationContext")
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
public final class NetworkModule_ProvideSharedPrefManagerFactory implements Factory<SharedPrefManager> {
  private final Provider<Context> contextProvider;

  public NetworkModule_ProvideSharedPrefManagerFactory(Provider<Context> contextProvider) {
    this.contextProvider = contextProvider;
  }

  @Override
  public SharedPrefManager get() {
    return provideSharedPrefManager(contextProvider.get());
  }

  public static NetworkModule_ProvideSharedPrefManagerFactory create(
      Provider<Context> contextProvider) {
    return new NetworkModule_ProvideSharedPrefManagerFactory(contextProvider);
  }

  public static SharedPrefManager provideSharedPrefManager(Context context) {
    return Preconditions.checkNotNullFromProvides(NetworkModule.INSTANCE.provideSharedPrefManager(context));
  }
}
