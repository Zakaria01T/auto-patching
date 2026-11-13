#include <stdio.h>
#include <stdlib.h>
#include <string.h>

void copy_block(void)
{
    int * data;
    int dataBuffer[50];
    data = dataBuffer;
    {
        int source[100] = {0};
        memcpy(data, source, 50*sizeof(int));
        printf("%d\n", data[0]);
    }
}
