/*
===============================================================================
Driver Name		:		B1_Hello
Author			:		TIGER
License			:		GPL
Description		:		LINUX DEVICE DRIVER PROJECT
===============================================================================
*/

#include "B1_Hello.h"

MODULE_LICENSE("GPL");
MODULE_AUTHOR("TIGER");

static int __init B1_Hello_init(void)
{
	/* TODO Auto-generated Function Stub */

	PINFO("INIT\n");
	printk(KERN_DEBUG "Hello World, Kernel 郭雅 !!!\n");
	return 0;
}

static void __exit B1_Hello_exit(void)
{	
	/* TODO Auto-generated Function Stub */
	printk(KERN_EMERG "GoodBye, cruel world, 雅 \n");

	PINFO("EXIT\n");

}

module_init(B1_Hello_init);
module_exit(B1_Hello_exit);

