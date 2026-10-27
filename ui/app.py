import html
import json
import os

import requests
import streamlit as st
import time

API_URL = os.getenv("API_URL", "http://localhost:8000")
UPLOAD_PATH = "/jobs"
UPLOAD_FIELD = "file"
KEY_JOB_ID = "id"
KEY_STATUS = "status"
KEY_LANGUAGE = "language"
KEY_ERROR = "detail"
REQUEST_TIMEOUT_S = 15
MAX_FILE_SIZE_MB = 1

UPLOAD_URL = f"{API_URL.rstrip('/')}{UPLOAD_PATH}"
JOB_PATH = "/jobs"
POLL_INTERVAL_S = 1
POLL_TIMEOUT_S = 500

TERMINAL_STATUSES = {"clean", "rejected", "accepted", "needs_human"}
REASON_KEYS = (
    "message",
    "reason",
    "rejection_reason",
    "detail",
    "error",
    "cause",
    "errors",
)


st.set_page_config(
    page_title="Auto-Patching Agent",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="collapsed",
)


#STYLE 

STYLE = """
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=Space+Grotesk:wght@500;600;700&display=swap');

:root {
    --bg: #070B16;
    --bg-light: #101827;
    --panel: #111D30;
    --blue: #78ABFF;
    --white: #F6F9FF;
    --muted: #C0CCDE;
    --border: #34445D;
}

html {
    scroll-behavior: smooth;
    scroll-padding-top: 100px;
}

.stApp,
[data-testid="stAppViewContainer"],
[data-testid="stMain"],
[data-testid="stMainBlockContainer"] {
    background: var(--bg) !important;
    color: var(--white);
    font-family: 'DM Sans', sans-serif;
}

#MainMenu,
footer,
.stDeployButton,
[data-testid="stAppDeployButton"],
[data-testid="stToolbar"] {
    display: none !important;
}

header[data-testid="stHeader"] {
    background: var(--bg) !important;
}

.block-container {
    max-width: 1400px;
    margin: 0 auto;
    padding: 90px 2rem 4rem;
}

/* === HERO ========== */


.main-content {
    width: 100%;
    max-width: 1250px;
    margin: 0 auto;
    padding-top: 145px;
    scroll-margin-top: 90px;
    text-align: center;
    box-sizing: border-box;
}

.hero-brand {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    gap: 1.3rem;
    width: 100%;
    margin: 0 auto 1.7rem;
    text-align: center;
}

.hero-icon {
    display: flex;
    align-items: center;
    justify-content: center;
    flex-shrink: 0;
    width: 94px;
    height: 94px;
    border-radius: 25px;
    background: rgba(120,171,255,.10);
    border: 1px solid rgba(120,171,255,.30);
}

.hero-icon svg {
    width: 58px;
    height: 58px;
}

h1.hero-title {
    display: block !important;
    width: 100% !important;
    max-width: none !important;
    margin: 0 auto !important;
    padding: 0 !important;
    color: #FFFFFF !important;
    font-family: 'Space Grotesk', sans-serif !important;
    font-size: 76px !important;
    font-weight: 700 !important;
    line-height: 1.12 !important;
    letter-spacing: -2.5px !important;
    text-align: center !important;
    white-space: normal !important;
}

.hero-description {
    display: block !important;
    width: 100% !important;
    max-width: 950px !important;
    margin-left: auto !important;
    margin-right: auto !important;
    padding: 0 !important;
    box-sizing: border-box !important;
    color: var(--muted);
    font-size: 1.3rem;
    line-height: 1.8;
    text-align: center !important;
}

/* === INPUT MODE: FILE / URL === */

div[data-testid="stVerticalBlock"] > div:has(> div[data-testid="stSegmentedControl"]) {
    width: 100% !important;
    min-width: 0 !important;
    align-self: stretch !important;
}

div[data-testid="stSegmentedControl"] {
    display: block !important;
    width: 100% !important;
    min-width: 0 !important;
    max-width: none !important;
    box-sizing: border-box !important;
    margin-bottom: 1.2rem !important;
}

div[data-testid="stSegmentedControl"] > div {
    display: flex !important;
    width: 100% !important;
    min-width: 0 !important;
    max-width: none !important;
    box-sizing: border-box !important;
    gap: 8px !important;
    padding: 6px !important;
    background: #101827 !important;
    border: 1px solid var(--border) !important;
    border-radius: 12px !important;
}

div[data-testid="stSegmentedControl"] button {
    flex: 1 1 0% !important;
    width: 50% !important;
    min-width: 0 !important;
    max-width: none !important;
    min-height: 54px !important;
    box-sizing: border-box !important;
    justify-content: center !important;
    border: none !important;
    border-radius: 8px !important;
    font-size: 1.05rem !important;
    font-weight: 700 !important;
}

div[data-testid="stSegmentedControl"] button[aria-checked="true"] {
    background: var(--blue) !important;
    color: #07111F !important;
}

/* ===== FORM AND UPLOAD ==== */

[data-testid="stForm"] {
    width: 100% !important;
    max-width: 100% !important;
    box-sizing: border-box !important;
}

[data-testid="stFileUploader"] {
    width: 100% !important;
    margin-top: .2rem;
    text-align: left !important;
}

[data-testid="stFileUploader"] label,
[data-testid="stTextInput"] label {
    color: #E0EAF7 !important;
    font-size: .95rem !important;
    font-weight: 600 !important;
}

[data-testid="stFileUploaderDropzone"] {
    width: 100% !important;
    min-height: 185px !important;
    display: flex !important;
    align-items: center !important;
    justify-content: center !important;
    padding: 1.5rem 1rem !important;
    box-sizing: border-box !important;
    background: #101827 !important;
    border: 1.5px dashed #536985 !important;
    border-radius: 12px !important;
    transition: background .2s ease, border-color .2s ease;
}

[data-testid="stFileUploaderDropzone"]:hover {
    background: #152238 !important;
    border-color: var(--blue) !important;
}

[data-testid="stFileUploaderDropzone"] button {
    color: #07111F !important;
    background: #DCEAFF !important;
    border: none !important;
    border-radius: 7px !important;
    font-weight: 700 !important;
}

[data-testid="stFileUploaderDropzone"] button:hover {
    background: var(--blue) !important;
}

[data-testid="stFileUploaderDropzone"] small {
    color: #C0CCDE !important;
}

[data-testid="stTextInput"] input {
    color: white !important;
    background: #101827 !important;
    border: 1px solid #536985 !important;
    border-radius: 10px !important;
    min-height: 50px;
}

[data-testid="stTextInput"] input:focus {
    border-color: var(--blue) !important;
    box-shadow: 0 0 0 2px rgba(120,171,255,.15) !important;
}

[data-testid="stTextInput"] input::placeholder {
    color: #94A9C3 !important;
}

[data-testid="stTextInput"] input:disabled {
    opacity: .5 !important;
    cursor: not-allowed !important;
}

[data-testid="stFormSubmitButton"] {
    width: 100% !important;
}

[data-testid="stFormSubmitButton"] button {
    width: 100% !important;
    min-height: 52px;
    border-radius: 9px !important;
    font-weight: 700 !important;
    color: #07111F !important;
    background: var(--blue) !important;
    border: 1px solid var(--blue) !important;
    transition: transform .2s ease, background .2s ease;
}

[data-testid="stFormSubmitButton"] button:hover {
    color: #07111F !important;
    background: #A7CAFF !important;
    border-color: #A7CAFF !important;
    transform: translateY(-1px);
}

[data-testid="stFormSubmitButton"] button:disabled {
    opacity: .45 !important;
    cursor: not-allowed !important;
    transform: none !important;
}
/* === LEGAL NOTE === */

.legal-note {
    display: block !important;
    width: 100% !important;
    max-width: 950px !important;
    margin: 1.5rem auto 0 !important;
    padding: 0 !important;
    box-sizing: border-box !important;
    text-align: center !important;
    color: #AEBBD0;
    font-size: .88rem;
    line-height: 1.8;
}

.legal-note strong {
    color: #DCE6F5;
    font-weight: 600;
}
/* === RESULTS  === */


.section-title {
    color: white;
    font-family: 'Space Grotesk', sans-serif;
    font-size: 1.7rem;
    font-weight: 600;
    text-align: center;
    margin: 3rem 0 .6rem;
}

.result-file {
    color: #B4C4D9;
    font-size: .95rem;
    text-align: center;
    margin: 0 0 1rem;
    overflow-wrap: anywhere;
}

.result {
    border-top: 1px solid var(--border);
    border-bottom: 1px solid var(--border);
    padding: .3rem 1rem;
    text-align: left;
}

.result-row {
    display: flex;
    justify-content: space-between;
    align-items: center;
    flex-wrap: wrap;
    gap: 1rem;
    padding: .9rem 0;
    border-bottom: 1px solid rgba(255,255,255,.09);
}

.result-row:last-child {
    border-bottom: none;
}

.result-label {
    color: #AFC0D5;
    font-size: .95rem;
}

.result-value {
    color: white;
    font-weight: 600;
    font-size: .95rem;
    overflow-wrap: anywhere;
}

.pill {
    color: #C6DEFF;
    background: #203A5B;
    border-radius: 30px;
    padding: .25rem .75rem;
    font-size: .85rem;
    font-weight: 600;
}

.stAlert {
    text-align: left;
}

/* === FOOTER === */

.footer {
    text-align: center;
    color: #849AB5;
    font-size: .85rem;
    margin-top: 4rem;
    padding: 1.4rem 0;
    border-top: 1px solid rgba(255,255,255,.10);
}

/* == RESPONSIVE ==== */

@media (max-width: 900px) {
    

    h1.hero-title {
        font-size: 58px !important;
        letter-spacing: -1.5px !important;
    }

    .hero-icon {
        width: 82px;
        height: 82px;
    }

    .hero-icon svg {
        width: 50px;
        height: 50px;
    }

    .hero-description {
        font-size: 1.15rem;
    }
}

@media (max-width: 640px) {
    .block-container {
        padding-left: 1rem;
        padding-right: 1rem;
    }

    
    .main-content {
        padding-top: 120px;
    }

    .hero-brand {
        gap: 1rem;
    }

    .hero-icon {
        width: 68px;
        height: 68px;
        border-radius: 18px;
    }

    .hero-icon svg {
        width: 43px;
        height: 43px;
    }

    h1.hero-title {
        font-size: 40px !important;
        line-height: 1.15 !important;
        letter-spacing: -1px !important;
    }

    .hero-description {
        font-size: 1rem;
        line-height: 1.75;
        padding: 0 .25rem;
    }

    [data-testid="stSegmentedControl"] button {
        min-height: 48px !important;
        font-size: 1rem !important;
    }

    [data-testid="stFileUploaderDropzone"] {
        min-height: 160px !important;
        padding: 1rem .5rem !important;
    }

    .legal-note {
        font-size: .8rem;
    }
}
</style>
"""

