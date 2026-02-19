package com.delivery.rider.ui.viewmodel;

import com.delivery.rider.data.repository.RiderRepository;
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
public final class RiderViewModel_Factory implements Factory<RiderViewModel> {
  private final Provider<RiderRepository> riderRepositoryProvider;

  public RiderViewModel_Factory(Provider<RiderRepository> riderRepositoryProvider) {
    this.riderRepositoryProvider = riderRepositoryProvider;
  }

  @Override
  public RiderViewModel get() {
    return newInstance(riderRepositoryProvider.get());
  }

  public static RiderViewModel_Factory create(Provider<RiderRepository> riderRepositoryProvider) {
    return new RiderViewModel_Factory(riderRepositoryProvider);
  }

  public static RiderViewModel newInstance(RiderRepository riderRepository) {
    return new RiderViewModel(riderRepository);
  }
}
