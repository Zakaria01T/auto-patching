def zip_report(report_path):
    import subprocess
    subprocess.run(["zip", "-j", "/tmp/report.zip", "--", report_path], check=True)
    return "/tmp/report.zip"
