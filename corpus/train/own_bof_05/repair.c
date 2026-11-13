#include <stdio.h>
#include <string.h>

void make_url(const char *host, const char *page) {
    char url[40];
    snprintf(url, sizeof(url), "https://%s%s", host, page);
    puts(url);
}
