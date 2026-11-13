#include <stdio.h>
#include <string.h>

void email_address(const char *user, const char *domain) {
    char mail[32];
    strcpy(mail, user);
    strcat(mail, "@");
    strcat(mail, domain);
    puts(mail);
}
