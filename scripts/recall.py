import json
import sys
from pathlib import Path

# 1. Add project root to python path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# 2. Import scan function
try:
    from scan import scan
except ImportError:
    from scanner import scan

CLASSES = [
    {"name": "sql_injection", "cwe": "CWE-89"},
    {"name": "xss", "cwe": "CWE-79"},
    {"name": "command_injection", "cwe": "CWE-78"},
    {"name": "buffer_overflow", "cwe": "CWE-120"},
]


def run_recall():
    corpus_dir = PROJECT_ROOT / "corpus" / "dev"
    stats = {
        cls["name"]: {
            "cwe": cls["cwe"],
            "cases": 0,
            "detected": 0,
            "missed_files": [],
        }
        for cls in CLASSES
    }

    # Iterate ONLY over meta.json files to count exactly 1 case per folder
    for meta_path in corpus_dir.rglob("meta.json"):
        # Skip _template and samples
        if "_template" in meta_path.parts or "samples" in meta_path.parts:
            continue

        with open(meta_path, "r", encoding="utf-8") as f:
            meta = json.load(f)

        language = meta.get("language")
        target_cwe = meta.get("cwe")

        # Find which class this test case belongs to
        class_info = next(
            (c for c in CLASSES if c["cwe"] == target_cwe), None
        )
        if not class_info:
            continue

        # Find the actual source file to scan based on the language
        ext = ".c" if language == "c" else ".py"
        source_files = list(meta_path.parent.glob(f"*{ext}"))
        
        if not source_files:
            continue  # No source file found in this directory
            
        filepath = source_files[0]  # Take the target source file (e.g., source.py)
        
        cls_name = class_info["name"]
        stats[cls_name]["cases"] += 1

        # Run scanner on the actual source file
        findings = scan(str(filepath), language)

        # Check if the target CWE was found
        is_detected = any(
            f.get("cwe") == target_cwe for f in findings if isinstance(f, dict)
        )
        
        if is_detected:
            stats[cls_name]["detected"] += 1
        else:
            stats[cls_name]["missed_files"].append(
                str(filepath.relative_to(PROJECT_ROOT))
            )

    # Print Results Table
    print(
        f"{'Class':<20} | {'Cases':<8} | {'Detected':<8} | {'Recall':<8}"
    )
    print("-" * 50)

    total_cases = 0
    total_detected = 0
    underperforming_classes = []

    for cls_name, data in stats.items():
        cases = data["cases"]
        detected = data["detected"]
        recall = (detected / cases * 100) if cases > 0 else 0.0

        total_cases += cases
        total_detected += detected

        print(
            f"{cls_name:<20} | {cases:<8} | {detected:<8} | {recall:>6.1f}%"
        )

        if recall < 90.0:
            underperforming_classes.append(
                (cls_name, recall, data["missed_files"])
            )

    overall_recall = (
        (total_detected / total_cases * 100) if total_cases > 0 else 0.0
    )
    print("-" * 50)
    print(
        f"{'Overall':<20} | {total_cases:<8} | {total_detected:<8} | {overall_recall:>6.1f}%\n"
    )

    # Actions for P3
    if underperforming_classes:
        print("🚨 Classes Under 90% Target:")
        for cls_name, recall, missed in underperforming_classes:
            print(f" - {cls_name}: {recall:.1f}%")
            if missed:
                print(f"   --> Sample missed file for P3: {missed[0]}")
    else:
        print("✅ All individual classes met the >= 90% recall target!")


if __name__ == "__main__":
    run_recall()
