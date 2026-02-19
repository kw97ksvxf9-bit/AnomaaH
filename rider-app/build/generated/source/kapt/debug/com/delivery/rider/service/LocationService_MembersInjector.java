package com.delivery.rider.service;

import com.google.android.gms.location.FusedLocationProviderClient;
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
public final class LocationService_MembersInjector implements MembersInjector<LocationService> {
  private final Provider<FusedLocationProviderClient> fusedLocationProviderClientProvider;

  public LocationService_MembersInjector(
      Provider<FusedLocationProviderClient> fusedLocationProviderClientProvider) {
    this.fusedLocationProviderClientProvider = fusedLocationProviderClientProvider;
  }

  public static MembersInjector<LocationService> create(
      Provider<FusedLocationProviderClient> fusedLocationProviderClientProvider) {
    return new LocationService_MembersInjector(fusedLocationProviderClientProvider);
  }

  @Override
  public void injectMembers(LocationService instance) {
    injectFusedLocationProviderClient(instance, fusedLocationProviderClientProvider.get());
  }

  @InjectedFieldSignature("com.delivery.rider.service.LocationService.fusedLocationProviderClient")
  public static void injectFusedLocationProviderClient(LocationService instance,
      FusedLocationProviderClient fusedLocationProviderClient) {
    instance.fusedLocationProviderClient = fusedLocationProviderClient;
  }
}
