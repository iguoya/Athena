#include <iostream>
using namespace std;
 
int main()
{   
    int i,j,k;   // p[x][y][z]

    int x  = 3,y = 3 ,z = 3;
    int ***p;

    p = new int **[x]; 
    for(i=0; i<x; i++) 
    { 
        p[i]=new int *[y]; 
        for(j=0; j<y; j++) 
            p[i][j]=new int[z]; 
    }
    
    //输出 p[i][j][k] 三维数据
    for(i=0; i<x; i++)   
    {
        for(j=0; j<y; j++)   
        { 
            for(k=0;k<z;k++)
            { 
                p[i][j][k]=i+j+k;
                cout<<p[i][j][k]<<" ";
            }
            cout<<endl;
        }
        cout<<endl;
    }
    
    // 释放内存
    for(i=0; i<x; i++) 
    {
        for(j=0; j<y; j++) 
        {   
            delete [] p[i][j];   
        }   
    }       
    for(i=0; i<x; i++)   
    {       
        delete [] p[i];   
    }   
    delete [] p;  
    return 0;
}