#include <stdio.h>
#include <string.h>

void email_address(const char *user, const char *domain) {
    char mail[32];
    snprintf(mail, sizeof(mail), "%s@%s", user, domain);
    puts(mail);
}
