#include <stdio.h>
#include <string.h>

void copy_ints(const int *values, size_t count) {
    int local[8];
    if (count > 8)
        count = 8;
    memcpy(local, values, count * sizeof(int));
    printf("%d\n", local[0]);
}
