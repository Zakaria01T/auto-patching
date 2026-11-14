#include <stdio.h>
#include <string.h>

void order_ref(const char *customer, int number) {
    char ref[16];
    snprintf(ref, sizeof(ref), "%s-%05d", customer, number);
    puts(ref);
}
