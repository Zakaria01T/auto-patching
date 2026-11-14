#include <stdio.h>
#include <string.h>

void save_username(const char *user) {
    char name[20];
    strcpy(name, user);
    printf("user=%s\n", name);
}
