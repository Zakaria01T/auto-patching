#include <stdio.h>
#include <string.h>

void order_ref(const char *customer, int number) {
    char ref[16];
    sprintf(ref, "%s-%05d", customer, number);
    puts(ref);
}
