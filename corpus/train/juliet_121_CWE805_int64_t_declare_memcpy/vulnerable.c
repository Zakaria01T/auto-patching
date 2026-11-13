#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdint.h>

void copy_block(void)
{
    int64_t * data;
    int64_t dataBuffer[50];
    data = dataBuffer;
    {
        int64_t source[100] = {0};
        memcpy(data, source, 100*sizeof(int64_t));
        printf("%lld\n", (long long)data[0]);
    }
}
