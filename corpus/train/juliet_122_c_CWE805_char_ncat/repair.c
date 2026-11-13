#include <stdio.h>
#include <stdlib.h>
#include <string.h>

void append_text(void)
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
        strncat(data, source, 50 - strlen(data) - 1);
        printf("%s\n", data);
        free(data);
    }
}
