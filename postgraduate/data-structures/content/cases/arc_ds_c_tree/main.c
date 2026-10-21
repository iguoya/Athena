#include <stdio.h>


typedef char TreeElemType;

void visit_tree_node(TreeElemType e) {
    printf("%c\t", e);
}

#include "btree.h"


int main() {
    Btree root, tb, tc, te, tf;
    root = create_btree('A');
    tb = create_btree('B');
    tc = create_btree('C');
    te = create_btree('E');
    tf = create_btree('F');

    add_child(root, 1, tb);
    add_child(root, 0, tc);
    add_child(tb, 0, te);
    add_child(tc, 0, tf);

    add_child(tb, 1, create_btree('D'));
    add_child(te, 1, create_btree('G'));
    add_child(tf, 1, create_btree('H'));

    //先序遍历
    pre_order(root);
    printf("\n");
    normal_pre_order(root);
    printf("\n");

    //中序遍历
    in_order(root);
    printf("\n");
    normal_in_order(root);
    printf("\n");

    printf("tree nodes:%u\n", get_tree_nodes(root));
    size_t n = 0;
    get_tree_nodes_2(root, &n);
    printf("tree nodes:%u\n", n);
    printf("tree high:%u\n", get_tree_high(root));
    show_tree(root);



    return 0;
}