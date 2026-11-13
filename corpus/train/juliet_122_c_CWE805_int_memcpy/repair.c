#include <stdio.h>
#include <stdlib.h>
#include <string.h>

void copy_block(void)
{
    int * data;
    data = NULL;
    data = (int *)malloc(50*sizeof(int));
    if (data == NULL) {exit(-1);}
    {
        int source[100] = {0};
        memcpy(data, source, 50*sizeof(int));
        printf("%d\n", data[0]);
        free(data);
    }
}