st.markdown(STYLE, unsafe_allow_html=True)


# HELPERS 

def format_error(resp: requests.Response) -> str:
    try:
        detail = resp.json().get(KEY_ERROR, resp.text)
    except (ValueError, AttributeError):
        return resp.text or "No error message returned."

    if isinstance(detail, list):
        return "; ".join(
            str(item.get("msg", item)) if isinstance(item, dict) else str(item)
            for item in detail
        )

    return str(detail)


def extract_reason(data: dict) -> str | None:
    if not isinstance(data, dict):
        return None

    for key in REASON_KEYS:
        value = data.get(key)
        if not value:
            continue
        if isinstance(value, list):
            return "; ".join(
                str(item.get("msg", item)) if isinstance(item, dict) else str(item)
                for item in value
            )
        if isinstance(value, dict):
            return json.dumps(value, ensure_ascii=False)
        return str(value)

    return None


ALLOWED_EXTENSIONS = (".py", ".c")


def validate_file(uploaded) -> list[str]:
    errors = []

    name = uploaded.name.lower()
    if not name.endswith(ALLOWED_EXTENSIONS):
        ext = os.path.splitext(uploaded.name)[1] or "(none)"
        errors.append(
            f"Unsupported file type: {ext}. Only Python (.py) and C (.c) files are accepted."
        )

    if uploaded.size == 0:
        errors.append("The file is empty (0 B).")
    elif uploaded.size > MAX_FILE_SIZE_MB * 1024 * 1024:
        errors.append(f"The file exceeds the {MAX_FILE_SIZE_MB} MB limit.")

    return errors


