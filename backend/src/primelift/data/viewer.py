"""HTML viewer utilities for the generated London campaign dataset."""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

from primelift.utils.paths import DEFAULT_DATASET_PATH, DEFAULT_DATASET_VIEW_PATH

COLUMN_COLORS = [
    "#dbeafe",
    "#fee2e2",
    "#fef3c7",
    "#dcfce7",
    "#e0e7ff",
    "#fae8ff",
    "#cffafe",
    "#fde68a",
    "#fce7f3",
    "#ede9fe",
    "#d1fae5",
    "#fef9c3",
    "#e2e8f0",
    "#ffedd5",
    "#d9f99d",
    "#ede9fe",
    "#fecdd3",
    "#bae6fd",
    "#ddd6fe",
    "#fed7aa",
    "#bfdbfe",
    "#c7d2fe",
]


def _build_column_css(column_count: int) -> str:
    """Build CSS selectors that apply a unique color to each column."""

    rules: list[str] = []
    for index in range(column_count):
        color = COLUMN_COLORS[index % len(COLUMN_COLORS)]
        css_index = index + 1
        rules.append(
            f"""
            .dataset-table td:nth-child({css_index}),
            .dataset-table th:nth-child({css_index}) {{
              background-color: {color};
            }}
            """
        )

    rules.append(
        """
        .dataset-table td:nth-child(1),
        .dataset-table th:nth-child(1) {
          background-color: #93c5fd;
          font-weight: 700;
          position: sticky;
          left: 0;
          z-index: 3;
        }

        .dataset-table thead th:nth-child(1) {
          z-index: 4;
        }
        """
    )
    return "\n".join(rules)


def render_dataset_view(
    input_path: Path = DEFAULT_DATASET_PATH,
    output_path: Path = DEFAULT_DATASET_VIEW_PATH,
) -> Path:
    """Render the full dataset into a colorized HTML table for local inspection."""

    dataset = pd.read_csv(input_path)
    table_html = dataset.to_html(index=False, classes="dataset-table", border=0)
    column_css = _build_column_css(len(dataset.columns))

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>PrimeLift Dataset View</title>
  <style>
    body {{
      margin: 0;
      font-family: "Segoe UI", Arial, sans-serif;
      background: #0f172a;
      color: #e2e8f0;
    }}

    .page {{
      padding: 16px;
    }}

    .summary {{
      margin-bottom: 12px;
      padding: 12px 14px;
      border-radius: 12px;
      background: #111827;
      border: 1px solid #334155;
      line-height: 1.5;
    }}

    .table-wrap {{
      max-height: calc(100vh - 120px);
      overflow: auto;
      border: 1px solid #334155;
      border-radius: 12px;
      background: white;
      box-shadow: 0 8px 24px rgba(15, 23, 42, 0.25);
    }}

    .dataset-table {{
      border-collapse: separate;
      border-spacing: 0;
      width: max-content;
      min-width: 100%;
      color: #0f172a;
      font-size: 12px;
    }}

    .dataset-table thead th {{
      position: sticky;
      top: 0;
      z-index: 2;
      font-weight: 700;
    }}

    .dataset-table th,
    .dataset-table td {{
      padding: 8px 10px;
      border-right: 1px solid rgba(15, 23, 42, 0.08);
      border-bottom: 1px solid rgba(15, 23, 42, 0.08);
      white-space: nowrap;
      text-align: left;
    }}

    .dataset-table tbody tr:hover td {{
      filter: brightness(0.97);
    }}

    {column_css}
  </style>
</head>
<body>
  <div class="page">
    <div class="summary">
      <strong>PrimeLift London Campaign Dataset</strong><br>
      Full dataset view: 100,000 rows.<br>
      The first column, <code>user_id</code>, is highlighted more strongly because that is the current working column focus.
    </div>
    <div class="table-wrap">
      {table_html}
    </div>
  </div>
</body>
</html>
"""

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(html, encoding="utf-8")
    return output_path


def _build_argument_parser() -> argparse.ArgumentParser:
    """Create the CLI argument parser."""

    parser = argparse.ArgumentParser(
        description="Render the full PrimeLift dataset as a colorized HTML file."
    )
    parser.add_argument(
        "--input",
        type=Path,
        default=DEFAULT_DATASET_PATH,
        help="Input CSV path.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=DEFAULT_DATASET_VIEW_PATH,
        help="Output HTML path.",
    )
    return parser


def main() -> None:
    """CLI entrypoint for rendering the dataset view."""

    parser = _build_argument_parser()
    args = parser.parse_args()
    output_path = render_dataset_view(input_path=args.input, output_path=args.output)
    print(f"Wrote dataset view to {output_path}")


if __name__ == "__main__":
    main()
