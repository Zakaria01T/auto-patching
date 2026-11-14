#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <alloca.h>

void copy_block(void)
{
    int * data;
    int * dataBuffer = (int *)alloca(50*sizeof(int));
    data = dataBuffer;
    {
        int source[100] = {0};
        memcpy(data, source, 100*sizeof(int));
        printf("%d\n", data[0]);
    }
}
