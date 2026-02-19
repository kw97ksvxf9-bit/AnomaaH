package com.delivery.rider.service;

import com.delivery.rider.data.local.SharedPrefManager;
import dagger.MembersInjector;
import dagger.internal.DaggerGenerated;
import dagger.internal.InjectedFieldSignature;
import dagger.internal.QualifierMetadata;
import javax.annotation.processing.Generated;
import javax.inject.Provider;

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
public final class RiderMessagingService_MembersInjector implements MembersInjector<RiderMessagingService> {
  private final Provider<SharedPrefManager> sharedPrefManagerProvider;

  public RiderMessagingService_MembersInjector(
      Provider<SharedPrefManager> sharedPrefManagerProvider) {
    this.sharedPrefManagerProvider = sharedPrefManagerProvider;
  }

  public static MembersInjector<RiderMessagingService> create(
      Provider<SharedPrefManager> sharedPrefManagerProvider) {
    return new RiderMessagingService_MembersInjector(sharedPrefManagerProvider);
  }

  @Override
  public void injectMembers(RiderMessagingService instance) {
    injectSharedPrefManager(instance, sharedPrefManagerProvider.get());
  }

  @InjectedFieldSignature("com.delivery.rider.service.RiderMessagingService.sharedPrefManager")
  public static void injectSharedPrefManager(RiderMessagingService instance,
      SharedPrefManager sharedPrefManager) {
    instance.sharedPrefManager = sharedPrefManager;
  }
}
