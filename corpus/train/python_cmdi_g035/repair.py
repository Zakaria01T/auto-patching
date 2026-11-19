def email_report(subject, recipient, report_path):
    import subprocess
    with open(report_path, "rb") as report:
        subprocess.run(["mailx", "-s", subject, "--", recipient], stdin=report, check=True)
