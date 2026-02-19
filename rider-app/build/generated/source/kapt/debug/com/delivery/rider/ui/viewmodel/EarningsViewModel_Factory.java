package com.delivery.rider.ui.viewmodel;

import com.delivery.rider.data.repository.EarningsRepository;
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
public final class EarningsViewModel_Factory implements Factory<EarningsViewModel> {
  private final Provider<EarningsRepository> earningsRepositoryProvider;

  public EarningsViewModel_Factory(Provider<EarningsRepository> earningsRepositoryProvider) {
    this.earningsRepositoryProvider = earningsRepositoryProvider;
  }

  @Override
  public EarningsViewModel get() {
    return newInstance(earningsRepositoryProvider.get());
  }

  public static EarningsViewModel_Factory create(
      Provider<EarningsRepository> earningsRepositoryProvider) {
    return new EarningsViewModel_Factory(earningsRepositoryProvider);
  }

  public static EarningsViewModel newInstance(EarningsRepository earningsRepository) {
    return new EarningsViewModel(earningsRepository);
  }
}
