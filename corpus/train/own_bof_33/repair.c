#include <stdio.h>
#include <string.h>

void add_signature(const char *body) {
    char mail[48];
    snprintf(mail, sizeof(mail), "%s -- sent from app", body);
    puts(mail);
}
