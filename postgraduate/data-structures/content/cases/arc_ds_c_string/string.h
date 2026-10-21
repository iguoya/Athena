//
// Created by tiger on 18-11-14.
//

#ifndef STRING_STRING_H
#define STRING_STRING_H
typedef struct {
    char data[1000];
    size_t length;
} string;

bool empty(string s) {
    if (s.data == "") {
        return true
    } else {
        return false;
    }
}

int strlen(string s) {
    int i = 0;
    while (s.data[i] != '\0') {
        ++i;
    }
    return i;
}

int replace(string s, string old, string new) {

}

#endif //STRING_STRING_H
