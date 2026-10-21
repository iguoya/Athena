#include <stdio.h>
#include <wchar.h>

int main(int argc, char *argv[]) {
    printf("Hello, World!\n");

    wchar_t wa;
    char ch;

    FILE *fp;

    fp = fopen(argv[1], "r");

    while((ch = fgetc(fp)) != EOF) {
        putchar(ch);
//        printf("<--->\n");
    }

    FILE *fq = fopen(argv[1], "r");
    char s[1000];
    int i=0;
    while((ch=fgetc(fq))!=EOF) {
        //按字符方式读取文件，每读一个字符判断一下是否为汉字编码(<0)，若是则存入字符数组，不是则跳过读取下一个字符，直到文件结束。
        if(ch<0) {
            s[i++]=ch;
        } else {
            s[i++] = ch;
        }

    }

    s[i]='\0';
    printf("%s\n",s);//打出来看看

    fclose(fp);
    fclose(fq);

    return 0;
}