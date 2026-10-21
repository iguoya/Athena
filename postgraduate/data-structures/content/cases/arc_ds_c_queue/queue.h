//
// Created by tiger on 18-11-11.
//
#include <stdbool.h>
#include <stddef.h>
#include <stdlib.h>

#ifndef QUEUE_QUEUE_H
#define QUEUE_QUEUE_H


typedef struct QueueNode {
    struct QueueNode * next;
    QueueElemType data;
} QueueNode, *LinkQueueNode;



typedef struct {
    LinkQueueNode front;
    LinkQueueNode rear;
} Queue, *LinkQueue;

LinkQueue init_queue() {
    LinkQueueNode head = malloc(sizeof(QueueNode));
    head->next = NULL;
    LinkQueue lq = malloc(sizeof(Queue));
    lq->front = head;
    lq->rear = head;
    return lq;
}

bool empty_queue(LinkQueue lq) {
    if(lq->front == lq->rear) {
        return true;
    } else {
        return false;
    }
}


bool get_queue_head(LinkQueue lq, QueueElemType *e) {
    if(empty_queue(lq)) {
        return false;
    } else {
        *e = (lq->front->next)->data;
        return true;
    }
}

void en_queue(LinkQueue lq, QueueElemType e) {
    LinkQueueNode pn = malloc(sizeof(QueueNode));
    pn->data = e;
    pn->next = NULL;
    lq->rear->next= pn;
    lq->rear = pn;
}

bool de_queue(LinkQueue lq) {
    if(empty_queue(lq)) {
        return false;
    } else {
        LinkQueueNode pn = lq->front->next;
        lq->front->next = pn->next;
        if(pn == lq->rear) {
            lq->rear = lq->front;
        }
        free(pn);
    }
}



#endif //QUEUE_QUEUE_H
