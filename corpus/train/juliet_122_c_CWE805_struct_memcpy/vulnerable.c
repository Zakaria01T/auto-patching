#include <stdio.h>
#include <stdlib.h>
#include <string.h>

typedef struct {
    int intOne;
    int intTwo;
} twoIntsStruct;

void copy_block(void)
{
    twoIntsStruct * data;
    data = NULL;
    data = (twoIntsStruct *)malloc(50*sizeof(twoIntsStruct));
    if (data == NULL) {exit(-1);}
    {
        twoIntsStruct source[100];
        {
            size_t i;
            for (i = 0; i < 100; i++)
            {
                source[i].intOne = 0;
                source[i].intTwo = 0;
            }
        }
        memcpy(data, source, 100*sizeof(twoIntsStruct));
        printf("%d -- %d\n", data[0].intOne, data[0].intTwo);
        free(data);
    }
}
