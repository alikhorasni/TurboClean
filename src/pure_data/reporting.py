from __future__ import annotations

from .contracts import DataProfile

class ReportGenerator:
    """Generate human-readable reports in Markdown and JSON formats."""

    @staticmethod
    def generate_markdown(
        profile: DataProfile, cleaning_steps: list[str] | None = None
    ) -> str:
        lines = ["# PureData Quality Report", ""]
        lines.append(f"**Schema:** {profile.schema}")
        lines.append("")
        lines.append("## Column Profiles")
        lines.append("| Column | Type | Nulls | Null Ratio | Drift Score | Suggested Rules |")
        lines.append("|--------|------|-------|------------|-------------|-----------------|")
        for col, prof in profile.column_profiles.items():
            nulls = prof.null_count
            ratio = f"{prof.null_ratio:.1%}"
            drift = (
                f"{prof.distribution_drift_score:.3f}"
                if prof.distribution_drift_score is not None
                else "N/A"
            )
            rules = ", ".join(r.name for r in prof.suggested_rules)
            lines.append(f"| {col} | {prof.dtype} | {nulls} | {ratio} | {drift} | {rules} |")

        if cleaning_steps:
            lines.append("")
            lines.append("## Applied Cleaning Steps")
            for step in cleaning_steps:
                lines.append(f"- {step}")

        return "\n".join(lines)

    @staticmethod
    def generate_json(profile: DataProfile) -> str:
        import json
        data = {
            "schema": str(profile.schema),
            "columns": {
                col: {
                    "dtype": str(prof.dtype),
                    "null_count": prof.null_count,
                    "null_ratio": prof.null_ratio,
                    "distribution_drift_score": prof.distribution_drift_score,
                    "suggested_rules": [r.name for r in prof.suggested_rules],
                }
                for col, prof in profile.column_profiles.items()
            }
        }
        return json.dumps(data, indent=2)
