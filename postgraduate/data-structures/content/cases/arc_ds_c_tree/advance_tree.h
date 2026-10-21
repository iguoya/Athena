//
// Created by tiger on 18-11-19.
//
#include "btree.h"

#ifndef TREE_HIGH_TREE_H
#define TREE_HIGH_TREE_H

QueueElemType get_random_nums(size_t level, float intensity) {

    bool is_retain = true;
    if(intensity > 0.5) {
        is_retain = false;
        intensity = 1-intensity;
    }

    QueueElemType arr;
    size_t num_min = get_level_max_num(n-1)+1;
    size_t num_max = get_level_max_num(n);=-55

    if(is_retain) {
        size_t retain_num = ceil(intensity*pow(2, level-1));
        arr.p = malloc(sizeof(size_t)*retain_num);
        arr.len = retain_num;
        for(size_t i = 1; i<=retain_num; ++i) {
            *(arr.p+i-1) = rand()%(num_max-num_min+1)+num_min;
        } b


    } else {

        size_t totol_len = num_max-num_min+1;
        size_t total_nums[totol_len];
        size_t abandon_num_len = ceil(intensity*pow(2, level-1));
        size_t abandon_nums[abandon_num_len];

        for(size_t i= 1; i <= totol_len; ++num_min) {
            total_nums[i-1] = num_min+i-1;
        }
        for(size_t i = 1; i<= abandon_nums; ++i) {
            size_t abandon_num = rand()%(num_max-num_min+1)+num_min;
            for(size_t j = 1; j <= num_max-num_min+1)

        }

    }
}



Btree create_random_tree(size_t level, float intensity) {
    srand(time(NULL));
//    size_t *level_node_num = malloc(sizeof(size_t)*level);
    size_t sum_node = 0;
    size_t level_total_num[level];

    LinkQueue tree_node_nums = init_queue();


    for(size_t n = 1; n <= level; ++n) {


        level_total_num[n-1] = level_node_num;
        printf("level %d: min:%d, max:%d, intensity:%d\n", n, num_min, num_max, level_node_num);



        *(num_set+n-1) = p;

//        sum_node += level_node_num;
    }
//    printf("total:%.0f, sum:%d, intensity : %.5f%%  \n",
//           pow(2, level)-1,
//            sum_node,
//            sum_node/(pow(2, level)-1)*100);

    for(size_t i = 0; i< level; ++i) {
        size_t *p = *(num_set+i);
        printf("-----------level:%d, total_num:%d---------------\n", i+1, level_total_num[i-1]);
        for(size_t j = 0; j < level_total_num[i-1]; ++j) {
            printf("%5d\t", *(p+j));
            if(i ==0) {
                break;
            }
        }
        printf("\n");
    }
}


#endif //TREE_HIGH_TREE_H
