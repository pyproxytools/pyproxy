"""
This module provides functions for generating HTML reports to visualize
benchmark results comparing performance with and without a proxy.
"""

import os
import plotly.graph_objects as go

TEMPLATE_PATH = "benchmark/templates/report_template.html"


def generate_combined_table(all_results: dict) -> str:
    """
    Generates a single HTML table combining statistics for all
    URLs with sub-columns for avg, min, and max.

    Args:
        all_results (dict): A dictionary containing the results for each URL.

    Returns:
        str: The HTML table as a string.
    """
    table_html = """
    <div class="summary">
        <h2>Benchmark Results Summary</h2>
        <table>
            <thead>
                <tr>
                    <th>URL</th>
                    <th colspan="3">Without Proxy</th>
                    <th colspan="3">With Proxy</th>
                </tr>
                <tr>
                    <th></th>
                    <th>Avg (s)</th>
                    <th>Min (s)</th>
                    <th>Max (s)</th>
                    <th>Avg (s)</th>
                    <th>Min (s)</th>
                    <th>Max (s)</th>
                </tr>
            </thead>
            <tbody>
    """

    for url, (stats, _) in all_results.items():
        table_html += f"""
            <tr>
                <td>{url}</td>
                <td>{stats["avg_without_proxy"]:.5f}</td>
                <td>{stats["min_without_proxy"]:.5f}</td>
                <td>{stats["max_without_proxy"]:.5f}</td>
                <td>{stats["avg_with_proxy"]:.5f}</td>
                <td>{stats["min_with_proxy"]:.5f}</td>
                <td>{stats["max_with_proxy"]:.5f}</td>
            </tr>
        """

    table_html += """
            </tbody>
        </table>
    </div>
    <hr>
    """

    return table_html


def prepare_filenames(output_dir: str, timestamp: str) -> dict:
    """
    Prepares the filenames for the report and plotly files.

    Args:
        output_dir (str): The directory to save the report in.
        timestamp (str): The timestamp to use in filenames.

    Returns:
        dict: A dictionary containing the plotly and html file paths.
    """
    output_dir = os.path.normpath(output_dir)

    plotly_filename = f"benchmark_combined_interactive_{timestamp}.html"
    html_filename = f"benchmark_combined_report_{timestamp}.html"

    plotly_filepath = os.path.join(output_dir, plotly_filename)
    html_filepath = os.path.join(output_dir, html_filename)

    return {"plotly": plotly_filepath, "html": html_filepath}


def render_template(template_path: str, context: dict) -> str:
    """
    Renders an HTML template by replacing placeholders with provided context.

    Args:
        template_path (str): Path to the HTML template.
        context (dict): A dictionary with keys matching placeholders.

    Returns:
        str: The rendered HTML content.
    """
    with open(template_path, "r", encoding="utf-8") as f:
        template = f.read()
    return template.format(**context)


def create_combined_html_report(
    all_results: dict,
    avg_without_proxy: float,
    avg_with_proxy: float,
    percentage_change: float,
    output_dir: str,
    timestamp: str,
) -> None:
    """
    Generates an HTML report with the benchmark results, including graphs and statistics.
    Saves the report to the specified output directory.

    Args:
        all_results (dict): A dictionary containing the results for each URL.
        avg_without_proxy (float): The average time for requests without a proxy.
        avg_with_proxy (float): The average time for requests with a proxy.
        percentage_change (float): The percentage change in performance
                    between requests with and without a proxy.
        output_dir (str): The directory to save the report in.
        timestamp (str): The timestamp to use in filenames.

    Returns:
        None
    """
    fig = go.Figure()

    filenames = prepare_filenames(output_dir, timestamp)

    for url, (_, results) in all_results.items():
        fig.add_trace(
            go.Scatter(
                x=results["Request Number"],
                y=results["Without Proxy"],
                mode="lines+markers",
                name=f"Without Proxy - {url}",
            )
        )
        fig.add_trace(
            go.Scatter(
                x=results["Request Number"],
                y=results["With Proxy"],
                mode="lines+markers",
                name=f"With Proxy - {url}",
            )
        )

    fig.update_layout(
        title="Response Time per Request (All URLs)",
        xaxis_title="Request Number",
        yaxis_title="Response Time (seconds)",
    )

    fig.write_html(filenames["plotly"])

    html_sections = generate_combined_table(all_results)

    context = {
        "avg_without_proxy": f"{avg_without_proxy:.6f} seconds",
        "avg_with_proxy": f"{avg_with_proxy:.6f} seconds",
        "impact": (
            f"{'Improvement' if percentage_change < 0 else 'Slowdown'} "
            f"of {abs(percentage_change):.2f}%"
        ),
        "html_sections": html_sections,
        "plotly_filename": os.path.basename(filenames["plotly"]),
    }

    html_content = render_template(TEMPLATE_PATH, context)

    with open(filenames["html"], "w", encoding="utf-8") as f:
        f.write(html_content)

    print(f"\nThe combined report has been generated at '{filenames['html']}'.")
