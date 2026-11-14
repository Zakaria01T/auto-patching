#include <stdio.h>
#include <string.h>

void user_agent(const char *browser, int version) {
    char ua[24];
    snprintf(ua, sizeof(ua), "%s/%d", browser, version);
    puts(ua);
}
