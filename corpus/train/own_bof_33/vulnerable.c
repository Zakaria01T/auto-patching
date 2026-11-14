#include <stdio.h>
#include <string.h>

void add_signature(const char *body) {
    char mail[48];
    strcpy(mail, body);
    strcat(mail, " -- sent from app");
    puts(mail);
}
