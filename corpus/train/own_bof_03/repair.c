#include <stdio.h>
#include <stdlib.h>
#include <string.h>

void store_token(const char *token) {
    char *copy = malloc(16);
    if (copy == NULL)
        return;
    strncpy(copy, token, 15);
    copy[15] = '\0';
    printf("token %s\n", copy);
    free(copy);
}
