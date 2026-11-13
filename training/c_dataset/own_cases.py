"""Our own C buffer overflow cases (option B): small functions that take input, like the
dev and gold cases, with varied copy functions and contexts.

Each case has a vulnerable and a repaired function, a normal call and an attack call.
check.py validates every case and drops it if any check fails. Names and patterns of
corpus/dev/bof_* and corpus/train/gold_bof_* are avoided on purpose.

    python3 training/c_dataset/own_cases.py   # writes candidates/own_bof_*/
"""
import json
import shutil
from pathlib import Path

HERE = Path(__file__).resolve().parent
OUT = HERE / "candidates"
LONG = '"' + "A" * 200 + '"'
H = "#include <stdio.h>\n#include <string.h>\n"
HS = "#include <stdio.h>\n#include <stdlib.h>\n#include <string.h>\n"
HV = "#include <stdarg.h>\n#include <stdio.h>\n"

# id, headers, vulnerable, repair, normal call, attack call, explanation
CASES = [
    ("own_bof_01", H, """void save_username(const char *user) {
    char name[20];
    strcpy(name, user);
    printf("user=%s\\n", name);
}""", """void save_username(const char *user) {
    char name[20];
    snprintf(name, sizeof(name), "%s", user);
    printf("user=%s\\n", name);
}""", 'save_username("alice")', f"save_username({LONG})",
     "Replaced strcpy with snprintf limited to the size of name."),

    ("own_bof_02", H, """struct server {
    char host[32];
    int port;
};

void set_host(const char *host) {
    struct server cfg;
    strcpy(cfg.host, host);
    cfg.port = 80;
    printf("%s:%d\\n", cfg.host, cfg.port);
}""", """struct server {
    char host[32];
    int port;
};

void set_host(const char *host) {
    struct server cfg;
    if (strlen(host) >= sizeof(cfg.host)) {
        puts("host name too long");
        return;
    }
    strcpy(cfg.host, host);
    cfg.port = 80;
    printf("%s:%d\\n", cfg.host, cfg.port);
}""", 'set_host("example.org")', f"set_host({LONG})",
     "Rejected host names that do not fit in the host field before copying."),

    ("own_bof_03", HS, """void store_token(const char *token) {
    char *copy = malloc(16);
    if (copy == NULL)
        return;
    strcpy(copy, token);
    printf("token %s\\n", copy);
    free(copy);
}""", """void store_token(const char *token) {
    char *copy = malloc(16);
    if (copy == NULL)
        return;
    strncpy(copy, token, 15);
    copy[15] = '\\0';
    printf("token %s\\n", copy);
    free(copy);
}""", 'store_token("ab12cd34")', f"store_token({LONG})",
     "Limited the copy to the 16-byte heap buffer and terminated the string."),

    ("own_bof_04", H, """void print_level(const char *level) {
    char tag[8];
    strcpy(tag, level);
    printf("[%s]\\n", tag);
}""", """void print_level(const char *level) {
    char tag[8];
    snprintf(tag, sizeof(tag), "%s", level);
    printf("[%s]\\n", tag);
}""", 'print_level("WARN")', f"print_level({LONG})",
     "Replaced strcpy with snprintf limited to the size of tag."),

    ("own_bof_05", H, """void make_url(const char *host, const char *page) {
    char url[40] = "https://";
    strcat(url, host);
    strcat(url, page);
    puts(url);
}""", """void make_url(const char *host, const char *page) {
    char url[40];
    snprintf(url, sizeof(url), "https://%s%s", host, page);
    puts(url);
}""", 'make_url("example.org", "/index")', f'make_url({LONG}, "/index")',
     "Built the URL with one snprintf limited to the size of url instead of two strcat calls."),

    ("own_bof_06", H, """void add_extension(const char *base) {
    char file[24] = "";
    strcat(file, base);
    strcat(file, ".txt");
    puts(file);
}""", """void add_extension(const char *base) {
    char file[24] = "";
    strncat(file, base, sizeof(file) - strlen(file) - 1);
    strncat(file, ".txt", sizeof(file) - strlen(file) - 1);
    puts(file);
}""", 'add_extension("notes")', f"add_extension({LONG})",
     "Limited each append to the space left in file."),

    ("own_bof_07", H, """void build_query(const char *term) {
    char q[48] = "search?q=";
    strcat(q, term);
    puts(q);
}""", """void build_query(const char *term) {
    char q[48] = "search?q=";
    if (strlen(q) + strlen(term) >= sizeof(q)) {
        puts("query too long");
        return;
    }
    strcat(q, term);
    puts(q);
}""", 'build_query("lamps")', f"build_query({LONG})",
     "Checked that the search term fits in the query buffer before appending it."),

    ("own_bof_08", H, """void email_address(const char *user, const char *domain) {
    char mail[32];
    strcpy(mail, user);
    strcat(mail, "@");
    strcat(mail, domain);
    puts(mail);
}""", """void email_address(const char *user, const char *domain) {
    char mail[32];
    snprintf(mail, sizeof(mail), "%s@%s", user, domain);
    puts(mail);
}""", 'email_address("sam", "mail.com")', f'email_address({LONG}, "mail.com")',
     "Built the address with snprintf limited to the size of mail."),

    ("own_bof_09", H, """void format_price(const char *product, int cents) {
    char line[24];
    sprintf(line, "%s: %d.%02d", product, cents / 100, cents % 100);
    puts(line);
}""", """void format_price(const char *product, int cents) {
    char line[24];
    snprintf(line, sizeof(line), "%s: %d.%02d", product, cents / 100, cents % 100);
    puts(line);
}""", 'format_price("tea", 350)', f"format_price({LONG}, 350)",
     "Replaced sprintf with snprintf limited to the size of line."),

    ("own_bof_10", H, """void log_event(const char *user, const char *action) {
    char msg[40];
    sprintf(msg, "%s did %s", user, action);
    puts(msg);
}""", """void log_event(const char *user, const char *action) {
    char msg[40];
    snprintf(msg, sizeof(msg), "%s did %s", user, action);
    puts(msg);
}""", 'log_event("kim", "login")', f'log_event("kim", {LONG})',
     "Replaced sprintf with snprintf limited to the size of msg."),

    ("own_bof_11", H, """void header_line(const char *name, const char *value) {
    char h[32];
    sprintf(h, "%s: %s", name, value);
    puts(h);
}""", """void header_line(const char *name, const char *value) {
    char h[32];
    snprintf(h, sizeof(h), "%s: %s", name, value);
    puts(h);
}""", 'header_line("Accept", "text/html")', f'header_line("Accept", {LONG})',
     "Replaced sprintf with snprintf limited to the size of h."),

    ("own_bof_12", H, """void temp_path(const char *dir, int id) {
    char p[20];
    sprintf(p, "%s/tmp%d", dir, id);
    puts(p);
}""", """void temp_path(const char *dir, int id) {
    char p[20];
    snprintf(p, sizeof(p), "%s/tmp%d", dir, id);
    puts(p);
}""", 'temp_path("/var", 7)', f"temp_path({LONG}, 7)",
     "Replaced sprintf with snprintf limited to the size of p."),

    ("own_bof_13", H, """void copy_packet(const char *payload, size_t len) {
    char buf[32];
    memcpy(buf, payload, len);
    printf("%zu bytes, first %c\\n", len, buf[0]);
}""", """void copy_packet(const char *payload, size_t len) {
    char buf[32];
    if (len > sizeof(buf)) {
        puts("packet too large");
        return;
    }
    memcpy(buf, payload, len);
    printf("%zu bytes, first %c\\n", len, buf[0]);
}""", 'copy_packet("hello", 5)', f"copy_packet({LONG}, 200)",
     "Rejected payloads larger than the buffer before memcpy."),

    ("own_bof_14", H, """void first_field(const char *line) {
    char field[12];
    const char *comma = strchr(line, ',');
    size_t n = comma ? (size_t)(comma - line) : strlen(line);
    memcpy(field, line, n);
    field[n] = '\\0';
    puts(field);
}""", """void first_field(const char *line) {
    char field[12];
    const char *comma = strchr(line, ',');
    size_t n = comma ? (size_t)(comma - line) : strlen(line);
    if (n >= sizeof(field))
        n = sizeof(field) - 1;
    memcpy(field, line, n);
    field[n] = '\\0';
    puts(field);
}""", 'first_field("bob,42,paris")', f"first_field({LONG})",
     "Capped the field length at the buffer size minus the terminator before memcpy."),

    ("own_bof_15", H, """void save_key(const char *key) {
    char k[16];
    memcpy(k, key, strlen(key) + 1);
    puts(k);
}""", """void save_key(const char *key) {
    char k[16];
    size_t n = strlen(key);
    if (n > sizeof(k) - 1)
        n = sizeof(k) - 1;
    memcpy(k, key, n);
    k[n] = '\\0';
    puts(k);
}""", 'save_key("api-key-1")', f"save_key({LONG})",
     "Copied at most the size of k minus one byte and terminated the string."),

    ("own_bof_16", H, """void copy_ints(const int *values, size_t count) {
    int local[8];
    memcpy(local, values, count * sizeof(int));
    printf("%d\\n", local[0]);
}""", """void copy_ints(const int *values, size_t count) {
    int local[8];
    if (count > 8)
        count = 8;
    memcpy(local, values, count * sizeof(int));
    printf("%d\\n", local[0]);
}""", "copy_ints((int[3]){4, 5, 6}, 3)", "copy_ints((int[64]){1}, 64)",
     "Limited the number of copied integers to the size of local."),

    ("own_bof_17", H, """void set_title(const char *title) {
    char t[16];
    strncpy(t, title, strlen(title) + 1);
    puts(t);
}""", """void set_title(const char *title) {
    char t[16];
    strncpy(t, title, sizeof(t) - 1);
    t[sizeof(t) - 1] = '\\0';
    puts(t);
}""", 'set_title("Report")', f"set_title({LONG})",
     "Bounded strncpy by the size of t instead of the length of the input."),

    ("own_bof_18", H, """void add_prefix(const char *word) {
    char w[16] = "pre_";
    strncat(w, word, strlen(word));
    puts(w);
}""", """void add_prefix(const char *word) {
    char w[16] = "pre_";
    strncat(w, word, sizeof(w) - strlen(w) - 1);
    puts(w);
}""", 'add_prefix("view")', f"add_prefix({LONG})",
     "Bounded strncat by the space left in w instead of the length of the input."),

    ("own_bof_19", H, """void tag_list(const char *a, const char *b) {
    char tags[20] = "";
    strncat(tags, a, 20);
    strncat(tags, ",", 1);
    strncat(tags, b, 20);
    puts(tags);
}""", """void tag_list(const char *a, const char *b) {
    char tags[20] = "";
    strncat(tags, a, sizeof(tags) - strlen(tags) - 1);
    strncat(tags, ",", sizeof(tags) - strlen(tags) - 1);
    strncat(tags, b, sizeof(tags) - strlen(tags) - 1);
    puts(tags);
}""", 'tag_list("red", "blue")', f'tag_list("red", {LONG})',
     "Bounded each strncat by the space left in tags instead of the full buffer size."),

    ("own_bof_20", H, """void parse_name(const char *line) {
    char first[10], last[10];
    if (sscanf(line, "%s %s", first, last) == 2)
        printf("%s, %s\\n", last, first);
}""", """void parse_name(const char *line) {
    char first[10], last[10];
    if (sscanf(line, "%9s %9s", first, last) == 2)
        printf("%s, %s\\n", last, first);
}""", 'parse_name("Ada Lovelace")', f'parse_name("Ada " {LONG})',
     "Added field widths to sscanf so each word fits in its buffer."),

    ("own_bof_21", H, """void parse_command(const char *line) {
    char cmd[8];
    int n;
    if (sscanf(line, "%s %d", cmd, &n) == 2)
        printf("%s x%d\\n", cmd, n);
}""", """void parse_command(const char *line) {
    char cmd[8];
    int n;
    if (sscanf(line, "%7s %d", cmd, &n) == 2)
        printf("%s x%d\\n", cmd, n);
}""", 'parse_command("jump 3")', f'parse_command({LONG} " 3")',
     "Added a field width to sscanf so the command fits in cmd."),

    ("own_bof_22", H, """void parse_setting(const char *line) {
    char key[8], value[8];
    if (sscanf(line, "%[^=]=%s", key, value) == 2)
        printf("%s -> %s\\n", key, value);
}""", """void parse_setting(const char *line) {
    char key[8], value[8];
    if (sscanf(line, "%7[^=]=%7s", key, value) == 2)
        printf("%s -> %s\\n", key, value);
}""", 'parse_setting("mode=dark")', f'parse_setting("mode=" {LONG})',
     "Added field widths to sscanf so the key and value fit in their buffers."),

    ("own_bof_23", HV, """void log_msg(const char *fmt, ...) {
    char buf[32];
    va_list args;
    va_start(args, fmt);
    vsprintf(buf, fmt, args);
    va_end(args);
    puts(buf);
}""", """void log_msg(const char *fmt, ...) {
    char buf[32];
    va_list args;
    va_start(args, fmt);
    vsnprintf(buf, sizeof(buf), fmt, args);
    va_end(args);
    puts(buf);
}""", 'log_msg("saved %d files", 3)', f'log_msg("%s", {LONG})',
     "Replaced vsprintf with vsnprintf limited to the size of buf."),

    ("own_bof_24", H, """void copy_ip(const char *ip) {
    char addr[16];
    strcpy(addr, ip);
    printf("ip %s\\n", addr);
}""", """void copy_ip(const char *ip) {
    char addr[16];
    if (strlen(ip) >= sizeof(addr)) {
        puts("invalid address");
        return;
    }
    strcpy(addr, ip);
    printf("ip %s\\n", addr);
}""", 'copy_ip("10.0.0.1")', f"copy_ip({LONG})",
     "Rejected addresses longer than the buffer before strcpy."),

    ("own_bof_25", H, """void country_code(const char *country) {
    char code[4];
    memcpy(code, country, strlen(country));
    code[3] = '\\0';
    puts(code);
}""", """void country_code(const char *country) {
    char code[4];
    size_t n = strlen(country);
    if (n > 3)
        n = 3;
    memcpy(code, country, n);
    code[n] = '\\0';
    puts(code);
}""", 'country_code("FRA")', f"country_code({LONG})",
     "Limited memcpy to three characters, the size of code minus the terminator."),

    ("own_bof_26", HS, """void save_comment(const char *text) {
    char *c = malloc(32);
    if (c == NULL)
        return;
    strcpy(c, text);
    puts(c);
    free(c);
}""", """void save_comment(const char *text) {
    char *c = malloc(32);
    if (c == NULL)
        return;
    snprintf(c, 32, "%s", text);
    puts(c);
    free(c);
}""", 'save_comment("nice post")', f"save_comment({LONG})",
     "Replaced strcpy with snprintf limited to the 32-byte heap buffer."),

    ("own_bof_27", H, """void user_agent(const char *browser, int version) {
    char ua[24];
    sprintf(ua, "%s/%d", browser, version);
    puts(ua);
}""", """void user_agent(const char *browser, int version) {
    char ua[24];
    snprintf(ua, sizeof(ua), "%s/%d", browser, version);
    puts(ua);
}""", 'user_agent("Firefox", 120)', f"user_agent({LONG}, 120)",
     "Replaced sprintf with snprintf limited to the size of ua."),

    ("own_bof_28", H, """void order_ref(const char *customer, int number) {
    char ref[16];
    sprintf(ref, "%s-%05d", customer, number);
    puts(ref);
}""", """void order_ref(const char *customer, int number) {
    char ref[16];
    snprintf(ref, sizeof(ref), "%s-%05d", customer, number);
    puts(ref);
}""", 'order_ref("acme", 42)', f"order_ref({LONG}, 42)",
     "Replaced sprintf with snprintf limited to the size of ref."),

    ("own_bof_29", H, """void sensor_window(const double *v, size_t n) {
    double window[4];
    memcpy(window, v, n * sizeof(double));
    printf("%.1f\\n", window[0]);
}""", """void sensor_window(const double *v, size_t n) {
    double window[4];
    if (n > 4)
        n = 4;
    memcpy(window, v, n * sizeof(double));
    printf("%.1f\\n", window[0]);
}""", "sensor_window((double[2]){1.5, 2.5}, 2)", "sensor_window((double[64]){1.0}, 64)",
     "Limited the number of copied values to the size of window."),

    ("own_bof_30", H, """void make_filename(const char *name, const char *ext) {
    char f[16];
    sprintf(f, "%s.%s", name, ext);
    puts(f);
}""", """void make_filename(const char *name, const char *ext) {
    char f[16];
    snprintf(f, sizeof(f), "%s.%s", name, ext);
    puts(f);
}""", 'make_filename("photo", "png")', f'make_filename({LONG}, "png")',
     "Replaced sprintf with snprintf limited to the size of f."),

    ("own_bof_31", H, """void parse_date(const char *s) {
    char month[4];
    int day, year;
    if (sscanf(s, "%d %s %d", &day, month, &year) == 3)
        printf("%s %d, %d\\n", month, day, year);
}""", """void parse_date(const char *s) {
    char month[4];
    int day, year;
    if (sscanf(s, "%d %3s %d", &day, month, &year) == 3)
        printf("%s %d, %d\\n", month, day, year);
}""", 'parse_date("14 Nov 2026")', f'parse_date("14 " {LONG} " 2026")',
     "Added a field width to sscanf so the month fits in month."),

    ("own_bof_32", H, """void line_prefix(const char *line, size_t n) {
    char prefix[10];
    memcpy(prefix, line, n);
    prefix[n] = '\\0';
    puts(prefix);
}""", """void line_prefix(const char *line, size_t n) {
    char prefix[10];
    if (n >= sizeof(prefix))
        n = sizeof(prefix) - 1;
    memcpy(prefix, line, n);
    prefix[n] = '\\0';
    puts(prefix);
}""", 'line_prefix("GET /home", 3)', f"line_prefix({LONG}, 150)",
     "Capped the prefix length at the buffer size minus the terminator."),

    ("own_bof_33", H, """void add_signature(const char *body) {
    char mail[48];
    strcpy(mail, body);
    strcat(mail, " -- sent from app");
    puts(mail);
}""", """void add_signature(const char *body) {
    char mail[48];
    snprintf(mail, sizeof(mail), "%s -- sent from app", body);
    puts(mail);
}""", 'add_signature("See you soon")', f"add_signature({LONG})",
     "Built the message with snprintf limited to the size of mail."),

    ("own_bof_34", H, """void menu_item(const char *dish, const char *price) {
    char item[20];
    strcpy(item, dish);
    strcat(item, " ... ");
    strcat(item, price);
    puts(item);
}""", """void menu_item(const char *dish, const char *price) {
    char item[20];
    snprintf(item, sizeof(item), "%s ... %s", dish, price);
    puts(item);
}""", 'menu_item("soup", "4.50")', f'menu_item({LONG}, "4.50")',
     "Built the menu line with snprintf limited to the size of item."),

    ("own_bof_35", H, """struct session {
    char id[16];
    int active;
};

void open_session(const char *id) {
    struct session s;
    memcpy(s.id, id, strlen(id) + 1);
    s.active = 1;
    printf("%s %d\\n", s.id, s.active);
}""", """struct session {
    char id[16];
    int active;
};

void open_session(const char *id) {
    struct session s;
    size_t n = strlen(id);
    if (n >= sizeof(s.id)) {
        puts("session id too long");
        return;
    }
    memcpy(s.id, id, n + 1);
    s.active = 1;
    printf("%s %d\\n", s.id, s.active);
}""", 'open_session("s-1234")', f"open_session({LONG})",
     "Rejected session ids that do not fit in the id field before memcpy."),

    ("own_bof_36", HS, """void copy_lines(const char *a, const char *b) {
    char *out = malloc(24);
    if (out == NULL)
        return;
    sprintf(out, "%s|%s", a, b);
    puts(out);
    free(out);
}""", """void copy_lines(const char *a, const char *b) {
    char *out = malloc(24);
    if (out == NULL)
        return;
    snprintf(out, 24, "%s|%s", a, b);
    puts(out);
    free(out);
}""", 'copy_lines("one", "two")', f'copy_lines("one", {LONG})',
     "Replaced sprintf with snprintf limited to the 24-byte heap buffer."),
]


def main():
    for old in OUT.glob("own_bof_*"):
        shutil.rmtree(old)
    for case_id, head, vuln, repair, normal, attack, why in CASES:
        d = OUT / case_id
        d.mkdir(parents=True)
        (d / "vulnerable.c").write_text(f"{head}\n{vuln}\n")
        (d / "repair.c").write_text(f"{head}\n{repair}\n")
        func = vuln.split("void ", 2)[-1].split("(")[0]
        meta = {"id": case_id, "language": "c", "class": "buffer_overflow", "cwe": "CWE-120",
                "explanation": why, "function": func, "normal_call": normal, "attack_call": attack,
                "source": f"own:{case_id}"}
        (d / "meta.json").write_text(json.dumps(meta, indent=2) + "\n")
    print(f"wrote {len(CASES)} cases to {OUT}")


if __name__ == "__main__":
    main()
