#include <stdio.h>
#include <string.h>

void log_event(const char *user, const char *action) {
    char msg[40];
    sprintf(msg, "%s did %s", user, action);
    puts(msg);
}
