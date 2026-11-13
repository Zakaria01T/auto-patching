#include <stdio.h>
#include <string.h>

void sensor_window(const double *v, size_t n) {
    double window[4];
    memcpy(window, v, n * sizeof(double));
    printf("%.1f\n", window[0]);
}
