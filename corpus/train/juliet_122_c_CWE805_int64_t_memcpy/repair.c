#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdint.h>

void copy_block(void)
{
    int64_t * data;
    data = NULL;
    data = (int64_t *)malloc(50*sizeof(int64_t));
    if (data == NULL) {exit(-1);}
    {
        int64_t source[100] = {0};
        memcpy(data, source, 50*sizeof(int64_t));
        printf("%lld\n", (long long)data[0]);
        free(data);
    }
}
