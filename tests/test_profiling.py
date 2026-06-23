from turboclean.profiling import DynamicProfiler


def test_drift_detection(large_dirty_df):
    profiler = DynamicProfiler(large_dirty_df.lazy())
    profile = profiler.generate_profile()
    assert profile.column_profiles["value"].distribution_drift_score is not None
    assert profile.column_profiles["value"].distribution_drift_score > 0.1
