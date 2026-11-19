def zip_report(report_path):
    import os
    cmd = "zip -j /tmp/report.zip " + report_path
    os.system(cmd)
    return "/tmp/report.zip"