def is_done(data: dict) -> bool:
    return (
        data.get(KEY_STATUS) in TERMINAL_STATUSES
        or isinstance(data.get("findings"), list)
    )


def poll_job(job_id: str) -> dict:
    job_url = f"{API_URL.rstrip('/')}{JOB_PATH}/{job_id}"
    deadline = time.monotonic() + POLL_TIMEOUT_S

    while time.monotonic() < deadline:
        response = requests.get(
            job_url,
            timeout=REQUEST_TIMEOUT_S,
        )

        if not response.ok:
            raise RuntimeError(
                f"Job API error {response.status_code}: "
                f"{format_error(response)}"
            )

        data = response.json()

        if is_done(data):
            return data

        time.sleep(POLL_INTERVAL_S)

    raise TimeoutError(
        "The scan is taking too long or failed on the server. "
        "Please try again."
    )


def pick(finding: dict, *keys, default="-"):
    for k in keys:
        if finding.get(k) not in (None, ""):
            return finding[k]
    return default


def render_findings(findings: list, filename: str = "-") -> None:
    rows = [
        {
            "File": filename,
            "Line": pick(f, "line"),
            "CWE": pick(f, "cwe"),
            "Severity": str(pick(f, "severity")).capitalize(),
        }
        for f in findings
        if isinstance(f, dict)
    ]
    st.dataframe(rows, hide_index=True, use_container_width=True)


