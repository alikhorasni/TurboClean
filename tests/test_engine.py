from turboclean.cleaners import MissingCleaner
from turboclean.contracts import FileFormat


def test_load_and_clean(large_dirty_df, engine):
    lf = large_dirty_df.lazy()
    engine._lf = lf
    engine.clean([MissingCleaner("value", "mean")])
    result = engine.collect()
    assert result["value"].null_count() == 0

def test_suggest_rules(engine, large_dirty_df):
    engine._lf = large_dirty_df.lazy()
    rules = engine.suggest_cleansing_rules()
    assert len(rules) > 0

def test_write_parquet(tmp_path, large_dirty_df, engine):
    engine._lf = large_dirty_df.lazy()
    out = tmp_path / "test.parquet"
    engine.write(out, FileFormat.PARQUET)
    assert out.exists()
