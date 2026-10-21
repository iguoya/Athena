//
// Created by tiger on 18-10-24.
//
#include <stdio.h>
#include <check.h>
#include "matrix.h"



START_TEST(test_avg)
    {
        ck_assert_int_eq(get_avg_sum(-10), -1);
        ck_assert_int_eq(get_avg_sum(0), -1);
        ck_assert_int_eq(get_avg_sum(3), 15);
        ck_assert_int_eq(get_avg_sum(4), 34);
        ck_assert_int_eq(get_avg_sum(5), 65);
    }
END_TEST

START_TEST(test_matrix)
    {
        struct node *p = init_matrix(5);

        show_matrix(p, 5);

//        ck_assert_int_eq((p+1)->value, 2);
//        ck_assert_int_eq((p+1)->row, 1);
//        ck_assert_int_eq((p+1)->column, 2);
//
//        ck_assert_int_eq((p + 12)->value, 13);
//        ck_assert_int_eq((p + 12)->row, 3);
//        ck_assert_int_eq((p + 12)->column, 3);
//
//        ck_assert_int_eq((p + 24)->value, 25);
//        ck_assert_int_eq((p + 24)->row, 5);
//        ck_assert_int_eq((p + 24)->column, 5);


    }
END_TEST


Suite *str_suite(void) {
    Suite *suite = suite_create("matrix");
    TCase *tcase = tcase_create("平均和");
    tcase_add_test(tcase, test_avg);
    TCase *t_matrix = tcase_create("矩阵");
    tcase_add_test(t_matrix, test_matrix);

    suite_add_tcase(suite, tcase);
    suite_add_tcase(suite, t_matrix);
    return suite;
}

int main(void) {
    int number_failed;
    Suite *suite = str_suite();
    SRunner *runner = srunner_create(suite);
    srunner_run_all(runner, CK_NORMAL);
    number_failed = srunner_ntests_failed(runner);
    srunner_free(runner);
    return number_failed;
}