def show_result(data: dict) -> None:
    job_id = html.escape(str(data.get(KEY_JOB_ID, "-")))
    status = html.escape(str(data.get(KEY_STATUS, "-")))
    language = html.escape(str(data.get(KEY_LANGUAGE, "-")))

    rows = [
        f'<div class="result-row"><span class="result-label">Job ID</span>'
        f'<span class="result-value">{job_id}</span></div>',
        f'<div class="result-row"><span class="result-label">Status</span>'
        f'<span class="pill">{status}</span></div>',
        f'<div class="result-row"><span class="result-label">Language</span>'
        f'<span class="result-value">{language}</span></div>',
    ]

    st.markdown(
        '<div class="result">' + "".join(rows) + "</div>",
        unsafe_allow_html=True,
    )


# HEADER

st.markdown("""
<style>
.site-header-fixed {
    position: fixed !important;
    top: 0 !important;
    left: 0 !important;
    width: 100vw !important;
    height: 76px !important;
    z-index: 999999 !important;
    box-sizing: border-box !important;
    padding: 0 5% !important;
    display: flex !important;
    align-items: center !important;
    justify-content: space-between !important;
    gap: 20px !important;
    background: #0B1530 !important;
    border-bottom: 1px solid #263653 !important;
    color: white !important;
}

.site-header-fixed .site-brand {
    font-size: 23px;
    font-weight: 800;
    color: white;
    white-space: nowrap;
}

.site-header-fixed .site-links {
    display: flex;
    align-items: center;
    justify-content: flex-end;
    gap: 20px;
    flex-wrap: wrap;
}

.site-header-fixed .site-links a {
    color: #CBD7E7 !important;
    text-decoration: none !important;
    font-size: 14px;
    font-weight: 600;
}

.site-header-fixed .site-links .site-signin {
    padding: 10px 14px;
    border: 1px solid #52627D;
    border-radius: 8px;
}

.site-header-fixed .site-links .site-signup {
    padding: 10px 14px;
    background: #8DBBFF;
    color: #07111F !important;
    border-radius: 8px;
}

div.block-container {
    padding-top: 6rem !important;
}

@media (max-width: 700px) {
    .site-header-fixed {
        padding: 0 14px !important;
    }

    .site-header-fixed .site-brand {
        font-size: 17px;
    }

    .site-header-fixed .site-links {
        gap: 8px;
    }

    .site-header-fixed .site-links a {
        font-size: 12px;
    }
}
</style>

<div class="site-header-fixed">
    <div class="site-brand">🛡️ Auto-Patching Agent</div>
    <div class="site-links">
        <a href="#home">Home</a>
        <a href="#analyze">Analyze</a>
        <a href="#results">Results</a>
        <a class="site-signin" href="#signin">Sign In</a>
        <a class="site-signup" href="#signup">Sign Up</a>
    </div>
</div>
""", unsafe_allow_html=True)

