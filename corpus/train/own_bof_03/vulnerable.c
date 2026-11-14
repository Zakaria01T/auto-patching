#include <stdio.h>
#include <stdlib.h>
#include <string.h>

void store_token(const char *token) {
    char *copy = malloc(16);
    if (copy == NULL)
        return;
    strcpy(copy, token);
    printf("token %s\n", copy);
    free(copy);
}
