#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <alloca.h>

void copy_block(void)
{
    char * data;
    char * dataBuffer = (char *)alloca(50*sizeof(char));
    data = dataBuffer;
    data[0] = '\0';
    {
        char source[100];
        memset(source, 'C', 100-1);
        source[100-1] = '\0';
        memcpy(data, source, 100*sizeof(char));
        data[100-1] = '\0';
        printf("%s\n", data);
    }
}