st.markdown('<div id="home"></div>', unsafe_allow_html=True)

#  HERO 


st.markdown(
    '<div class="main-content">'
    '<div class="hero-brand">'
    '<div class="hero-icon">'
    '<svg viewBox="0 0 48 48" fill="none" xmlns="http://www.w3.org/2000/svg">'
    '<path d="M24 4L40 10V21C40 30 33.5 37.5 24 42C14.5 37.5 8 30 8 21V10L24 4Z" '
    'stroke="#78ABFF" stroke-width="2.2" stroke-linejoin="round"/>'
    '<path d="M19 19L15 23L19 27M29 19L33 23L29 27M27 16L21 30" '
    'stroke="white" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"/>'
    '</svg></div>'
    '<h1 class="hero-title">Auto-Patching Agent</h1>'
    '</div>'
    '<p class="hero-description">'
    'Analyze your source code for potential security vulnerabilities and work '
    'toward safer code with automated patching. '
    'Upload a Python or C file to get started.'
    '</p></div>',
    unsafe_allow_html=True,
)


#  ANALYSIS 

st.markdown('<div id="analyze"></div>', unsafe_allow_html=True)
st.markdown("<div style='height:1.5rem'></div>", unsafe_allow_html=True)

left_space, center, right_space = st.columns([1, 10, 1])

