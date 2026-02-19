package com.delivery.rider.ui.viewmodel;

import com.delivery.rider.data.repository.OrderRepository;
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
public final class TrackingViewModel_Factory implements Factory<TrackingViewModel> {
  private final Provider<OrderRepository> orderRepositoryProvider;

  public TrackingViewModel_Factory(Provider<OrderRepository> orderRepositoryProvider) {
    this.orderRepositoryProvider = orderRepositoryProvider;
  }

  @Override
  public TrackingViewModel get() {
    return newInstance(orderRepositoryProvider.get());
  }

  public static TrackingViewModel_Factory create(
      Provider<OrderRepository> orderRepositoryProvider) {
    return new TrackingViewModel_Factory(orderRepositoryProvider);
  }

  public static TrackingViewModel newInstance(OrderRepository orderRepository) {
    return new TrackingViewModel(orderRepository);
  }
}
