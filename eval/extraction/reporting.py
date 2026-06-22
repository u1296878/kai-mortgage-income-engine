def markdown_report(result: dict) -> str:
    lines = [
        "# Extraction Accuracy + Variance Report",
        "",
        f"Provider: `{result['provider']}`",
        f"Model: `{result['model']}`",
        f"Runs: `{result['runs']}`",
        "",
    ]
    for doc in result["documents"]:
        lines.extend(_doc_lines(doc))
    summary = result["summary"]
    lines.append(
        f"Top line: {summary['tieouts']}/{summary['tieout_total']} docs tie out; "
        f"variance {summary['varied_fields']} fields."
    )
    return "\n".join(lines)


def _doc_lines(doc: dict) -> list[str]:
    lines = [f"## {doc['id']}", ""]
    if doc["status"] != "DONE":
        return [*lines, f"{doc['status']}: {doc['reason']}", ""]
    lines.extend(["| field | expected | got by run | accuracy | variance |", "|---|---:|---:|---:|---|"])
    for field in doc["fields"]:
        lines.append(
            f"| `{field['field']}` | {_fmt(field['expected'])} | "
            f"{_fmt(field['got'])} | {field['accuracy']} | {_yes(field['varied'])} |"
        )
    if doc["subtotal"]:
        subtotal = doc["subtotal"]
        lines.extend(
            [
                "",
                f"Subtotal `{subtotal['type']}`: expected {_fmt(subtotal['expected'])}, "
                f"got {_fmt(subtotal['got'])} ({subtotal['status']}, {subtotal['accuracy']}).",
            ]
        )
    lines.append("")
    return lines


def _fmt(value) -> str:
    if isinstance(value, list):
        return ", ".join(str(item) for item in value)
    return str(value)


def _yes(value: bool) -> str:
    return "yes" if value else "no"
