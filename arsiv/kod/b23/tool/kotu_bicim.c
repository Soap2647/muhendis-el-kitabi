#include <stdio.h>
#include <stdlib.h>
int olc(int *a,int n){int s=0;
for(int i=0;i<n;i++){ if(a[i]>0){s+=a[i];}else{ s-=a[i] ;} }
if(s>100){printf("buyuk %d\n",s);return 1;}
return 0;}
