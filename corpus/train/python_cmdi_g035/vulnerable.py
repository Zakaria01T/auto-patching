def email_report(subject, recipient, report_path):
    import os
    cmd = "mailx -s '{}' {} < {}".format(subject, recipient, report_path)
    os.system(cmd)