with center:
    mode = st.segmented_control(
        label="Input method",
        options=["File", "URL"],
        default="File",
        key="input_mode",
        width="stretch",
        label_visibility="collapsed",
    )

    if mode == "URL":
        with st.form("url_form", border=False):
            st.text_input(
                "Source URL",
                placeholder="https://example.com/source.py",
                disabled=True,
            )

            st.caption("URL analysis is not available yet. Please upload a file.")

            st.form_submit_button(
                "Analyze URL  →",
                type="primary",
                use_container_width=True,
                disabled=True,
            )

    else:
        with st.form("upload_form", border=False):
            uploaded = st.file_uploader(
                "Upload a source file",
                #type=["py", "c"],
                help=(
                    "Accepted formats: Python (.py) and C (.c). "
                    "Maximum size: 1 MB."
                ),
            )

            submitted = st.form_submit_button(
                "Analyze file  →",
                type="primary",
                use_container_width=True,
            )

        if submitted:
            if uploaded is None:
                st.warning("Please select a Python or C file.")
            elif local_errors := validate_file(uploaded):
                for msg in local_errors:
                    st.error(msg)
            else:
                try:
                    with st.spinner("Submitting file..."):
                        response = requests.post(
                            UPLOAD_URL,
                            files={
                                UPLOAD_FIELD: (
                                    uploaded.name,
                                    uploaded.getvalue(),
                                )
                            },
                            timeout=REQUEST_TIMEOUT_S,
                        )
                except requests.exceptions.ConnectionError:
                    st.error(
                        f"Cannot reach the API at {API_URL}. "
                        "Check that FastAPI is running."
                    )
                except requests.exceptions.Timeout:
                    st.error("The API did not answer in time. Try again.")
                except requests.exceptions.RequestException as exc:
                    st.error(f"Upload request failed: {exc}")
                else:
                    if response.ok:
                        try:
                            data = response.json()
                        except ValueError:
                            st.error("The API returned an invalid JSON response.")
                        else:
                            if data.get(KEY_STATUS) == "rejected":
                                reason = extract_reason(data)
                                st.error(
                                    f"File rejected: {reason}"
                                    if reason
                                    else "The API rejected this file."
                                )
                            else:
                                job_id = data.get("job_id") or data.get("id")

                                if not job_id:
                                    st.error("The API response contains no job ID.")
                                else:
                                    try:
                                        with st.spinner("Scanning your file..."):
                                            result = poll_job(str(job_id))

                                        st.session_state["last_job"] = result
                                        st.session_state["last_filename"] = uploaded.name

                                        status = result.get("status")
                                        findings = result.get("findings")

                                        if status == "clean":
                                            st.success("Scan completed: clean, no findings detected.")
                                        elif status == "rejected":
                                            reason = extract_reason(result)
                                            st.error(
                                                f"File rejected: {reason}"
                                                if reason
                                                else "The API rejected this file."
                                            )
                                        elif isinstance(findings, list) and findings:
                                            st.warning(
                                                f"Scan completed: {len(findings)} finding(s) detected."
                                            )
                                        else:
                                            st.info(
                                                f"Scan finished with status: {status}"
                                            )

                                    except requests.exceptions.RequestException as exc:
                                        st.error(f"Unable to retrieve the job: {exc}")
                                    except (RuntimeError, TimeoutError, ValueError) as exc:
                                        st.error(str(exc))
                    else:
                        st.error(
                            f"API error {response.status_code}: "
                            f"{format_error(response)}"
                        )

    # LEGAL NOTE 

    st.markdown(
        """
        <div class="legal-note">
            <strong>File types:</strong> Python (.py) and C (.c).
            <strong>Maximum size:</strong> 1 MB.
            <br><br>
            By submitting a file, you confirm that you are authorized to share
            its contents for security analysis. Avoid uploading secrets,
            credentials, personal information or confidential source code
            unless you have permission.
        </div>
        """,
        unsafe_allow_html=True,
    )

    # RESULTS

    st.markdown('<div id="results"></div>', unsafe_allow_html=True)

    if st.session_state.get("last_job") is not None:
        st.markdown(
            '<div class="section-title">Latest analysis job</div>',
            unsafe_allow_html=True,
        )

        filename = html.escape(
            str(st.session_state.get("last_filename", "Source file"))
        )

        st.markdown(
            f'<p class="result-file">Submitted file: {filename}</p>',
            unsafe_allow_html=True,
        )

        show_result(st.session_state["last_job"])
    
    # Findings

    st.markdown(
        '<div id="findings"></div>'
        '<div class="section-title">Findings</div>',
        unsafe_allow_html=True,
    )

    job = st.session_state.get("last_job")

    if job:
        status = job.get("status")
        findings = job.get("findings")

        if status == "clean":
            st.success("Clean — no findings detected.")
        elif status == "rejected":
            st.error(
                f"The file was rejected: "
                f"{extract_reason(job) or 'no reason provided.'}"
            )
        elif isinstance(findings, list) and findings:
            render_findings(
                findings,
                job.get("filename")
                or st.session_state.get("last_filename", "-"),
            )
        else:
            st.info(f"Job status: {status}")

# FOOTER 

st.markdown(
    '<div class="footer">Auto-Patching Agent · Application Security</div>',
    unsafe_allow_html=True,
)