from click.testing import CliRunner
from pure_data.cli import main


def test_clean_auto_magic(tmp_path):
    # Create a small dirty CSV
    csv = tmp_path / "dirty.csv"
    csv.write_text("a,b\n1,2\n,3\n4,5\n")
    out = tmp_path / "clean.parquet"
    runner = CliRunner()
    result = runner.invoke(main, ["clean", str(csv), str(out), "--auto-magic"])
    assert result.exit_code == 0
    assert out.exists()
