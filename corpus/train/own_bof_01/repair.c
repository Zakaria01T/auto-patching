#include <stdio.h>
#include <string.h>

void save_username(const char *user) {
    char name[20];
    snprintf(name, sizeof(name), "%s", user);
    printf("user=%s\n", name);
}
