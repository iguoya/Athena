#include <iostream>
#include "btree.h"
#include <vector>
#include <string>

using namespace std;

int main()
{
    cout << "Hello World!" << endl;
//    Btree<string> tree;
//    tree.root = new BtreeNode<string>(new string("A"));
//    tree.root->add_child(new BtreeNode<string>(new string("B")), new BtreeNode<string>(new string("C")));
//    tree.root->lchild->add_child(new BtreeNode<string>(new string("D")), new BtreeNode<string>(new string("E")));
//    tree.root->rchild->add_child(new BtreeNode<string>(new string("F")), new BtreeNode<string>(new string("G")));
//    BtreeNode<string> *d = tree.root->lchild->lchild;
//    d->add_child(new BtreeNode<string>(new string("H")), new BtreeNode<string>(new string("I")));
//    BtreeNode<string> *e = tree.root->lchild->rchild;
//    e->add_child(new BtreeNode<string>(new string("J")), new BtreeNode<string>(new string("K")));
//    BtreeNode<string> *f = tree.root->rchild->lchild;
//    f->add_child(new BtreeNode<string>(new string("L")), new BtreeNode<string>(new string("M")));
//    BtreeNode<string> *g = tree.root->rchild->rchild;
//    g->add_child(new BtreeNode<string>(new string("N")ratio), new BtreeNode<string>(new string("O")));

//    BtreeNode<string> *j = e->lchild;
//    j->add_lchild(new BtreeNode<string>(new string("P")));
//    BtreeNode<string> *m = f->rchild;
//    m->add_rchild(new BtreeNode<string>(new string("Q")));

    Btree<size_t> tree;
    tree.set_full_tree();
    tree.show();
    tree.set_random_tree(63, 1);
    tree.show();


    return 0;
}
