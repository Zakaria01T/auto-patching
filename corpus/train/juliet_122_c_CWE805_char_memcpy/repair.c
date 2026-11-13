#include <stdio.h>
#include <stdlib.h>
#include <string.h>

void copy_block(void)
{
    char * data;
    data = NULL;
    data = (char *)malloc(50*sizeof(char));
    if (data == NULL) {exit(-1);}
    data[0] = '\0';
    {
        char source[100];
        memset(source, 'C', 100-1);
        source[100-1] = '\0';
        memcpy(data, source, 50*sizeof(char));
        data[50 - 1] = '\0';
        printf("%s\n", data);
        free(data);
    }
}
