#include <stdio.h>
#include <string.h>

void make_url(const char *host, const char *page) {
    char url[40] = "https://";
    strcat(url, host);
    strcat(url, page);
    puts(url);
}
